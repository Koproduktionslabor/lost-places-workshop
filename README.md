# lost-places-workshop

<img width="2481" height="1400" alt="lostplaces_title" src="https://github.com/user-attachments/assets/e3156331-c29b-48f8-a8ba-a52d86066520" /> <br>

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
Within each scene, add an **NDI Source**. Here, too, consistent naming is important to maintain clarity (e.g. `NDI-Video-1`):
* **Source Names:** If you work with the MaxMSP setup from our workshop the NDI sources should be named `max_video_1` through `max_video_4`.
* **Connectivity:** Ensure you are on the same network as the source machine (Max/MSP) to detect the streams.  

<img width="1273" height="985" alt="lp_doc_01" src="https://github.com/user-attachments/assets/791b1db2-447f-4472-9598-6c338f42143d" /> <br>

*Note:* If you're working with video files, you can also add a local source here. Make sure the source is set to “Loop” and that “Restart playback when source becomes active” is unchecked.

---

### 2. Automation with Advanced Scene Switcher

The **Advanced Scene Switcher** (Tools -> Advanced Scene Switcher) acts as the central brain of the installation, handling generative transitions.  
The full documentation can be found [here](https://github.com/WarmUpTill/SceneSwitcher).

#### Initial Configuration
To access all necessary menus, navigate to the **General** tab -> **UI Settings** and uncheck:
`Hide tabs which can be represented via macros`.

#### Scene Groups
To avoid linear loops (1-2-3-4), we use **Scene Groups** as randomizing containers.
* **Type:** Random.
* **Content:** Add your four NDI scenes to the group. This allows the system to pick a random "next" scene. To add a scene, select a scene from the dropdown menu and click the plus sign.  

<img width="1300" height="680" alt="lp_doc_02" src="https://github.com/user-attachments/assets/26fbda8a-7af4-44a5-be03-0d15397c9e43" /> <br>

#### Macros (If/Then Logic)
Macros control the audio-reactive switching. A macro is created for each scene following this logic:
* **Condition (IF):** Audio level of the current scene is above/below a specific threshold **AND** the current scene is active (this "security check" prevents background triggers).
* **Action (THEN):** Switch to a random scene within the **Scene Group**.  

<img width="1510" height="991" alt="lp_doc_03" src="https://github.com/user-attachments/assets/f63b2dd9-2673-4319-b397-d5edd3e82374" /> <br>

You can play around with different thresholds and duration modifiers here. For example you could say that the audio source has to be above/below the threshold for a certain amount of time.

---

### 3. Audio-Reactive Filters (Audio Move)

The **Audio Move** filter allows audio data to control visual effects (e.g., Glitch intensity or Displacement). Filters can be added to any scene using the Filter button.  

<img width="216" height="375" alt="lp_doc_04" src="https://github.com/user-attachments/assets/1c9f4177-4254-4af2-8372-1de16c060763" /> <br>

The most important settings are the following:  

#### Meter Types
* **Magnitude:** Measures average energy (RMS-like). Best for smooth, fluid movements.
* **Peak Sample:** Measures the highest digital peak. Best for sudden, glitchy reactions.
* **Peak True:** More precise than Peak Sample; calculates inter-sample peaks.
* **Input Peak (Sample/True):** Measures the raw signal *before* other filters (like EQ/Compressor) are applied.
* **Normal (No Input):** Measures the signal as it arrives at its current position in the filter chain.

#### Key Parameters
* **Source/Filter/Setting:** Select the source and the specific effect or parameter you want to control in a sound-responsive way.
* **Threshold Action (only for *Filter Enable*):** What should happen when the threshold is reached?
* **Base Value:** The default value when silent. (e.g., 0.10 = 10% effect intensity at all times).
* **Factor:** The multiplier for audio input. A higher factor (e.g., 70.00) causes extreme reactions to low volumes.
* **Action:** Can either toggle a filter (**Filter Enable**) or modulate a specific value (**Setting**).

---

### 4. Signal Normalization (Compression)

Since the scraped YouTube videos vary significantly in volume, an aggressive compression stage is necessary to ensure the automation triggers reliably.

#### MCompressor Configuration
Using a compressor as a "Brute Force" normalizer flattens the audio into a consistent block of energy.  

<img width="937" height="504" alt="lp_doc_05" src="https://github.com/user-attachments/assets/37ff82e5-d336-4ab1-9618-c4a7c7ffa72d" /> <br>

| Parameter | Recommended Value | Description |
| :--- | :--- | :--- |
| **Threshold** | -31.5 dB | The level at which compression begins. Low values capture quiet signals. |
| **Ratio** | 20.00 : 1 | High compression ratio to "flatten" the signal (Limiter-style). |
| **Attack** | 0 ms | Immediate reaction to incoming audio peaks. |
| **Release** | 500 ms | Time taken to stop compressing; creates a rhythmic "pumping" effect. |
| **Output** | +20.00 dB | Makeup gain to bring the flattened signal to a loud, constant level. |

---

### 5. Deployment Strategy

There are two ways to handle varied audio signals in the workshop:
1.  **Passive:** Allow the system to idle until a sufficiently loud video is fed in.
2.  **Active (Recommended):** Use the **MCompressor** settings above to force all signals into a predictable range, ensuring the Advanced Scene Switcher macros fire consistently regardless of the source material's original quality.

---

### 6. Creative Processing: Visual and Audio Filters

Beyond the technical automation, the core of the **Digital Junkyard** aesthetic lies in creative experimentation. You are encouraged to stack and combine multiple filters to achieve a unique "data-waste" look and sound.

#### Visual Experimentation
Feel free to add multiple video filters to your NDI sources. Some recommended starting points include:
* **Color Correction:** Crush the blacks or oversaturate the image to mimic old surveillance footage.
* **Scaling/Aspect Ratio:** Stretch or distort the videos to break the "clean" 16:9 look.
* **Third-Party Shaders:** Use plugins like *Recursion Effect*, *Shadertastic* or *Retro Effects* for pixelation, scanlines, or digital noise.
* **Chain Order:** Remember that filters are processed from top to bottom. Changing the order (e.g., Glitch before or after Color Correction) can drastically change the output.

#### Sonic Textures
The audio doesn't just drive the automation; it is a primary aesthetic element. Consider adding:
* **VST Plugins:** Beyond the MCompressor, try adding Delays, Reverbs, or Bitcrushers to turn the original YouTube audio into abstract soundscapes.
* **EQing:** Use high-pass or low-pass filters to isolate specific frequencies (e.g., making it sound like it's coming through a tiny telephone speaker).

**Tip:** Every added filter can also be targeted by the **Audio Move** plugin (see Section 3), allowing the "destruction" of the image to react dynamically to the intensity of the sound.
