from yt_dlp import YoutubeDL
from pathlib import Path
import random
import sys
import re
import json

# Reject videos above these limits before downloading.
MAX_DURATION_SECONDS = 300
MAX_FILESIZE_BYTES = 60 * 1024 * 1024       #60 MB


def generate_obscure_query() -> str:
    # Generate filename-like search terms to surface low-profile uploads.
    prefixes = ["IMG_", "DSC_", "MVI_", "VID_", "MOV_"]
    random_prefix = random.choice(prefixes)
    random_number = str(random.randint(0, 9999)).zfill(4)
    return f"{random_prefix}{random_number}"


def emit(tag: str, message: str | None = None, **extra) -> None:
    # Send exactly one JSON object per line to stdout so bridge.js
    # can parse it safely.
    payload = {"tag": tag}
    if message is not None:
        payload["message"] = message
    payload.update(extra)
    print(json.dumps(payload, ensure_ascii=False), flush=True)


def sanitize_filename(name: str) -> str:
    # Remove characters that are invalid in typical filesystem names.
    return re.sub(r'[<>:"/\\|?*]', "_", name).strip()


def format_upload_date(raw_date) -> str:
    # yt-dlp dates usually arrive as YYYYMMDD.
    if not raw_date or not isinstance(raw_date, str) or len(raw_date) != 8:
        return "Unknown"
    return f"{raw_date[6:8]}-{raw_date[4:6]}-{raw_date[0:4]}"


def format_duration(seconds) -> str:
    if not isinstance(seconds, (int, float)):
        return "Unknown"

    total = int(seconds)
    hours = total // 3600
    minutes = (total % 3600) // 60
    secs = total % 60

    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def print_metadata(info: dict) -> None:
    # Forward selected metadata as log messages.
    emit("log", f"Upload date: {format_upload_date(info.get('upload_date'))}")
    emit("log", f"Video name: {info.get('title') or 'Unknown'}")
    emit("log", f"Uploader: {info.get('uploader') or info.get('channel') or 'Unknown'}")
    emit("log", f"View Count: {info.get('view_count') or 0}")
    emit("log", f"Likes: {info.get('like_count') or 0}")
    emit("log", f"Duration: {info.get('duration_string') or format_duration(info.get('duration'))}")


def get_webpage_url(entry: dict) -> str | None:
    # Resolve a normal watch URL from a flat yt-dlp search result.
    video_id = entry.get("id")
    webpage_url = entry.get("webpage_url") or entry.get("url")

    if video_id and (not webpage_url or not str(webpage_url).startswith("http")):
        return f"https://www.youtube.com/watch?v={video_id}"

    if webpage_url and str(webpage_url).startswith("http"):
        return str(webpage_url)

    return None


def get_total_filesize(info: dict) -> int | None:
    # Try direct filesize first. If video/audio are separate streams,
    # sum the requested format sizes instead.
    direct_size = info.get("filesize") or info.get("filesize_approx")
    if isinstance(direct_size, (int, float)):
        return int(direct_size)

    requested_formats = info.get("requested_formats")
    if isinstance(requested_formats, list) and requested_formats:
        total = 0
        found_any = False

        for fmt in requested_formats:
            if not isinstance(fmt, dict):
                continue
            size = fmt.get("filesize") or fmt.get("filesize_approx")
            if isinstance(size, (int, float)):
                total += int(size)
                found_any = True

        if found_any:
            return total

    return None


def is_too_big(info: dict) -> bool:
    # Enforce duration and filesize limits.
    duration = info.get("duration")
    if isinstance(duration, (int, float)) and duration > MAX_DURATION_SECONDS:
        return True

    total_size = get_total_filesize(info)
    if isinstance(total_size, int) and total_size > MAX_FILESIZE_BYTES:
        return True

    return False


def find_random_video(max_attempts: int = 20, search_batch_size: int = 5) -> dict | None:
    search_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,   # faster search results, without full extraction
        "skip_download": True,
        "playlistend": search_batch_size,
    }

    with YoutubeDL(search_opts) as ydl:
        for _ in range(max_attempts):
            query = generate_obscure_query()
            emit("log", f"Searching YouTube for obscure filename: {query}...")

            try:
                search_result = ydl.extract_info(
                    f"ytsearch{search_batch_size}:{query}",
                    download=False,
                )
            except Exception as err:
                # Continue searching even if one query fails.
                emit("error", f"search-warning {err}")
                continue

            entries = (search_result or {}).get("entries") or []
            entries = [entry for entry in entries if entry]

            if not entries:
                continue

            random.shuffle(entries)

            for chosen in entries:
                webpage_url = get_webpage_url(chosen)
                if not webpage_url:
                    continue

                emit("log", f'Found video: "{chosen.get("title", "Unknown")}"')
                return {
                    "query": query,
                    "id": chosen.get("id"),
                    "url": webpage_url,
                    "title": chosen.get("title") or "video",
                }

    return None


def download_video(url: str, filename: str) -> bool:
    script_dir = Path(__file__).resolve().parent
    output_dir = (script_dir / "tmp_vid").resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    safe_name = sanitize_filename(filename)

    options = {
        # Save into tmp_vid with the requested base name.
        "outtmpl": str(output_dir / f"{safe_name}.%(ext)s"),
        # Prefer mp4 output when possible.
        "format": "mp4/bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
        "noplaylist": True,
        # Keep yt-dlp quiet so stdout remains clean JSON.
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "overwrites": True,
    }

    with YoutubeDL(options) as ydl:
        # Read metadata first so we can log it and reject oversized videos.
        info = ydl.extract_info(url, download=False)
        print_metadata(info)

        if is_too_big(info):
            emit("failed", "too big")
            return False

        ydl.download([url])
        emit("done")
        return True


def run_search_mode() -> int:
    try:
        chosen_video = find_random_video()
        if not chosen_video or not chosen_video.get("url"):
            emit("failed", "no_url")
            return 1

        emit("url", chosen_video["url"])
        return 0
    except Exception as err:
        emit("error", str(err))
        return 2


def run_download_mode(url: str, filename: str) -> int:
    try:
        ok = download_video(url, filename)
        if ok:
            return 0
        return 1
    except Exception as err:
        emit("error", str(err))
        return 2


def main() -> int:
    # Supported CLI modes:
    #   python download.py search
    #   python download.py download <url> <filename>
    if len(sys.argv) < 2:
        emit("error", "missing-mode")
        return 2

    mode = sys.argv[1]

    if mode == "search":
        return run_search_mode()

    if mode == "download":
        if len(sys.argv) < 4:
            emit("error", "missing-args")
            return 2
        return run_download_mode(sys.argv[2], sys.argv[3])

    emit("error", f"unknown-mode {mode}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())