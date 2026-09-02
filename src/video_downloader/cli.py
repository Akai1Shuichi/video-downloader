"""Command-line interface for Video Downloader."""

from typing import Annotated

import typer

from video_downloader import __version__

app = typer.Typer(
    name="video-downloader",
    help="Download public videos with yt-dlp and FFmpeg.",
    no_args_is_help=True,
)


def version_callback(value: bool) -> None:
    """Print the installed application version and exit."""
    if value:
        typer.echo(f"video-downloader {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            callback=version_callback,
            is_eager=True,
            help="Show the version and exit.",
        ),
    ] = None,
) -> None:
    """Download public videos with yt-dlp and FFmpeg."""

