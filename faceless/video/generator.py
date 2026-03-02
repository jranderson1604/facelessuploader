"""Video generator — background footage + TTS audio + animated subtitles."""

import logging
import random
from pathlib import Path

from moviepy import (
    AudioFileClip,
    ColorClip,
    CompositeVideoClip,
    TextClip,
    VideoFileClip,
    concatenate_videoclips,
    vfx,
)

from faceless.config import BACKGROUND_DIR, FONT, FONT_SIZE, OUTPUT_DIR, VIDEO_HEIGHT, VIDEO_WIDTH
from faceless.tts.engine import generate_speech

log = logging.getLogger(__name__)


def _get_background(duration: float) -> VideoFileClip | ColorClip:
    bg_files = list(BACKGROUND_DIR.glob("*.mp4")) + list(BACKGROUND_DIR.glob("*.webm"))

    if not bg_files:
        log.warning("No background videos in backgrounds/ — using solid color")
        return ColorClip(size=(VIDEO_WIDTH, VIDEO_HEIGHT), color=(15, 15, 25), duration=duration)

    clip = VideoFileClip(str(random.choice(bg_files)), audio=False)

    if clip.duration < duration:
        clip = concatenate_videoclips([clip] * (int(duration / clip.duration) + 1))
    clip = clip.subclipped(0, duration)

    clip = clip.resized(height=VIDEO_HEIGHT)
    if clip.w > VIDEO_WIDTH:
        x = clip.w / 2 - VIDEO_WIDTH / 2
        clip = clip.cropped(x1=x, x2=x + VIDEO_WIDTH)

    return clip


def _make_subtitles(words: list[dict]) -> list[TextClip]:
    clips = []
    chunk_size = 5
    for i in range(0, len(words), chunk_size):
        chunk = words[i : i + chunk_size]
        if not chunk:
            continue
        start = chunk[0]["start"]
        end = chunk[-1]["start"] + chunk[-1]["duration"]
        text = " ".join(w["text"] for w in chunk)

        txt = (
            TextClip(
                text=text,
                font_size=FONT_SIZE,
                color="white",
                font=FONT,
                stroke_color="black",
                stroke_width=3,
                size=(VIDEO_WIDTH - 100, None),
                method="caption",
            )
            .with_position(("center", VIDEO_HEIGHT * 0.40))
            .with_start(start)
            .with_duration(end - start)
        )
        clips.append(txt)
    return clips


def generate_video(text: str, title: str = "Untitled") -> Path:
    """Generate a faceless short video. Returns path to the .mp4."""
    log.info("Generating video: %s", title[:60])

    # TTS
    audio_path, word_timestamps = generate_speech(text)
    audio_clip = AudioFileClip(str(audio_path))
    duration = audio_clip.duration + 1.0

    # Background
    bg = _get_background(duration)

    # Subtitles
    subs = _make_subtitles(word_timestamps)

    # Title card
    title_clip = (
        TextClip(
            text=title[:80],
            font_size=FONT_SIZE + 10,
            color="yellow",
            font=FONT,
            stroke_color="black",
            stroke_width=4,
            size=(VIDEO_WIDTH - 80, None),
            method="caption",
        )
        .with_position(("center", VIDEO_HEIGHT * 0.15))
        .with_start(0)
        .with_duration(min(3.0, duration))
        .with_effects([vfx.CrossFadeIn(0.5)])
    )

    # Compose & render
    final = CompositeVideoClip(
        [bg, title_clip, *subs], size=(VIDEO_WIDTH, VIDEO_HEIGHT)
    ).with_audio(audio_clip).with_duration(duration)

    safe_title = "".join(c if c.isalnum() or c in " -_" else "" for c in title)[:50].strip()
    output_path = OUTPUT_DIR / f"{safe_title.replace(' ', '_')}.mp4"

    log.info("Rendering → %s", output_path.name)
    final.write_videofile(
        str(output_path), fps=30, codec="libx264", audio_codec="aac",
        preset="medium", threads=4, logger=None,
    )

    audio_clip.close()
    bg.close()
    final.close()

    log.info("Done: %s (%.1f MB)", output_path.name, output_path.stat().st_size / (1024 * 1024))
    return output_path
