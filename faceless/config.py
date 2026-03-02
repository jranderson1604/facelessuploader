"""Centralised configuration loaded from .env and sensible defaults."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ── Reddit ───────────────────────────────────────────────────────────
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "faceless-uploader/1.0")

# ── TTS ──────────────────────────────────────────────────────────────
TTS_ENGINE = os.getenv("TTS_ENGINE", "edge")  # edge | gtts | pyttsx3
TTS_VOICE = os.getenv("TTS_VOICE", "en-US-ChristopherNeural")

# ── Video ────────────────────────────────────────────────────────────
VIDEO_WIDTH = int(os.getenv("VIDEO_WIDTH", "1080"))
VIDEO_HEIGHT = int(os.getenv("VIDEO_HEIGHT", "1920"))
BACKGROUND_VIDEO_DIR = Path(os.getenv("BACKGROUND_VIDEO_DIR", BASE_DIR / "backgrounds"))
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", BASE_DIR / "output"))
FONT_SIZE = int(os.getenv("FONT_SIZE", "60"))
FONT_COLOR = os.getenv("FONT_COLOR", "white")
SUBTITLE_STYLE = os.getenv("SUBTITLE_STYLE", "word_highlight")

# ── Uploaders ────────────────────────────────────────────────────────
YOUTUBE_CLIENT_SECRETS_FILE = os.getenv("YOUTUBE_CLIENT_SECRETS_FILE", "client_secrets.json")
TIKTOK_SESSION_ID = os.getenv("TIKTOK_SESSION_ID", "")
INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME", "")
INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD", "")

# ── Scheduler ────────────────────────────────────────────────────────
UPLOADS_PER_DAY = int(os.getenv("UPLOADS_PER_DAY", "10"))
SCHEDULE_START_HOUR = int(os.getenv("SCHEDULE_START_HOUR", "8"))
SCHEDULE_END_HOUR = int(os.getenv("SCHEDULE_END_HOUR", "22"))

# ── Web ──────────────────────────────────────────────────────────────
WEB_HOST = os.getenv("WEB_HOST", "127.0.0.1")
WEB_PORT = int(os.getenv("WEB_PORT", "5000"))
WEB_SECRET_KEY = os.getenv("WEB_SECRET_KEY", "change-me")

# Ensure output dirs exist
BACKGROUND_VIDEO_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
