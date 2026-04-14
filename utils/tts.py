import os
import requests
import wave
from piper.voice import PiperVoice

VOICES_DIR = "voices"
VOICE_MODELS = {
    "Ryan (Deep Male/HQ)": "en_US-ryan-high",
    "Lessac (Natural/HQ)": "en_US-lessac-high",
    "Alan (UK Male/HQ)": "en_GB-alan-medium",
    "Amy (Clear Female/HQ)": "en_US-amy-medium"
}
VOICE_CONFIG = {
    "Ryan (Deep Male/HQ)": {"speaker_id": 0},
    "Lessac (Natural/HQ)": {"speaker_id": 0},
    "Alan (UK Male/HQ)": {"speaker_id": 0},
    "Amy (Clear Female/HQ)": {"speaker_id": 0}
}
BASE_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0"

def get_voice_path(voice_id):
    mapping = {
        "en_US-ryan-high": "en/en_US/ryan/high",
        "en_US-lessac-high": "en/en_US/lessac/high",
        "en_GB-alan-medium": "en/en_GB/alan/medium",
        "en_US-amy-medium": "en/en_US/amy/medium"
    }
    rel_path = mapping.get(voice_id)
    if not rel_path: return None, None
        
    onnx_path = os.path.join(VOICES_DIR, f"{voice_id}.onnx")
    json_path = os.path.join(VOICES_DIR, f"{voice_id}.onnx.json")
    if not os.path.exists(onnx_path) or not os.path.exists(json_path):
        os.makedirs(VOICES_DIR, exist_ok=True)
        download_file_internal(f"{BASE_URL}/{rel_path}/{voice_id}.onnx", onnx_path)
        download_file_internal(f"{BASE_URL}/{rel_path}/{voice_id}.onnx.json", json_path)
    return onnx_path, json_path

def download_file_internal(url, dest_path):
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(dest_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

def generate_narration(text, voice_name, output_path, speed=1.35, pause_duration=1.0):
    voice_id = VOICE_MODELS.get(voice_name)
    onnx_path, json_path = get_voice_path(voice_id)
    voice = PiperVoice.load(onnx_path)
    
    length_scale = 1.0 / speed
    from piper.config import SynthesisConfig
    syn_config = SynthesisConfig(length_scale=length_scale, speaker_id=0)
    
    parts = text if isinstance(text, list) else [text]
    with wave.open(output_path, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(voice.config.sample_rate)
        for i, part in enumerate(parts):
            if not part.strip(): continue
            for chunk in voice.synthesize(part, syn_config=syn_config):
                wav_file.writeframes(chunk.audio_int16_bytes)
            if i < len(parts) - 1:
                wav_file.writeframes(b'\x00\x00' * int(pause_duration * voice.config.sample_rate))
    return output_path
