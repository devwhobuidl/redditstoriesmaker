import os
import random
import subprocess
import pysubs2
from moviepy import VideoFileClip, AudioFileClip

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMP_DIR = os.path.join(PROJECT_ROOT, "temp")

def generate_ass_subtitles(captions, output_path, resolution=(1080, 1920), style="Classic Reddit", fontsize=80):
    subs = pysubs2.SSAFile()
    subs.info["PlayResX"] = resolution[0]
    subs.info["PlayResY"] = resolution[1]
    
    alignment = 5 
    if "Classic" in style:
        font_size_val = fontsize
        outline_val = 12
        primary_color = pysubs2.Color(255, 255, 255)
    elif "TikTok" in style:
        font_size_val = fontsize * 1.3
        outline_val = 14
        primary_color = pysubs2.Color(255, 252, 0)
    else:
        font_size_val = fontsize * 0.8
        outline_val = 4
        primary_color = pysubs2.Color(255, 255, 255)

    my_style = pysubs2.SSAStyle(
        fontname="Arial Black", 
        fontsize=font_size_val,
        primarycolor=primary_color,
        bold=True,
        outline=outline_val,
        outlinecolor=pysubs2.Color(0, 0, 0), 
        alignment=alignment,
        backcolor=pysubs2.Color(0, 0, 0, 240)
    )
    my_style.wrapstyle = 0 
    subs.styles["Default"] = my_style

    for line in captions:
        if not line: continue
        for i, active_word in enumerate(line):
            text_parts = []
            for j, w in enumerate(line):
                if i == j:
                    text_parts.append(f"{{\\c&H00FFFF&}}{{\\fscx105\\fscy105}}{w['word'].upper()}{{\\fscx100\\fscy100}}{{\\c&HFFFFFF&}}")
                else:
                    text_parts.append(w["word"].upper())
            event = pysubs2.SSAEvent(
                start=pysubs2.make_time(s=active_word["start"]),
                end=pysubs2.make_time(s=active_word["end"]),
                text=" ".join(text_parts)
            )
            subs.append(event)
    subs.save(output_path)
    return output_path

def fast_concat_background(video_files, target_duration, output_path, resolution=(1080, 1920)):
    concat_file = os.path.join(TEMP_DIR, "concat.txt")
    pool = list(video_files)
    random.shuffle(pool)
    current_dur = 0
    selected_videos = []
    ffprobe_bin = os.environ.get("FFPROBE_BINARY", "ffprobe")
    
    while current_dur < target_duration + 2:
        for v in pool:
            selected_videos.append(v)
            cmd = [ffprobe_bin, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", v]
            try:
                dur = float(subprocess.check_output(cmd).decode().strip())
                current_dur += dur
            except:
                current_dur += 10
            if current_dur >= target_duration + 2: break
        else:
            random.shuffle(pool)
            
    with open(concat_file, "w") as f:
        for v in selected_videos:
            f.write(f"file '{os.path.abspath(v)}'\\n")
            
    ffmpeg_bin = os.environ.get("FFMPEG_BINARY", "ffmpeg")
    cmd = [
        ffmpeg_bin, "-y", "-f", "concat", "-safe", "0", "-i", concat_file,
        "-t", str(target_duration), "-vf", f"scale={resolution[0]}:{resolution[1]}:force_original_aspect_ratio=increase,crop={resolution[0]}:{resolution[1]},setsar=1",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23", "-an", output_path
    ]
    subprocess.run(cmd, check=True)
    return output_path

def assemble_final_video(story_text, bg_clips_paths, narration_path, music_path, music_volume, captions_data, output_path, resolution=(1080, 1920), caption_style="Classic Reddit", caption_size=70, fast_render=True):
    ffmpeg_bin = os.environ.get("FFMPEG_BINARY", "ffmpeg")
    narration_clip = AudioFileClip(narration_path)
    final_dur = narration_clip.duration
    narration_clip.close()

    bg_processed = os.path.join(TEMP_DIR, "bg_engine.mp4")
    fast_concat_background(bg_clips_paths, final_dur, bg_processed, resolution)

    ass_path = os.path.join(TEMP_DIR, "subtitles.ass")
    generate_ass_subtitles(captions_data, ass_path, resolution, style=caption_style, fontsize=caption_size)

    cmd = [ffmpeg_bin, "-y", "-i", bg_processed, "-i", narration_path]
    filter_complex = []
    if music_path and os.path.exists(music_path):
        cmd += ["-stream_loop", "-1", "-i", music_path]
        filter_complex += [
            f"[2:a]volume={music_volume/100:.2f},atrim=0:{final_dur}[music]",
            f"[1:a][music]amix=inputs=2:duration=first[audio_out]"
        ]
        audio_map = "[audio_out]"
    else:
        audio_map = "1:a"

    escaped_ass = ass_path.replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
    filter_complex += [f"[0:v]subtitles='{escaped_ass}'[v_out]"]
    cmd += ["-filter_complex", ";".join(filter_complex)]
    cmd += ["-map", "[v_out]", "-map", audio_map]
    cmd += ["-c:v", "libx264", "-preset", "ultrafast", "-crf", "22", "-c:a", "aac", "-b:a", "192k", "-t", str(final_dur), output_path]
    subprocess.run(cmd, check=True)
    return output_path
