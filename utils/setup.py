import os
import requests
import platform
import zipfile
import shutil
from huggingface_hub import snapshot_download

# Define paths relative to the project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
VOICES_DIR = os.path.join(PROJECT_ROOT, "voices")
BIN_DIR = os.path.join(PROJECT_ROOT, "bin")

def ensure_dirs():
    for d in [MODELS_DIR, VOICES_DIR, BIN_DIR]:
        os.makedirs(d, exist_ok=True)

def download_ffmpeg(progress_callback=None):
    is_win = platform.system() == "Windows"
    ext = ".exe" if is_win else ""
    ffmpeg_path = os.path.join(BIN_DIR, f"ffmpeg{ext}")
    
    if os.path.exists(ffmpeg_path):
        return ffmpeg_path

    if progress_callback: progress_callback(0.05, f"📥 Downloading FFmpeg for {platform.system()}...")
    
    if is_win:
        url = "https://github.com/ffbinaries/ffbinaries-prebuilt/releases/download/v6.1/ffmpeg-6.1-win-64.zip"
    else:
        url = "https://github.com/ffbinaries/ffbinaries-prebuilt/releases/download/v6.1/ffmpeg-6.1-osx-64.zip"
    
    zip_path = os.path.join(BIN_DIR, "ffmpeg_temp.zip")
    r = requests.get(url, stream=True)
    with open(zip_path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(BIN_DIR)
    
    os.remove(zip_path)
    
    if not is_win:
        os.chmod(ffmpeg_path, 0o755)
        probe_path = os.path.join(BIN_DIR, "ffprobe")
        if os.path.exists(probe_path): os.chmod(probe_path, 0o755)
        
    return ffmpeg_path

def download_whisper_tiny(progress_callback=None):
    model_path = os.path.join(MODELS_DIR, "whisper-tiny")
    if not os.path.exists(model_path) or not os.listdir(model_path):
        if progress_callback: progress_callback(0.1, "📥 Downloading AI Models (Whisper)...")
        snapshot_download(
            repo_id="guillaumekln/faster-whisper-tiny.en",
            local_dir=model_path,
            local_dir_use_symlinks=False
        )
    return model_path

def download_default_voice(progress_callback=None):
    voice_file = os.path.join(VOICES_DIR, "en_US-ryan-high.onnx")
    if not os.path.exists(voice_file):
        if progress_callback: progress_callback(0.6, "📥 Downloading Premium Voice (Ryan)...")
        url = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/ryan/high/en_US-ryan-high.onnx"
        cfg_url = url + ".json"
        
        r = requests.get(url, stream=True)
        with open(voice_file, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        
        r = requests.get(cfg_url)
        with open(voice_file + ".json", 'wb') as f:
            f.write(r.content)
    return voice_file

def run_setup(progress_callback=None):
    ensure_dirs()
    download_ffmpeg(progress_callback)
    download_whisper_tiny(progress_callback)
    download_default_voice(progress_callback)
    if progress_callback: progress_callback(1.0, "✅ System Ready!")
