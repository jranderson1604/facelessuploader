"""CLI — paste a Reddit link or raw text, get a video."""

import logging
from pathlib import Path

import click
from rich.console import Console
from rich.logging import RichHandler

console = Console()


def _setup_logging(verbose: bool = False):
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(message)s",
        handlers=[RichHandler(rich_tracebacks=True, show_path=False)],
    )


@click.group()
@click.option("-v", "--verbose", is_flag=True, help="Debug logging")
def main(verbose: bool):
    """Faceless Shorts — Reddit story to video generator."""
    _setup_logging(verbose)


@main.command()
@click.argument("url")
def url(url: str):
    """Generate a video from a Reddit post URL."""
    from faceless.pipeline import from_url

    path = from_url(url)
    console.print(f"\n[bold green]Done![/] Video saved to: {path}")


@main.command()
@click.option("-t", "--title", default="Untitled", help="Title shown in the video")
@click.option("-f", "--file", "filepath", type=click.Path(exists=True), help="Read story from a text file")
def text(title: str, filepath: str | None):
    """Generate a video from pasted text (no Reddit API needed).

    Paste your story and press Ctrl+Z then Enter (Windows) or Ctrl+D (Mac/Linux) when done.
    Or use --file to read from a .txt file.
    """
    from faceless.pipeline import from_text

    if filepath:
        story = Path(filepath).read_text(encoding="utf-8")
    else:
        console.print("[bold cyan]Paste your story below.[/] Press Ctrl+Z then Enter (Win) or Ctrl+D (Mac/Linux) when done:\n")
        import sys
        story = sys.stdin.read().strip()

    if not story:
        console.print("[bold red]No text provided.[/]")
        raise SystemExit(1)

    path = from_text(story, title=title)
    console.print(f"\n[bold green]Done![/] Video saved to: {path}")


@main.command()
@click.option("-n", "--count", default=1, help="Number of videos")
def auto(count: int):
    """Auto-grab top Reddit stories and make videos."""
    from faceless.pipeline import from_top

    paths = from_top(count)
    console.print(f"\n[bold green]Done![/] Generated {len(paths)} video(s):")
    for p in paths:
        console.print(f"  {p}")


if __name__ == "__main__":
    main()
