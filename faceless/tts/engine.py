"""Text-to-speech via Microsoft Edge TTS (free, high quality)."""

import asyncio
import logging
import tempfile
from pathlib import Path

from faceless.config import TTS_VOICE

log = logging.getLogger(__name__)


async def _tts_with_timestamps(
    text: str, output_path: Path, voice: str
) -> tuple[Path, list[dict]]:
    import edge_tts

    communicate = edge_tts.Communicate(text, voice, boundary="WordBoundary")
    subs: list[dict] = []

    with open(output_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                subs.append({
                    "text": chunk["text"],
                    "start": chunk["offset"] / 1e7,
                    "duration": chunk["duration"] / 1e7,
                })

    return output_path, subs


def generate_speech(
    text: str, voice: str | None = None
) -> tuple[Path, list[dict]]:
    """Generate TTS audio with word-level timestamps.

    Returns (audio_path, word_timestamps).
    """
    voice = voice or TTS_VOICE
    output_path = Path(tempfile.mktemp(suffix=".mp3"))

    log.info("Generating TTS (%s)...", voice)
    audio_path, subs = asyncio.run(_tts_with_timestamps(text, output_path, voice))
    log.info("TTS done: %d words, %.1f KB", len(subs), audio_path.stat().st_size / 1024)
    return audio_path, subs
