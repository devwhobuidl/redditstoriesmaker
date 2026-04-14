import os
import requests
import wave
import json
from piper.voice import PiperVoice

VOICES_DIR = "voices"

VOICE_MODELS = {
    # Premium High Quality Voices
    "Ryan (Deep Male/HQ)": "en_US-ryan-high",
    "Lessac (Natural/HQ)": "en_US-lessac-high",
    "Alan (UK Male/HQ)": "en_GB-alan-medium",
    "Amy (Clear Female/HQ)": "en_US-amy-medium"
}

AZURE_VOICES = {
    "Ava (Azure/Premium)": "en-US-AvaNeural",
    "Andrew (Azure/Premium)": "en-US-AndrewNeural",
    "Emma (Azure/Premium)": "en-US-EmmaNeural",
    "Brian (Azure/Premium)": "en-US-BrianNeural"
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
    if not rel_path:
        return None, None
        
    onnx_path = os.path.join(VOICES_DIR, f"{voice_id}.onnx")
    json_path = os.path.join(VOICES_DIR, f"{voice_id}.onnx.json")
    
    if not os.path.exists(onnx_path) or not os.path.exists(json_path):
        os.makedirs(VOICES_DIR, exist_ok=True)
        onnx_url = f"{BASE_URL}/{rel_path}/{voice_id}.onnx"
        json_url = f"{BASE_URL}/{rel_path}/{voice_id}.onnx.json"
        download_file_internal(onnx_url, onnx_path)
        download_file_internal(json_url, json_path)
        
    return onnx_path, json_path

def download_file_internal(url, dest_path):
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(dest_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

def generate_silence(duration_sec, sample_rate):
    """Generates silent PCM bytes."""
    num_samples = int(duration_sec * sample_rate)
    return b'\x00\x00' * num_samples

def generate_narration(text, voice_name, output_path, speed=1.35, pause_duration=1.0, azure_config=None):
    """
    Generates a WAV narration file from text.
    Switches between Azure Cloud and Local Piper based on voice selection and config.
    """
    # 1. Check if Azure Voice
    if voice_name in AZURE_VOICES:
        if not azure_config or not azure_config.get("key") or not azure_config.get("region"):
            raise ValueError("Azure Speech requires API Key and Region in settings.")
        
        from .azure_tts import generate_azure_narration
        full_text = " ".join(text) if isinstance(text, list) else text
        return generate_azure_narration(
            full_text, 
            output_path, 
            azure_config["key"], 
            azure_config["region"], 
            voice_name=AZURE_VOICES[voice_name],
            speed=speed
        )

    # 2. Fallback to Local Piper
    voice_id = VOICE_MODELS.get(voice_name)
    if not voice_id:
        raise ValueError(f"Unknown voice: {voice_name}")
        
    onnx_path, json_path = get_voice_path(voice_id)
    voice = PiperVoice.load(onnx_path)
    
    length_scale = 1.0 / speed
    from piper.config import SynthesisConfig
    syn_config = SynthesisConfig(length_scale=length_scale, speaker_id=0)
    
    # If text is a list, we'll join with silence
    parts = text if isinstance(text, list) else [text]
    
    with wave.open(output_path, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(voice.config.sample_rate)
        
        for i, part in enumerate(parts):
            if not part.strip(): continue
            
            # Synthesize part
            for chunk in voice.synthesize(part, syn_config=syn_config):
                wav_file.writeframes(chunk.audio_int16_bytes)
            
            # Add silence between parts (but not after the last one)
            if i < len(parts) - 1:
                silence_bytes = generate_silence(pause_duration, voice.config.sample_rate)
                wav_file.writeframes(silence_bytes)
        
    return output_path
