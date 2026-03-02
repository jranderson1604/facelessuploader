"""Upload manager — distributes videos to all configured platforms."""

import logging
from dataclasses import dataclass, field
from pathlib import Path

from faceless.uploaders import youtube, tiktok, instagram

log = logging.getLogger(__name__)


@dataclass
class UploadResult:
    platform: str
    success: bool
    video_id: str | None = None
    error: str | None = None


@dataclass
class UploadReport:
    video_path: str
    title: str
    results: list[UploadResult] = field(default_factory=list)

    @property
    def all_success(self) -> bool:
        return all(r.success for r in self.results)

    @property
    def summary(self) -> str:
        lines = [f"Upload report for: {self.title}"]
        for r in self.results:
            status = "OK" if r.success else f"FAIL ({r.error})"
            lines.append(f"  {r.platform}: {status}")
        return "\n".join(lines)


def upload_to_all(
    video_path: str | Path,
    title: str,
    description: str = "",
    tags: list[str] | None = None,
    platforms: list[str] | None = None,
) -> UploadReport:
    """Upload a video to all configured platforms.

    Args:
        video_path: Path to the .mp4 file.
        title: Video title.
        description: Video description (used for YouTube).
        tags: Hashtags / tags.
        platforms: List of platforms to upload to. Default: all configured.

    Returns:
        UploadReport with per-platform results.
    """
    video_path = Path(video_path)
    platforms = platforms or ["youtube", "tiktok", "instagram"]
    report = UploadReport(video_path=str(video_path), title=title)

    for platform in platforms:
        try:
            if platform == "youtube":
                video_id = youtube.upload(
                    video_path, title=title, description=description, tags=tags
                )
                report.results.append(
                    UploadResult(platform="youtube", success=True, video_id=video_id)
                )
            elif platform == "tiktok":
                ok = tiktok.upload(video_path, title=title, tags=tags)
                report.results.append(UploadResult(platform="tiktok", success=ok))
            elif platform == "instagram":
                ok = instagram.upload(video_path, title=title, tags=tags)
                report.results.append(UploadResult(platform="instagram", success=ok))
            else:
                log.warning("Unknown platform: %s", platform)
                report.results.append(
                    UploadResult(platform=platform, success=False, error="unknown platform")
                )
        except Exception as exc:
            log.error("Upload to %s failed: %s", platform, exc)
            report.results.append(
                UploadResult(platform=platform, success=False, error=str(exc))
            )

    log.info(report.summary)
    return report
