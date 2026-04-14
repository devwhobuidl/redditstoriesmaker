# 🤖 RedditStoryVideoMaker v1.5.0

Your 100% local, high-speed Reddit video generator.

## 📁 How to Use Your Own Assets

1. **Background Videos**: Place your `.mp4` clips in the `videos/` folder. They will be randomly shuffled and stitched to match the length of your story.
2. **Background Music**: Place your `.mp3` or `.wav` files in the `music/` folder. You can select them and adjust volume in the UI.

## 🚀 Performance Modes

- **Ultra-Fast Render (Default)**: Uses optimized FFmpeg stitching for background videos. It's nearly instant compared to standard rendering.
- **Fast Mode (Sentence Captions)**: Disables Whisper AI transcription. Captions are generated based on sentence timing. Ideal for long stories where you want instant results.
- **Precise Whisper AI**: Toggle this on if you want word-for-word accuracy. (Requires an initial ~150MB download).

## 🛠️ One-Time Setup
On the first run, the app will download:
- **Whisper Tiny Model** (~150MB) for precise captions.
- **Piper TTS Base Voice** (~50MB) for high-quality narration.

After this, the app functions **100% offline**.

## ✨ Pro Tip
Use the **"Refresh Assets"** button in the UI if you add new videos or music while the app is running!
