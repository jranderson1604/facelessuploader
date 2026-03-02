"""Instagram Reels uploader via instagrapi."""

import logging
from pathlib import Path

from faceless.config import INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD

log = logging.getLogger(__name__)


def upload(
    video_path: str | Path,
    title: str,
    tags: list[str] | None = None,
) -> bool:
    """Upload a video as an Instagram Reel.

    Uses instagrapi for direct API access. Requires username/password.

    Returns True on success.
    """
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    if not INSTAGRAM_USERNAME or not INSTAGRAM_PASSWORD:
        log.error("Instagram credentials not configured. Set them in .env")
        return False

    tag_str = " ".join(f"#{t}" for t in (tags or ["reddit", "storytime", "shorts", "reels"]))
    caption = f"{title[:100]}\n\n{tag_str}"

    log.info("Uploading to Instagram: %s", title[:60])

    try:
        from instagrapi import Client

        cl = Client()
        cl.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
        cl.clip_upload(str(video_path), caption=caption)
        log.info("Instagram Reel upload complete")
        return True
    except ImportError:
        log.warning("instagrapi not installed. Install with: pip install instagrapi")
        return False
    except Exception as exc:
        log.error("Instagram upload failed: %s", exc)
        return False
