"""Scheduler — runs the pipeline automatically N times per day."""

import logging
import random
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from faceless.config import SCHEDULE_END_HOUR, SCHEDULE_START_HOUR, UPLOADS_PER_DAY
from faceless.pipeline import process_auto

log = logging.getLogger(__name__)


def _run_job(platforms: list[str] | None = None):
    """Single scheduled job: generate and upload one video."""
    log.info("Scheduler triggered at %s", datetime.now().isoformat())
    try:
        results = process_auto(count=1, platforms=platforms)
        for r in results:
            if r["status"] == "success":
                log.info("Scheduled upload succeeded: %s", r["story"]["title"][:50])
            else:
                log.warning("Scheduled upload issue: %s", r.get("error", "unknown"))
    except Exception as exc:
        log.error("Scheduled job failed: %s", exc)


def start_scheduler(
    uploads_per_day: int | None = None,
    start_hour: int | None = None,
    end_hour: int | None = None,
    platforms: list[str] | None = None,
):
    """Start the blocking scheduler.

    Distributes uploads_per_day evenly between start_hour and end_hour.
    """
    uploads = uploads_per_day or UPLOADS_PER_DAY
    start_h = start_hour or SCHEDULE_START_HOUR
    end_h = end_hour or SCHEDULE_END_HOUR

    hours_range = end_h - start_h
    if hours_range <= 0:
        hours_range = 14  # fallback

    # Calculate interval in minutes between uploads
    interval_minutes = max(5, (hours_range * 60) // uploads)

    log.info(
        "Starting scheduler: %d uploads/day, every %d min, %d:00–%d:00",
        uploads,
        interval_minutes,
        start_h,
        end_h,
    )

    scheduler = BlockingScheduler()

    # Add a small random offset (0–10 min) to each run so posts aren't exactly periodic
    jitter_minutes = random.randint(0, 10)

    scheduler.add_job(
        _run_job,
        trigger="interval",
        minutes=interval_minutes,
        start_date=f"{datetime.now().strftime('%Y-%m-%d')} {start_h:02d}:{jitter_minutes:02d}:00",
        kwargs={"platforms": platforms},
        id="faceless_upload",
        name="Faceless Shorts Upload",
        max_instances=1,
    )

    print(f"\nScheduler running: {uploads} uploads/day every ~{interval_minutes} min")
    print(f"Active hours: {start_h}:00 – {end_h}:00")
    print("Press Ctrl+C to stop.\n")

    try:
        scheduler.start()
    except KeyboardInterrupt:
        log.info("Scheduler stopped by user")
        scheduler.shutdown()
