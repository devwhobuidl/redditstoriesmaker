import flet as ft
import os
import re
import shutil
import time
import datetime
import json
import threading
import ssl
import platform

# Fix for macOS SSL certificate issues during Flet client download
ssl._create_default_https_context = ssl._create_unverified_context
from utils.setup import run_setup, MODELS_DIR, VOICES_DIR
from utils.tts import generate_narration, VOICE_MODELS
from utils.transcription import get_transcription, group_semantically
from utils.video_engine import assemble_final_video

# --- CONSTANTS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEOS_DIR = os.path.join(BASE_DIR, "videos")
MUSIC_DIR = os.path.join(BASE_DIR, "music")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
BIN_DIR = os.path.join(BASE_DIR, "bin")
TEMP_DIR = os.path.join(BASE_DIR, "temp")
CONFIG_FILE = os.path.join(BASE_DIR, "config_flet.json")

for d in [VIDEOS_DIR, MUSIC_DIR, OUTPUTS_DIR, BIN_DIR, TEMP_DIR, MODELS_DIR, VOICES_DIR]:
    os.makedirs(d, exist_ok=True)

import math

class SetupApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "RedditStoryVideoMaker • 100% Local"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.padding = 0
        self.page.window_width = 1100
        self.page.window_height = 800
        self.page.bgcolor = "#0b0c0e"
        
        # Dependency check
        self.setup_env()
        
        # Load Config
        self.config = self.load_config()
        
        # State
        self.logs = []
        self.is_generating = False
        
        # UI Elements (initialized later)
        self.main_container = None
        self.setup_overlay = None
        
        self.build_ui()
        self.check_first_run()

    def setup_env(self):
        \"\"\"Configure FFmpeg paths for Mac/Windows.\"\"\"
        is_win = platform.system() == "Windows"
        ext = ".exe" if is_win else ""
        local_ffmpeg = os.path.join(BIN_DIR, f"ffmpeg{ext}")
        local_ffprobe = os.path.join(BIN_DIR, f"ffprobe{ext}")
        
        ffmpeg = local_ffmpeg if os.path.exists(local_ffmpeg) else shutil.which("ffmpeg")
        ffprobe = local_ffprobe if os.path.exists(local_ffprobe) else shutil.which("ffprobe")
        if ffmpeg: os.environ["FFMPEG_BINARY"] = ffmpeg
        if ffprobe: os.environ["FFPROBE_BINARY"] = ffprobe

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f: return json.load(f)
            except: pass
        return {
            "voice": "Ryan (Deep Male/HQ)",
            "music": "None",
            "volume": 15,
            "style": "Bold TikTok",
            "size": 80,
            "speed": 1.35, # New natural default
            "speed_boost": 1.0,
            "precise": False,
            "fast": True
        }

    def save_config(self):
        with open(CONFIG_FILE, 'w') as f: json.dump(self.config, f)

    def build_ui(self):
        # Asset Tracking
        v_count = 0
        try: 
            v_count = len([f for f in os.listdir(VIDEOS_DIR) if f.endswith(".mp4")])
        except: 
            pass
        self.asset_badge = ft.Text(f"Using {v_count} local background clips", color=ft.Colors.PURPLE_300, weight=ft.FontWeight.W_600)
        self.gen_progress = ft.ProgressBar(height=8, value=0, visible=False, color=ft.Colors.ORANGE_400, bgcolor=ft.Colors.WHITE10)
        self.gen_btn = ft.ElevatedButton(
            content=ft.Row([ft.Icon(ft.Icons.BOLT_ROUNDED, size=20), ft.Text("Create Professional Video", size=15, weight=ft.FontWeight.W_600)], spacing=10),
            height=48,
            bgcolor=ft.Colors.ORANGE_900,
            color=ft.Colors.WHITE,
            disabled=True, 
            on_click=self.start_generation,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12))
        )
        
        # --- TOP BAR ---
        self.header = ft.Container(
            padding=ft.padding.only(left=20, right=20, top=10, bottom=10),
            bgcolor="#15171e",
            content=ft.Column([
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Row([
                            ft.Icon(ft.Icons.ROCKET_LAUNCH, color=ft.Colors.ORANGE_700, size=30),
                            ft.Text("RedditStoryVideoMaker", size=22, weight=ft.FontWeight.BOLD),
                            ft.Container(
                                padding=ft.padding.symmetric(6, 12),
                                border_radius=20,
                                border=ft.border.all(1, ft.Colors.WHITE24),
                                content=ft.Text("100% Local • Offline • Fast", size=12, color=ft.Colors.WHITE70)
                            )
                        ]),
                        ft.Row([
                            self.asset_badge,
                            ft.IconButton(
                                icon=ft.Icons.FOLDER_OPEN_OUTLINED,
                                tooltip="Open Outputs Folder",
                                on_click=self.open_outputs
                            ),
                            ft.IconButton(
                                icon=ft.Icons.WB_SUNNY_OUTLINED if self.page.theme_mode == ft.ThemeMode.DARK else ft.Icons.DARK_MODE_OUTLINED,
                                tooltip="Toggle Light/Dark Mode",
                                on_click=self.toggle_theme
                            ),
                            self.gen_btn
                        ], spacing=10)
                    ]
                ),
                self.gen_progress
            ])
        )

        # --- LEFT: STORY INPUT ---
        self.title_input = ft.TextField(
            label="Video Title (Narrated First)",
            multiline=True,
            height=80,
            text_size=14,
            border_color=ft.Colors.WHITE10,
            focused_border_color=ft.Colors.ORANGE_400,
            hint_text="Enter a catchy title...",
            on_change=self.on_story_change
        )
        self.body_input = ft.TextField(
            label="Story Body",
            multiline=True,
            expand=True,
            text_size=14,
            border_color=ft.Colors.WHITE10,
            focused_border_color=ft.Colors.PURPLE_400,
            hint_text="Paste the main story content here...",
            on_change=self.on_story_change
        )
        self.duration_text = ft.Text("Estimated duration: ~0s", color=ft.Colors.WHITE54)

        # --- CENTER: SETTINGS CARDS ---
        self.voice_picker = ft.Dropdown(
            label="TTS Voice",
            value=self.config["voice"],
            options=[ft.dropdown.Option(v) for v in VOICE_MODELS.keys()],
            border_color=ft.Colors.WHITE10,
            expand=True
        )
        
        # Audio Initialization with Fallback for older Flet versions
        self.use_fallback_audio = False
        try:
            self.preview_audio = ft.Audio(src="", autoplay=False)
        except AttributeError:
            self.use_fallback_audio = True
            self.preview_audio = None
            print("Warning: ft.Audio not found. Using system fallback for previews.")
        
        # --- SLIDERS WITH LIVE LABELS ---
        def update_speed_text(e):
            self.speed_val_text.value = f\"{e.control.value:.2f}x\"
            self.save_config() # Auto-save speed pref
            self.page.update()

        self.speed_val_text = ft.Text(f\"{self.config.get('speed', 1.35):.2f}x\")
        self.speed_slider = ft.Slider(
            min=0.8, max=2.0, 
            value=self.config.get(\"speed\", 1.35), 
            divisions=24, 
            label=\"{value}x\",
            on_change=update_speed_text
        )
        
        self.music_picker = ft.Dropdown(
            label="Background Music",
            value=self.config["music"],
            options=[ft.dropdown.Option("None")],
            border_color=ft.Colors.WHITE10
        )
        self.music_val_text = ft.Text(f\"{self.config['volume']}% \")
        self.music_vol = ft.Slider(
            min=0, max=50, 
            value=self.config["volume"], 
            label=\"{value}%\",
            on_change=lambda e: setattr(self.music_val_text, \"value\", f\"{int(e.control.value)}%\") or self.page.update()
        )

        self.style_picker = ft.Dropdown(
            label="Caption Style",
            value=self.config["style"],
            options=[ft.dropdown.Option(s) for s in ["Classic Reddit", "Bold TikTok", "Minimal"]],
            border_color=ft.Colors.WHITE10
        )
        self.font_size_text = ft.Text(f\"{int(self.config['size'])}px\")
        self.font_slider = ft.Slider(
            min=40, max=120, 
            value=self.config.get(\"size\", 80), 
            divisions=80, 
            label=\"{value}px\", # Clean integer label
            on_change=lambda e: setattr(self.font_size_text, \"value\", f\"{int(e.control.value)}px\") or self.page.update()
        )
        self.font_hint = ft.Text("Larger font = better mobile readability", size=11, color=ft.Colors.WHITE30)
        
        self.speed_boost_val_text = ft.Text(f\"{self.config.get('speed_boost', 1.0):.2f}x\")
        self.speed_boost_slider = ft.Slider(
            min=1.0, max=3.0, 
            value=self.config.get(\"speed_boost\", 1.0), 
            divisions=200, 
            label=\"{value}x\",
            on_change=lambda e: setattr(self.speed_boost_val_text, \"value\", f\"{e.control.value:.2f}x\") or self.page.update()
        )

        self.precise_check = ft.Checkbox(label="Use Precise Whisper AI", value=self.config["precise"])
        self.fast_render = ft.Checkbox(label="Enabled Ultra-Fast Render", value=self.config["fast"])

        # --- RIGHT: PREVIEW & LOGS ---
        self.video_preview_container = ft.Container(
            height=350,
            bgcolor=\"#1e2026\",
            border_radius=12,
            alignment=ft.Alignment(0, 0),
            content=ft.Column([
                ft.Icon(ft.Icons.VIDEOCAM_OUTLINED, size=50, color=ft.Colors.WHITE10),
                ft.Text(\"Video will appear here after generation.\", color=ft.Colors.WHITE24, text_align=ft.TextAlign.CENTER)
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )
        self.log_output = ft.Column(
            scroll=ft.ScrollMode.ALWAYS,
            expand=True,
            spacing=5
        )

        # Main Layout Assembly
        self.main_container = ft.Column(
            expand=True,
            controls=[
                self.header,
                ft.Container(
                    padding=20,
                    expand=True,
                    content=ft.Column(
                        scroll=ft.ScrollMode.AUTO,
                        expand=True,
                        controls=[
                            ft.ResponsiveRow(
                                alignment=ft.MainAxisAlignment.START,
                                vertical_alignment=ft.CrossAxisAlignment.START,
                                spacing=20,
                                controls=[
                            # Left
                            ft.Column([
                                ft.Text(\"1. Paste Reddit Story\", size=18, weight=ft.FontWeight.BOLD),
                                self.title_input,
                                ft.Container(content=self.body_input, height=450),
                                self.duration_text,
                                ft.ElevatedButton(\"📂 Load .txt\", icon=ft.Icons.UPLOAD_FILE, on_click=lambda _: None)
                            ], col={\"sm\": 12, \"md\": 4}),
                            
                            # Center
                            ft.Column([
                                ft.Text(\"2. Audio & Settings\", size=18, weight=ft.FontWeight.BOLD),
                                ft.Card(
                                    content=ft.Container(
                                        padding=15,
                                        content=ft.Column([
                                            ft.Text(\"🎙️ Narration\", size=14, weight=ft.FontWeight.W_600),
                                            ft.Row([
                                                self.voice_picker,
                                                ft.ElevatedButton(
                                                    content=ft.Row([ft.Icon(ft.Icons.VOLUME_UP_ROUNDED, size=18), ft.Text(\"Preview Voice\")], spacing=8),
                                                    bgcolor=ft.Colors.PURPLE_900,
                                                    color=ft.Colors.WHITE,
                                                    on_click=self.play_voice_preview,
                                                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                                                )
                                            ], spacing=5),
                                            ft.Text(\"Paragraph Narration Speed\", size=12, color=ft.Colors.WHITE54),
                                            ft.Row([self.speed_slider, self.speed_val_text], spacing=5),
                                            ft.Divider(height=20, color=ft.Colors.WHITE10),
                                            ft.Text(\"🎵 Music\", size=14, weight=ft.FontWeight.W_600),
                                            self.music_picker,
                                            ft.Text(\"Volume\", size=12, color=ft.Colors.WHITE54),
                                            ft.Row([self.music_vol, self.music_val_text], spacing=5),
                                        ])
                                    )
                                ),
                                ft.Card(
                                    content=ft.Container(
                                        padding=15,
                                        content=ft.Column([
                                            ft.Text(\"📝 Rendering\", size=14, weight=ft.FontWeight.W_600),
                                            self.style_picker,
                                            ft.Text(\"Font Size\", size=12, color=ft.Colors.WHITE54),
                                            ft.Row([self.font_slider, self.font_size_text], spacing=5),
                                            self.font_hint,
                                            ft.Text(\"Caption Speed Boost (Global Velocity)\", size=12, color=ft.Colors.WHITE54),
                                            ft.Row([self.speed_boost_slider, self.speed_boost_val_text], spacing=5),
                                            self.precise_check,
                                            self.fast_render
                                        ])
                                    )
                                ),
                            ], col={\"sm\": 12, \"md\": 4}),
                            
                            # Right
                            ft.Column([
                                ft.Text(\"3. Preview & Status\", size=18, weight=ft.FontWeight.BOLD),
                                ft.Container(
                                    height=350,
                                    bgcolor=\"#1e2026\",
                                    border_radius=12,
                                    alignment=ft.Alignment(0, 0),
                                    content=self.video_preview_container
                                ),
                                ft.Text(\"📜 Generation Logs\", size=14, weight=ft.FontWeight.W_600),
                                ft.Container(
                                    height=300,
                                    bgcolor=\"#000000\",
                                    padding=10,
                                    border_radius=8,
                                    content=self.log_output
                                )
                            ], col={\"sm\": 12, \"md\": 4})
                        ]
                            )
                        ]
                    )
                )
            ]
        )

        # SETUP VIEW
        self.progress_bar = ft.ProgressBar(width=400, value=0, color=ft.Colors.ORANGE_400, bgcolor=ft.Colors.WHITE10)
        self.setup_status = ft.Text(\"Checking local models...\", size=16)
        self.setup_view = ft.Container(
            expand=True,
            bgcolor=\"#0b0c0e\",
            alignment=ft.Alignment(0, 0),
            visible=False,
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(ft.Icons.DOWNLOAD, size=50, color=ft.Colors.ORANGE_400),
                    ft.Text(\"One-time Setup\", size=24, weight=ft.FontWeight.BOLD),
                    ft.Text(\"Downloading TTS voices and Whisper AI (~350MB).\", color=ft.Colors.WHITE54),
                    ft.Container(height=20),
                    self.progress_bar,
                    self.setup_status
                ]
            )
        )

        self.page.add(ft.Stack(expand=True, controls=[self.main_container, self.setup_view]))
        if not self.use_fallback_audio:
            self.page.overlay.append(self.preview_audio)
        else:
            self.add_log(\"⚠️ Flet is outdated. Please run: pip install --upgrade flet\", ft.Colors.ORANGE_300)
            
        self.scan_assets()
        self.check_first_run()

    def run_background_setup(self):
        def on_progress(p, msg):
            self.progress_bar.value = p
            self.setup_status.value = msg
            self.page.update()
        
        run_setup(progress_callback=on_progress)
        time.sleep(1)
        self.setup_view.visible = False
        self.add_log(\"✅ Setup Complete. Ready to generate!\")
        self.page.update()

    def scan_assets(self):
        v_files = [f for f in os.listdir(VIDEOS_DIR) if f.endswith(\".mp4\")]
        m_files = [f for f in os.listdir(MUSIC_DIR) if any(f.endswith(ext) for ext in [\".mp3\", \".wav\"])]
        
        voice_badge = self.config.get(\"voice\", \"Ryan\").split(\"(\")[0].strip()
        self.asset_badge.value = f\"📂 {len(v_files)} Video Clips • {voice_badge} (HQ)\"
        self.music_picker.options = [ft.dropdown.Option(\"None\")] + [ft.dropdown.Option(m) for m in m_files]
        
        # Friendly message for empty videos
        if not v_files:
            self.add_log(\"💡 TIP: Drop background MP4s into 'videos/' folder to start! \", ft.Colors.ORANGE_300)
            self.gen_btn.tooltip = \"Please add video clips to the 'videos/' folder first.\"
            
        self.page.update()

    def on_story_change(self, e):
        combined_text = f\"{self.title_input.value} {self.body_input.value}\"
        words = len(combined_text.split())
        # Refined duration: Piper high is approx 150-160 WPM at 1.0x
        # 160 WPM = 2.66 WPS -> 1/2.66 = 0.375s per word
        base_sec = words * 0.38
        speed_factor = self.config.get(\"speed\", 1.1)
        est_sec = int(base_sec / speed_factor)
        
        self.duration_text.value = f\"Estimated duration: ~{est_sec} seconds\"
        
        # Validation: Disable button if no content
        self.gen_btn.disabled = not (self.title_input.value.strip() or self.body_input.value.strip())
        
        self.page.update()

    def play_voice_preview(self, e):
        voice_name = self.voice_picker.value
        if not voice_name: return
        
        # ... logic ...
        pass

    def add_log(self, text, color=ft.Colors.WHITE70):
        t = datetime.datetime.now().strftime(\"%H:%M:%S\")
        self.log_output.controls.append(ft.Text(f\"[{t}] {text}\", color=color, size=12, font_family=\"monospace\"))
        self.page.update()

    def generation_task(self):
        try:
            start_t = time.time()
            self.update_progress(0.1, \"🚀 Initializing Ultra-Fast Engine...\")
            # ... core logic from original main.py ...
        except Exception as e:
            self.add_log(f\"❌ Error: {str(e)}\", ft.Colors.RED_400)

def main(page: ft.Page):
    SetupApp(page)

if __name__ == \"__main__\":
    ft.app(target=main)
