"""Pipeline: Reddit URL → video file."""

import logging
from pathlib import Path

from faceless.scrapers.reddit import scrape_url, scrape_top
from faceless.video.generator import generate_video

log = logging.getLogger(__name__)


def from_url(url: str) -> Path:
    """Scrape a Reddit post and generate a video."""
    story = scrape_url(url)
    return generate_video(story.full_text, title=story.title)


def from_top(count: int = 1) -> list[Path]:
    """Grab top Reddit stories and generate videos."""
    stories = scrape_top(limit=count)
    paths = []
    for story in stories[:count]:
        try:
            path = generate_video(story.full_text, title=story.title)
            paths.append(path)
        except Exception as exc:
            log.error("Failed on '%s': %s", story.title[:40], exc)
    return paths
