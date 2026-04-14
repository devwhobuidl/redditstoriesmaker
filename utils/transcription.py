import os
import re
from faster_whisper import WhisperModel

# Project Root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL_MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "whisper-tiny")

def get_transcription(audio_path, fast_mode=False, story_text=None, sync_offset=0.0, pause_multiplier=1.0, speed_boost=1.0):
    if fast_mode and story_text:
        return get_fast_transcription(audio_path, story_text, sync_offset=sync_offset, pause_multiplier=pause_multiplier, speed_boost=speed_boost)
        
    model_path = LOCAL_MODEL_PATH if os.path.exists(LOCAL_MODEL_PATH) else "tiny.en"
    
    model = WhisperModel(model_path, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(audio_path, word_timestamps=True)
    
    words = []
    for segment in segments:
        for word in segment.words:
            raw_start = word.start + sync_offset
            raw_end = word.end + sync_offset
            words.append({
                "word": word.word.strip(),
                "start": max(0.0, raw_start),
                "end": max(0.0, raw_end)
            })
    return words

def get_fast_transcription(audio_path, text, sync_offset=0.0, pause_multiplier=1.0, speed_boost=1.0):
    from pydub.utils import mediainfo
    import re
    try:
        info = mediainfo(audio_path)
        duration = float(info.get('duration', 0)) - 1.5 
        if duration < 0: duration = float(info.get('duration', 0))
    except Exception as e:
        duration = len(text.split()) * 0.4
    
    target_duration = duration / speed_boost
    paragraphs_raw = [p.strip() for p in text.split('\n\n') if p.strip()]
    if not paragraphs_raw: return []
    
    p_weights = [len(p) for p in paragraphs_raw]
    total_p_weight = sum(p_weights)
    
    words_data = []
    current_time = 0.0
    
    for p_idx, p_text in enumerate(paragraphs_raw):
        p_time = (p_weights[p_idx] / total_p_weight) * target_duration
        clean_p = re.sub(r'\s+', ' ', p_text.strip())
        p_words = clean_p.split()
        if not p_words: continue
        
        word_weights = []
        for i, w in enumerate(p_words):
            weight = len(w)
            if w.endswith(('.', '!', '?')): weight += (35 * pause_multiplier)
            elif w.endswith((',', ':', ';', '—', '-')): weight += (15 * pause_multiplier)
            word_weights.append(weight)
        
        total_word_weight = sum(word_weights)
        
        for i, w in enumerate(p_words):
            w_duration = (word_weights[i] / total_word_weight) * p_time
            raw_start = current_time + sync_offset
            raw_end = raw_start + w_duration
            words_data.append({
                "word": w,
                "start": max(0.0, raw_start),
                "end": max(0.05, raw_end)
            })
            current_time += w_duration
            
    return words_data

def group_semantically(words, max_chars=60):
    lines = []
    current_line = []
    current_chars = 0
    for w in words:
        word_len = len(w["word"])
        if current_chars + word_len > max_chars and current_line:
            lines.append(current_line)
            current_line = []
            current_chars = 0
        current_line.append(w)
        current_chars += word_len + 1
        if w["word"].endswith(('.', '!', '?')):
            lines.append(current_line)
            current_line = []
            current_chars = 0
    if current_line:
        lines.append(current_line)
    return lines
