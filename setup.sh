#!/bin/bash
echo "🚀 Setting up RedditStoryVideoMaker (Mac/3.12 Fix Edition)..."

# Ensure we are in a venv
if [ -z "$VIRTUAL_ENV" ]; then
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    else
        echo "Creating virtual environment..."
        python3 -m venv .venv
        source .venv/bin/activate
    fi
fi

echo "📦 Installing core dependencies..."
python -m pip install --upgrade pip
python -m pip install onnxruntime numpy<2.0.0 Pillow moviepy gradio faster-whisper pydub requests python-dotenv imageio-ffmpeg

echo "📦 Installing Piper (Mac Compatibility Mode)..."
# We install piper-tts without deps first to avoid failing on piper-phonemize
python -m pip install --no-deps piper-tts==1.2.0
python -m pip install piper-phonemize-cross==1.2.1

echo "✅ Setup complete! run 'python app.py' to launch."
