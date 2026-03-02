"""CLI — paste a Reddit link, get a video."""

import logging

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
