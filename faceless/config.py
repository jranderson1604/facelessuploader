"""Config loaded from .env."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")

TTS_VOICE = os.getenv("TTS_VOICE", "en-US-ChristopherNeural")

VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
FONT_SIZE = 60
FONT = "Arial-Bold" if os.name == "nt" else "Liberation-Sans-Bold"

BACKGROUND_DIR = BASE_DIR / "backgrounds"
OUTPUT_DIR = BASE_DIR / "output"

BACKGROUND_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
