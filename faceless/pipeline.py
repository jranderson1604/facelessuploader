"""End-to-end pipeline: scrape → generate video → upload to all platforms."""

import json
import logging
from datetime import datetime
from pathlib import Path

from faceless.config import OUTPUT_DIR
from faceless.scrapers.reddit import RedditStory, scrape_url, scrape_best_stories
from faceless.video.generator import generate_video
from faceless.uploaders.manager import upload_to_all, UploadReport

log = logging.getLogger(__name__)

HISTORY_FILE = OUTPUT_DIR / "upload_history.json"


def _load_history() -> list[dict]:
    if HISTORY_FILE.exists():
        return json.loads(HISTORY_FILE.read_text())
    return []


def _save_history(history: list[dict]):
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(json.dumps(history, indent=2, default=str))


def _already_processed(post_id: str) -> bool:
    history = _load_history()
    return any(h.get("post_id") == post_id for h in history)


def _record(story: RedditStory, video_path: Path, report: UploadReport):
    history = _load_history()
    history.append(
        {
            "post_id": story.post_id,
            "title": story.title,
            "subreddit": story.subreddit,
            "video_path": str(video_path),
            "uploaded_at": datetime.now().isoformat(),
            "platforms": [
                {"platform": r.platform, "success": r.success, "video_id": r.video_id}
                for r in report.results
            ],
        }
    )
    _save_history(history)


def process_url(
    url: str,
    platforms: list[str] | None = None,
    upload: bool = True,
) -> dict:
    """Full pipeline for a single Reddit URL.

    Returns dict with story info, video path, and upload results.
    """
    log.info("Processing URL: %s", url)
    story = scrape_url(url)

    if _already_processed(story.post_id):
        log.warning("Story already processed: %s", story.post_id)
        return {"status": "skipped", "reason": "already_processed", "story": story.to_dict()}

    video_path = generate_video(story.full_text, title=story.title)

    result = {"status": "success", "story": story.to_dict(), "video_path": str(video_path)}

    if upload:
        report = upload_to_all(
            video_path, title=story.title, description=story.full_text[:500], platforms=platforms
        )
        _record(story, video_path, report)
        result["upload_report"] = report.summary
    else:
        result["upload_report"] = "Upload skipped (--no-upload)"

    return result


def process_auto(
    count: int = 1,
    platforms: list[str] | None = None,
) -> list[dict]:
    """Auto-scrape top stories and process them.

    Returns list of result dicts.
    """
    log.info("Auto-processing %d stories", count)
    stories = scrape_best_stories(limit=count * 2)  # fetch extra in case some are dupes
    results = []

    for story in stories:
        if len(results) >= count:
            break

        if _already_processed(story.post_id):
            log.info("Skipping already-processed: %s", story.title[:50])
            continue

        try:
            video_path = generate_video(story.full_text, title=story.title)
            report = upload_to_all(
                video_path,
                title=story.title,
                description=story.full_text[:500],
                platforms=platforms,
            )
            _record(story, video_path, report)
            results.append(
                {
                    "status": "success",
                    "story": story.to_dict(),
                    "video_path": str(video_path),
                    "upload_report": report.summary,
                }
            )
        except Exception as exc:
            log.error("Failed to process story %s: %s", story.post_id, exc)
            results.append(
                {
                    "status": "error",
                    "story": story.to_dict(),
                    "error": str(exc),
                }
            )

    return results


def get_history() -> list[dict]:
    """Return the upload history."""
    return _load_history()
