
# WavNoiseReduction

## 1. Prerequisite

Before compiling and running the program, make sure you have the required dependencies installed. On a Linux system, you can use the following command to install them:

```sh
sudo apt install libspeexdsp-dev
```

Additionally, this program relies on **[RNNoise](https://github.com/xiph/rnnoise)** for noise reduction. Make sure to build and link **RNNoise** before using the program.

## 2. Compile

To compile the program, you can use the provided `build.sh` script. Depending on the architecture of your system, use the following commands:

### For x64:
```sh
./build.sh x64
```

### For arm64:
```sh
./build.sh arm64
```

## 3. Run the Program

Once the program is compiled and the dependencies are installed, you can run the program from the terminal. The general usage is as follows:

```sh
./WavNoiseReduction input.wav output.wav
```

- `input.wav`: The input audio file (must be in WAV format).
- `output.wav`: The output file where the processed audio will be saved.


## 4. Configuration File (`config.ini`)

The program reads a configuration file named `config.ini` to load various settings. If this file is not found, the program will generate a default configuration file. You can modify the settings in this file to change the behavior of the program.

Sample `config.ini`:

```ini
[settings]
enable_noise_gate = 1
enable_filter = 1
enable_compression = 1
threshold_dbfs = -25
hold_frames = 8
compression_threshold = 25000
enable_denoise = 1
```

### 4.1 Configuration File Explanation

The items in `config.ini` control various settings for the program's audio processing. Below is an explanation of each setting:

### 1. `enable_noise_gate`

  This setting determines whether a **noise gate** is applied to the audio. A **noise gate** reduces the volume of audio signals below a certain threshold, effectively silencing quiet or background noises.

  - **When enabled** (`1`): Audio signals quieter than a specified threshold (in dBFS) will be silenced. This is useful for removing low-level background noise or silence in the audio.
  - **When disabled** (`0`): The noise gate is not applied, and all audio, including background noise, will be processed.

---

### 2. `enable_filter`

  This setting enables or disables **filtering** in the audio processing. Filtering typically involves removing or reducing certain frequencies, such as high-frequency noise or unwanted sounds.

  - **When enabled** (`1`): Various types of filtering (e.g., low-pass or high-pass filters) will be applied to the audio to reduce noise or unwanted frequencies.
  - **When disabled** (`0`): No filtering is applied, and the audio will retain its original frequency content.

---

### 3. `enable_compression`

  This setting controls whether **dynamic compression** is applied to the audio signal. Compression reduces the dynamic range by lowering the volume of loud sounds and raising the volume of quieter sounds.

  - **When enabled** (`1`): The audio signal will be compressed to prevent loud parts from becoming too loud and to bring up quiet parts. This helps to create a more consistent overall volume.
  - **When disabled** (`0`): The audio signal will not be compressed, preserving the original dynamic range of the audio, which may result in loud parts clipping or being distorted.

---

### 4. `threshold_dbfs`

  This setting defines the **threshold** in **dBFS (decibels relative to full scale)** below which the noise gate will activate. Audio signals that are quieter than this threshold will be considered background noise and silenced.

  - **Typical value**: A value like **-25** would mean that any audio quieter than **-25 dBFS** would be silenced by the noise gate.

---

### 5. `hold_frames`

  This setting determines how many **frames** of audio should be held open by the noise gate once it detects audio above the threshold. Essentially, it sets how long the gate remains open after detecting a loud sound.

  - **Typical value**: A value like **8** means the gate will remain open for **8 frames** after detecting audio above the threshold.

---

### 6. `compression_threshold`

  This setting defines the **threshold** above which dynamic compression will be applied to the audio. Audio signals that exceed this threshold will be compressed, reducing their volume to prevent clipping or distortion.

  - **Typical value**: A value like **25000** means that any audio above **25000** will be compressed.

---

### 7. `enable_denoise`

  This setting controls whether **denoising** should be applied to the audio. **Denoising** is the process of removing unwanted noise from the audio signal, which could be background hum, static, or other types of undesirable sound artifacts.

  - **When enabled** (`1`): The audio signal will undergo a **denoising** process, where noise is identified and removed from the audio. This improves clarity, especially in noisy environments or recordings with background interference.
  - **When disabled** (`0`): No denoising is applied, and the original noise in the audio is retained. This might be useful in cases where noise removal could distort important details in the audio.
