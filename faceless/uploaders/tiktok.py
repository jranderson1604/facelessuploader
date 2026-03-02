"""TikTok uploader — uses browser session cookie approach."""

import logging
import subprocess
import json
from pathlib import Path

from faceless.config import TIKTOK_SESSION_ID

log = logging.getLogger(__name__)


def upload(
    video_path: str | Path,
    title: str,
    tags: list[str] | None = None,
) -> bool:
    """Upload a video to TikTok.

    Uses the tiktok-uploader package which automates browser-based uploads.
    Requires a valid TikTok session cookie.

    Returns True on success.
    """
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    if not TIKTOK_SESSION_ID:
        log.error("TikTok session ID not configured. Set TIKTOK_SESSION_ID in .env")
        return False

    # Build caption with hashtags
    tag_str = " ".join(f"#{t}" for t in (tags or ["reddit", "storytime", "shorts"]))
    caption = f"{title[:100]} {tag_str}"

    log.info("Uploading to TikTok: %s", title[:60])

    try:
        from tiktok_uploader.upload import upload_video
        upload_video(
            str(video_path),
            description=caption,
            cookies=[{"name": "sessionid", "value": TIKTOK_SESSION_ID}],
        )
        log.info("TikTok upload complete")
        return True
    except ImportError:
        log.warning(
            "tiktok-uploader not installed. Install with: pip install tiktok-uploader"
        )
        return False
    except Exception as exc:
        log.error("TikTok upload failed: %s", exc)
        return False
