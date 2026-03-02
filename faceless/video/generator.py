"""Video generator — combines background footage, TTS audio, and animated subtitles."""

import logging
import random
import tempfile
from pathlib import Path

from moviepy.editor import (
    AudioFileClip,
    ColorClip,
    CompositeVideoClip,
    TextClip,
    VideoFileClip,
    concatenate_videoclips,
)

from faceless.config import (
    BACKGROUND_VIDEO_DIR,
    FONT_COLOR,
    FONT_SIZE,
    OUTPUT_DIR,
    VIDEO_HEIGHT,
    VIDEO_WIDTH,
)
from faceless.tts.engine import generate_speech, generate_speech_with_timestamps

log = logging.getLogger(__name__)


def _get_background_clip(duration: float) -> VideoFileClip | ColorClip:
    """Pick a random background video from the backgrounds dir, or use a solid color."""
    bg_files = list(BACKGROUND_VIDEO_DIR.glob("*.mp4")) + list(
        BACKGROUND_VIDEO_DIR.glob("*.webm")
    )

    if bg_files:
        bg_path = random.choice(bg_files)
        log.info("Using background: %s", bg_path.name)
        clip = VideoFileClip(str(bg_path), audio=False)

        # Loop if background is shorter than needed
        if clip.duration < duration:
            loops_needed = int(duration / clip.duration) + 1
            clip = concatenate_videoclips([clip] * loops_needed)

        clip = clip.subclip(0, duration)

        # Resize to vertical short format
        clip = clip.resize(height=VIDEO_HEIGHT)
        w = clip.w
        if w > VIDEO_WIDTH:
            x_center = w / 2 - VIDEO_WIDTH / 2
            clip = clip.crop(x1=x_center, x2=x_center + VIDEO_WIDTH)

        return clip
    else:
        log.warning("No background videos found — using dark gradient")
        return ColorClip(
            size=(VIDEO_WIDTH, VIDEO_HEIGHT),
            color=(15, 15, 25),
            duration=duration,
        )


def _build_subtitle_clips(
    words: list[dict], video_width: int, video_height: int
) -> list[TextClip]:
    """Create animated word-highlight subtitle clips from timestamps."""
    clips = []
    chunk_size = 5  # words per subtitle group
    chunks = [words[i : i + chunk_size] for i in range(0, len(words), chunk_size)]

    for chunk in chunks:
        if not chunk:
            continue

        start_time = chunk[0]["start"]
        end_time = chunk[-1]["start"] + chunk[-1]["duration"]
        text = " ".join(w["text"] for w in chunk)

        txt_clip = (
            TextClip(
                text,
                fontsize=FONT_SIZE,
                color=FONT_COLOR,
                font="Liberation-Sans-Bold",
                stroke_color="black",
                stroke_width=3,
                size=(video_width - 100, None),
                method="caption",
            )
            .set_position(("center", video_height * 0.40))
            .set_start(start_time)
            .set_duration(end_time - start_time)
        )
        clips.append(txt_clip)

    return clips


def _build_simple_subtitles(
    text: str, audio_duration: float, video_width: int, video_height: int
) -> list[TextClip]:
    """Fallback: evenly-timed subtitle chunks when no timestamps available."""
    words = text.split()
    chunk_size = 5
    chunks = [" ".join(words[i : i + chunk_size]) for i in range(0, len(words), chunk_size)]
    time_per_chunk = audio_duration / len(chunks) if chunks else audio_duration
    clips = []

    for i, chunk_text in enumerate(chunks):
        txt_clip = (
            TextClip(
                chunk_text,
                fontsize=FONT_SIZE,
                color=FONT_COLOR,
                font="Liberation-Sans-Bold",
                stroke_color="black",
                stroke_width=3,
                size=(video_width - 100, None),
                method="caption",
            )
            .set_position(("center", video_height * 0.40))
            .set_start(i * time_per_chunk)
            .set_duration(time_per_chunk)
        )
        clips.append(txt_clip)

    return clips


def generate_video(
    text: str,
    title: str = "Untitled",
    output_filename: str | None = None,
    use_timestamps: bool = True,
) -> Path:
    """Generate a complete faceless short video.

    Args:
        text: The story/content text to narrate.
        title: Used for the output filename if output_filename is not set.
        output_filename: Explicit output filename.
        use_timestamps: Use word-level timestamps for subtitles (Edge TTS only).

    Returns:
        Path to the generated .mp4 file.
    """
    log.info("Generating video for: %s", title[:60])

    # 1. Generate TTS audio
    if use_timestamps:
        try:
            audio_path, word_timestamps = generate_speech_with_timestamps(text)
        except Exception:
            log.warning("Timestamp TTS failed, falling back to simple TTS")
            audio_path = generate_speech(text)
            word_timestamps = []
    else:
        audio_path = generate_speech(text)
        word_timestamps = []

    audio_clip = AudioFileClip(str(audio_path))
    duration = audio_clip.duration + 1.0  # add 1s padding

    # 2. Background video
    bg_clip = _get_background_clip(duration)

    # 3. Subtitles
    if word_timestamps:
        subtitle_clips = _build_subtitle_clips(
            word_timestamps, VIDEO_WIDTH, VIDEO_HEIGHT
        )
    else:
        subtitle_clips = _build_simple_subtitles(
            text, audio_clip.duration, VIDEO_WIDTH, VIDEO_HEIGHT
        )

    # 4. Title card (first 3 seconds)
    title_display = title[:80]  # truncate long titles
    title_clip = (
        TextClip(
            title_display,
            fontsize=FONT_SIZE + 10,
            color="yellow",
            font="Liberation-Sans-Bold",
            stroke_color="black",
            stroke_width=4,
            size=(VIDEO_WIDTH - 80, None),
            method="caption",
        )
        .set_position(("center", VIDEO_HEIGHT * 0.15))
        .set_start(0)
        .set_duration(min(3.0, duration))
        .crossfadein(0.5)
    )

    # 5. Compose everything
    final = CompositeVideoClip(
        [bg_clip, title_clip, *subtitle_clips],
        size=(VIDEO_WIDTH, VIDEO_HEIGHT),
    ).set_audio(audio_clip)

    final = final.set_duration(duration)

    # 6. Output
    if output_filename is None:
        safe_title = "".join(c if c.isalnum() or c in " -_" else "" for c in title)[:50]
        output_filename = f"{safe_title.strip().replace(' ', '_')}.mp4"

    output_path = OUTPUT_DIR / output_filename
    output_path.parent.mkdir(parents=True, exist_ok=True)

    log.info("Rendering video → %s", output_path)
    final.write_videofile(
        str(output_path),
        fps=30,
        codec="libx264",
        audio_codec="aac",
        preset="medium",
        threads=4,
        logger=None,  # suppress moviepy progress bar in logs
    )

    # Cleanup temp files
    audio_clip.close()
    bg_clip.close()
    final.close()

    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    log.info("Video complete: %s (%.1f MB)", output_path.name, file_size_mb)
    return output_path
