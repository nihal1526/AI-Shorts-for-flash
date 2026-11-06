import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"
FRONTEND_DIR = BASE_DIR / "frontend"
STORAGE_DIR = BASE_DIR / "storage"

DOWNLOADS_DIR = STORAGE_DIR / "downloads"
RENDERED_DIR = STORAGE_DIR / "rendered"
TEMP_DIR = STORAGE_DIR / "temp"

# Ensure directories exist
for directory in [DOWNLOADS_DIR, RENDERED_DIR, TEMP_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Server Configuration
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", 8000))

# Subtitle styling presets (ASS subtitle formatting)
SUBTITLE_PRESETS = {
    "hormozi": {
        "name": "Viral Yellow (Hormozi)",
        "fontname": "Arial Black",
        "fontsize": 24,
        "primary_color": "&H00FFFFFF",      # White text
        "highlight_color": "&H0000E6FF",    # Bright Yellow in BGR (&HBBGGRR)
        "outline_color": "&H00000000",      # Pure Black
        "outline": 4,
        "shadow": 2,
        "bold": 1,
        "alignment": 2,                     # Bottom Center (numpad 2)
        "margin_v": 130
    },
    "cyber_cyan": {
        "name": "Neon Aqua (MrBeast)",
        "fontname": "Arial Black",
        "fontsize": 24,
        "primary_color": "&H00FFFFFF",
        "highlight_color": "&H00FFFF00",    # Cyan / Aqua (&H00FFFF00)
        "outline_color": "&H00000000",
        "outline": 4,
        "shadow": 2,
        "bold": 1,
        "alignment": 2,
        "margin_v": 130
    },
    "emerald": {
        "name": "Electric Emerald",
        "fontname": "Arial Black",
        "fontsize": 24,
        "primary_color": "&H00FFFFFF",
        "highlight_color": "&H0000FF33",    # Vivid Green
        "outline_color": "&H00000000",
        "outline": 4,
        "shadow": 2,
        "bold": 1,
        "alignment": 2,
        "margin_v": 130
    },
    "clean_white": {
        "name": "Minimalist White",
        "fontname": "Trebuchet MS",
        "fontsize": 22,
        "primary_color": "&H00FFFFFF",
        "highlight_color": "&H00FFFFFF",
        "outline_color": "&H00000000",
        "outline": 3,
        "shadow": 3,
        "bold": 1,
        "alignment": 2,
        "margin_v": 130
    }
}
