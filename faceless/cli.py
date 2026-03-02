"""CLI interface — the main entry point for controlling everything."""

import json
import logging
import sys

import click
from rich.console import Console
from rich.table import Table
from rich.logging import RichHandler

console = Console()


def _setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[RichHandler(rich_tracebacks=True, show_path=False)],
    )


@click.group()
@click.option("-v", "--verbose", is_flag=True, help="Enable debug logging")
def main(verbose: bool):
    """Faceless Shorts — automated video generator & multi-platform uploader."""
    _setup_logging(verbose)


# ── Generate from URL ────────────────────────────────────────────────


@main.command()
@click.argument("url")
@click.option("--no-upload", is_flag=True, help="Generate video only, skip uploading")
@click.option(
    "--platform",
    "-p",
    multiple=True,
    help="Upload to specific platform(s): youtube, tiktok, instagram",
)
def url(url: str, no_upload: bool, platform: tuple[str, ...]):
    """Generate a video from a Reddit URL and upload it."""
    from faceless.pipeline import process_url

    platforms = list(platform) if platform else None
    result = process_url(url, platforms=platforms, upload=not no_upload)

    if result["status"] == "success":
        console.print(f"\n[bold green]Done![/] Video: {result['video_path']}")
        console.print(result.get("upload_report", ""))
    elif result["status"] == "skipped":
        console.print(f"[yellow]Skipped:[/] {result['reason']}")
    else:
        console.print(f"[red]Error:[/] {result.get('error', 'unknown')}")


# ── Auto mode ────────────────────────────────────────────────────────


@main.command()
@click.option("-n", "--count", default=1, help="Number of videos to generate")
@click.option("--no-upload", is_flag=True, help="Generate videos only")
@click.option("-p", "--platform", multiple=True, help="Target platform(s)")
def auto(count: int, no_upload: bool, platform: tuple[str, ...]):
    """Auto-scrape top Reddit stories and generate videos."""
    from faceless.pipeline import process_auto

    platforms = list(platform) if platform else None
    results = process_auto(count=count, platforms=platforms)

    console.print(f"\n[bold]Processed {len(results)} videos:[/]")
    for r in results:
        status = "[green]OK[/]" if r["status"] == "success" else f"[red]{r['status']}[/]"
        title = r["story"]["title"][:60] if "story" in r else "unknown"
        console.print(f"  {status} {title}")


# ── Scheduler ────────────────────────────────────────────────────────


@main.command()
@click.option("-n", "--uploads-per-day", type=int, help="Uploads per day (default: 10)")
@click.option("--start-hour", type=int, help="Start hour (default: 8)")
@click.option("--end-hour", type=int, help="End hour (default: 22)")
@click.option("-p", "--platform", multiple=True, help="Target platform(s)")
def schedule(
    uploads_per_day: int | None,
    start_hour: int | None,
    end_hour: int | None,
    platform: tuple[str, ...],
):
    """Start the automated scheduler (runs in foreground)."""
    from faceless.scheduler.scheduler import start_scheduler

    platforms = list(platform) if platform else None
    start_scheduler(
        uploads_per_day=uploads_per_day,
        start_hour=start_hour,
        end_hour=end_hour,
        platforms=platforms,
    )


# ── History ──────────────────────────────────────────────────────────


@main.command()
@click.option("--json-output", is_flag=True, help="Output as JSON")
def history(json_output: bool):
    """Show upload history."""
    from faceless.pipeline import get_history

    data = get_history()

    if json_output:
        console.print(json.dumps(data, indent=2))
        return

    if not data:
        console.print("[yellow]No uploads yet.[/]")
        return

    table = Table(title="Upload History")
    table.add_column("Date", style="cyan")
    table.add_column("Subreddit", style="green")
    table.add_column("Title", max_width=40)
    table.add_column("Platforms")

    for entry in reversed(data[-20:]):
        platforms_str = ", ".join(
            f"{'✓' if p['success'] else '✗'} {p['platform']}"
            for p in entry.get("platforms", [])
        )
        table.add_row(
            entry.get("uploaded_at", "?")[:16],
            entry.get("subreddit", "?"),
            entry.get("title", "?")[:40],
            platforms_str,
        )

    console.print(table)


# ── Auth helpers ─────────────────────────────────────────────────────


@main.group()
def auth():
    """Authenticate with upload platforms."""
    pass


@auth.command()
def youtube():
    """Authenticate with YouTube (opens browser for OAuth2)."""
    from faceless.uploaders.youtube import _get_authenticated_service

    console.print("Opening browser for YouTube authentication...")
    _get_authenticated_service()
    console.print("[green]YouTube authentication successful![/]")


# ── Web dashboard ────────────────────────────────────────────────────


@main.command()
@click.option("--host", default=None, help="Host to bind to")
@click.option("--port", type=int, default=None, help="Port to bind to")
def web(host: str | None, port: int | None):
    """Start the web dashboard."""
    from web.app import create_app
    from faceless.config import WEB_HOST, WEB_PORT

    app = create_app()
    app.run(
        host=host or WEB_HOST,
        port=port or WEB_PORT,
        debug=True,
    )


# ── Download backgrounds ────────────────────────────────────────────


@main.command()
@click.option(
    "--query",
    "-q",
    default="minecraft parkour gameplay",
    help="Search query for background video",
)
@click.option("--count", "-n", default=3, help="Number of videos to download")
def download_backgrounds(query: str, count: int):
    """Download background videos (Minecraft parkour, etc.) from YouTube."""
    import subprocess

    from faceless.config import BACKGROUND_VIDEO_DIR

    console.print(f"Downloading {count} background videos for: '{query}'")

    for i in range(1, count + 1):
        output_file = BACKGROUND_VIDEO_DIR / f"bg_{i}.mp4"
        cmd = [
            "yt-dlp",
            f"ytsearch{i}:{query}",
            "--max-downloads", "1",
            "-f", "bestvideo[height<=1080][ext=mp4]",
            "-o", str(output_file),
            "--no-playlist",
            "--quiet",
        ]
        console.print(f"  [{i}/{count}] Downloading...")
        try:
            subprocess.run(cmd, check=True, timeout=120)
            console.print(f"  [green]Saved: {output_file.name}[/]")
        except Exception as exc:
            console.print(f"  [red]Failed: {exc}[/]")

    console.print("[green]Background downloads complete![/]")


if __name__ == "__main__":
    main()
