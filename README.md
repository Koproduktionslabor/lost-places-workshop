# lost-places-workshop
This repository contains the documentation and configuration guidelines for the audiovisual installation **"Lost Places of the Internet"**, part of the **Digital Junkyard** project. This setup uses OBS Studio to transform almost 0-view YouTube streams into a generative, audio-reactive wasteland.

---

## Download Links

To participate in the workshop, OBS and the following plugins should be installed:

[OBS](https://obsproject.com/de/download)  
[Move Transitions](https://obsproject.com/forum/resources/move.913/)  
[Retro effects](https://obsproject.com/forum/resources/retro-effects.1972/)  
[Recursion Effect](https://obsproject.com/forum/resources/recursion-effect.1008/)  
[DistroAV](https://obsproject.com/forum/resources/distroav-network-audio-video-in-obs-studio-using-ndi%C2%AE-technology.528/)  
[Advanced Scene Switcher](https://obsproject.com/forum/resources/advanced-scene-switcher.395/)   
[Free Melda Audio Plugins](https://www.meldaproduction.com/effects/free)   

*Note:*

On MacOS, you will probably not be able to install the OBS plugins directly, as they are not authorized by Apple. To get around this, you can do the following:

1. Open the terminal  
2. Enter the following command:

```sudo xattr -rd com.apple.quarantine ```

**Make sure you enter a space after the command**  

3. Drag and drop the installation file for the respective plugin into the Terminal and press Enter  
4. Now enter your password and confirm the input.

---

## Documentation

### 1. Scene and Source Structure

The installation relies on a 1:1 mapping of NDI streams to OBS scenes to maintain organizational clarity.

### Scenes
Create four distinct scenes, named sequentially (e.g., `NDI-1` through `NDI-4`). Clear naming is essential for the automation logic in later steps.

### Sources
Within each scene, add an **NDI Source**:
* **Source Names:** `max_video_1` through `max_video_4`.
* **Connectivity:** Ensure you are on the same network as the source machine (Max/MSP) to detect the streams.

---

### 2. Automation with Advanced Scene Switcher

The **Advanced Scene Switcher** (Tools -> Advanced Scene Switcher) acts as the central brain of the installation, handling generative transitions.

#### Initial Configuration
To access all necessary menus, navigate to the **General** tab -> **UI Settings** and uncheck:
`Hide tabs which can be represented via macros`.

#### Scene Groups
To avoid linear loops (1-2-3-4), we use **Scene Groups** as randomizing containers.
* **Type:** Random.
* **Content:** Add your four NDI scenes to the group. This allows the system to pick a random "next" scene.

#### Macros (If/Then Logic)
Macros control the audio-reactive switching. A macro is created for each scene following this logic:
* **Condition (IF):** Audio level of the current scene is above/below a specific threshold **AND** the current scene is active (this "security check" prevents background triggers).
* **Action (THEN):** Switch to a random scene within the **Scene Group**.

---

### 3. Audio-Reactive Filters (Audio Move)

The **Audio Move** filter allows audio data to control visual effects (e.g., Glitch intensity or Displacement).

#### Meter Types
* **Magnitude:** Measures average energy (RMS-like). Best for smooth, fluid movements.
* **Peak Sample:** Measures the highest digital peak. Best for sudden, glitchy reactions.
* **Peak True:** More precise than Peak Sample; calculates inter-sample peaks.
* **Input Peak (Sample/True):** Measures the raw signal *before* other filters (like EQ/Compressor) are applied.
* **Normal (No Input):** Measures the signal as it arrives at its current position in the filter chain.

#### Key Parameters
* **Base Value:** The default value when silent. (e.g., 0.10 = 10% effect intensity at all times).
* **Factor:** The multiplier for audio input. A higher factor (e.g., 70.00) causes extreme reactions to low volumes.
* **Action:** Can either toggle a filter (**Filter Enable**) or modulate a specific value (**Setting**).

---

### 4. Signal Normalization (Compression)

Since the scraped YouTube videos vary significantly in volume, an aggressive compression stage is necessary to ensure the automation triggers reliably.

#### MCompressor Configuration
Using a compressor as a "Brute Force" normalizer flattens the audio into a consistent block of energy.

| Parameter | Recommended Value | Description |
| :--- | :--- | :--- |
| **Threshold** | -31.5 dB | The level at which compression begins. Low values capture quiet signals. |
| **Ratio** | 20.00 : 1 | High compression ratio to "flatten" the signal (Limiter-style). |
| **Attack** | 0 ms | Immediate reaction to incoming audio peaks. |
| **Release** | 500 ms | Time taken to stop compressing; creates a rhythmic "pumping" effect. |
| **Output** | +20.00 dB | Makeup gain to bring the flattened signal to a loud, constant level. |

---

## 5. Deployment Strategy

There are two ways to handle varied audio signals in the workshop:
1.  **Passive:** Allow the system to idle until a sufficiently loud video is fed in.
2.  **Active (Recommended):** Use the **MCompressor** settings above to force all signals into a predictable range, ensuring the Advanced Scene Switcher macros fire consistently regardless of the source material's original quality.
