# 🤖 Microsoft Story Maker (Reddit Edition)

Your premium, high-speed Reddit video generator with **Microsoft Azure AI Integration** and **Hardware Acceleration**.

---

## 💎 Microsoft Edition Enhancements

- **Azure Cloud Voices**: Integration with Microsoft Azure Speech SDK for premium, human-like neural narrations.
- **Hardware Acceleration**: Automatic performance boost using NVENC (NVIDIA) or QSV (Intel) for near-instant rendering on Windows.
- **Fluent Design**: A sleek, modern UI inspired by Windows 11 aesthetics.

---

## 📥 Download the App (Windows)

You don't need to install Python to use this app. You can download the pre-built standalone version:

1. Go to the **[Actions]** tab in this GitHub repository.
2. Select the latest run of the **"Build Microsoft Edition (Windows)"** workflow.
3. Scroll down to **Artifacts** and download the `MicrosoftStoryMaker_Windows` ZIP file.
4. Extract the ZIP and run `MicrosoftStoryMaker.exe`.

---

## 📁 How to Use Your Own Assets

1. **Background Videos**: Place your `.mp4` clips in the `videos/` folder. They will be randomly shuffled and stitched to match the length of your story.
2. **Background Music**: Place your `.mp3` or `.wav` files in the `music/` folder. You can select them and adjust volume in the UI.

## 🚀 Performance Modes

- **Ultra-Fast Render (Default)**: Uses optimized FFmpeg stitching for background videos. It's nearly instant compared to standard rendering.
- **Fast Mode (Sentence Captions)**: Disables Whisper AI transcription. Captions are generated based on sentence timing. Ideal for long stories where you want instant results.
- **Precise Whisper AI**: Toggle this on if you want word-for-word accuracy. (Requires an initial ~150MB download).

## 🛠️ One-Time Setup
On the first run (if using local voices), the app will download:
- **Whisper Tiny Model** (~150MB) for precise captions.
- **Piper TTS Base Voice** (~50MB) for high-quality narration.

---
*Built with ❤️ for the Microsoft Ecosystem.*
