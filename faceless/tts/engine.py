"""Text-to-speech engine — supports Edge TTS (best), gTTS, and pyttsx3."""

import asyncio
import logging
import tempfile
from pathlib import Path

from faceless.config import TTS_ENGINE, TTS_VOICE

log = logging.getLogger(__name__)


async def _edge_tts(text: str, output_path: Path, voice: str) -> Path:
    """Generate speech using Microsoft Edge TTS (free, high quality)."""
    import edge_tts

    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(output_path))
    return output_path


async def _edge_tts_with_timestamps(
    text: str, output_path: Path, voice: str
) -> tuple[Path, list[dict]]:
    """Edge TTS with word-level timestamps for subtitle sync."""
    import edge_tts

    communicate = edge_tts.Communicate(text, voice)
    subs: list[dict] = []

    with open(output_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                subs.append(
                    {
                        "text": chunk["text"],
                        "start": chunk["offset"] / 1e7,  # convert to seconds
                        "duration": chunk["duration"] / 1e7,
                    }
                )

    return output_path, subs


def _gtts(text: str, output_path: Path) -> Path:
    """Generate speech using Google TTS."""
    from gtts import gTTS

    tts = gTTS(text=text, lang="en")
    tts.save(str(output_path))
    return output_path


def _pyttsx3_tts(text: str, output_path: Path) -> Path:
    """Generate speech using pyttsx3 (fully offline)."""
    import pyttsx3

    engine = pyttsx3.init()
    engine.setProperty("rate", 170)
    engine.save_to_file(text, str(output_path))
    engine.runAndWait()
    return output_path


def generate_speech(
    text: str,
    output_path: str | Path | None = None,
    engine: str | None = None,
    voice: str | None = None,
) -> Path:
    """Generate a speech audio file from text. Returns path to the .mp3 file."""
    engine = engine or TTS_ENGINE
    voice = voice or TTS_VOICE

    if output_path is None:
        output_path = Path(tempfile.mktemp(suffix=".mp3"))
    else:
        output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    log.info("Generating TTS (%s) → %s", engine, output_path.name)

    if engine == "edge":
        asyncio.run(_edge_tts(text, output_path, voice))
    elif engine == "gtts":
        _gtts(text, output_path)
    elif engine == "pyttsx3":
        _pyttsx3_tts(text, output_path)
    else:
        raise ValueError(f"Unknown TTS engine: {engine}")

    log.info("TTS complete: %s (%.1f KB)", output_path.name, output_path.stat().st_size / 1024)
    return output_path


def generate_speech_with_timestamps(
    text: str,
    output_path: str | Path | None = None,
    voice: str | None = None,
) -> tuple[Path, list[dict]]:
    """Generate speech with word-level timestamps (Edge TTS only).

    Returns (audio_path, word_timestamps) where each timestamp is
    {"text": str, "start": float_seconds, "duration": float_seconds}.
    """
    voice = voice or TTS_VOICE

    if output_path is None:
        output_path = Path(tempfile.mktemp(suffix=".mp3"))
    else:
        output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    log.info("Generating TTS with timestamps → %s", output_path.name)

    audio_path, subs = asyncio.run(_edge_tts_with_timestamps(text, output_path, voice))
    log.info("TTS complete: %d words with timestamps", len(subs))
    return audio_path, subs
