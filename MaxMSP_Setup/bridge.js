const Max = require("max-api");
const { spawn } = require("child_process");
const path = require("path");

// Prevent overlapping Python jobs.
let isBusy = false;

// Used to generate sequential IDs / filenames like vid1, vid2, ...
let videofile_id = 1;

// Stop retrying after too many controlled failures.
const MAX_TRIES = 5;
let tries = 0;


function resetTries() {
  tries = 0;
  Max.outlet("log", "Tries reset!");
}

function getPythonCommand() {
  // Use the Python interpreter from the local virtual environment.
  if (process.platform === "win32") {
    return path.join(__dirname, ".venv", "Scripts", "python.exe");
  }
  return path.join(__dirname, ".venv", "bin", "python3");
}

function handleJsonMessage(msg) {
  if (!msg || typeof msg !== "object") {
    Max.outlet("error", "invalid-json-message");
    return;
  }

  const tag = msg.tag;
  const message = typeof msg.message === "string" ? msg.message : "";

  // Route structured Python messages into Max outlets.
  switch (tag) {
    case "url":
      Max.outlet("url", message);
      break;

    case "log":
      Max.outlet("log", message);
      break;

    case "done":
      // Successful download: output current id, advance counter,
      // reset tries, then notify Max with a bang.
      Max.outlet("id", videofile_id);
      Max.outlet("done", "bang");
      tries = 0;
      videofile_id++;
      break;

    case "failed":
      // Controlled failure such as "too big" or "no_url".
      tries++;
      Max.outlet("failed", `${message}, Tries: ${tries}`);
      break;

    case "error":
      Max.outlet("error", message);
      break;

    default:
      // Keep unknown message types visible for debugging.
      Max.outlet("log", JSON.stringify(msg));
      break;
  }

}

function processStdoutBuffer(state) {
  // stdout is a stream, so one event may contain partial lines
  // or several lines at once. Split complete lines and keep the
  // unfinished last fragment in the buffer.
  const lines = state.stdoutBuffer.split(/\r?\n/);
  state.stdoutBuffer = lines.pop();

  for (const rawLine of lines) {
    const line = rawLine.trim();
    if (!line) continue;

    try {
      const msg = JSON.parse(line);
      handleJsonMessage(msg);
    } catch (err) {
      Max.outlet("error", `invalid-json ${line}`);
    }
  }
}

function runPython(args) {
  if (isBusy) {
    Max.outlet("error", "busy");
    return;
  }

  isBusy = true;

  const pythonScript = path.join(__dirname, "download.py");
  const pythonExe = getPythonCommand();

  // Start Python in unbuffered mode (-u) so messages arrive immediately.
  const py = spawn(pythonExe, ["-u", pythonScript, ...args], {
    windowsHide: true,
    cwd: __dirname
  });

  const state = {
    stdoutBuffer: "",
    stderrBuffer: ""
  };

  py.stdout.on("data", (data) => {
    // stdout carries one JSON object per line.
    state.stdoutBuffer += data.toString();
    processStdoutBuffer(state);
  });

  py.stderr.on("data", (data) => {
    // stderr is kept as raw text for unexpected diagnostics.
    state.stderrBuffer += data.toString();

    const lines = state.stderrBuffer.split(/\r?\n/);
    state.stderrBuffer = lines.pop();

    for (const rawLine of lines) {
      const line = rawLine.trim();
      if (line) {
        Max.outlet("error", line);
      }
    }
  });

  py.on("error", (err) => {
    // Process-level error: Python could not be started at all.
    isBusy = false;
    Max.outlet("error", err.message);
  });

  py.on("close", (code) => {
    // Python has finished, so allow the next request.
    isBusy = false;

    // Flush any final partial line left in the buffers.
    const remainingStdout = state.stdoutBuffer.trim();
    const remainingStderr = state.stderrBuffer.trim();

    if (remainingStdout) {
      try {
        handleJsonMessage(JSON.parse(remainingStdout));
      } catch (err) {
        Max.outlet("error", `invalid-json ${remainingStdout}`);
      }
    }

    if (remainingStderr) {
      Max.outlet("error", remainingStderr);
    }

    // 0 = success, 1 = controlled failure, anything else is unexpected.
    if (code !== 0 && code !== 1) {
      Max.outlet("error", `python-exit-${code}`);
    }
  });
}

function search() {
  if (tries >= MAX_TRIES) {
    Max.outlet("log", "Maximum number of tries reached. Reset first!");
    return;
  }

  runPython(["search"]);
}

function download(url) {
  if (tries >= MAX_TRIES) {
    Max.outlet("log", "Maximum number of tries reached. Reset first!");
    return;
  }

  const filename = "vid" + videofile_id;

  if (!url) {
    Max.outlet("error", "Missing URL");
    return;
  }

  runPython(["download", url, filename]);
}

// Expose Max messages to Node handlers.
Max.addHandler("search", search);
Max.addHandler("download", download);
Max.addHandler("resetTries", resetTries);