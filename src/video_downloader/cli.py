"""Command-line interface for Video Downloader."""

import json
from dataclasses import asdict
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table
from rich.text import Text

from video_downloader import __version__
from video_downloader.doctor import run_environment_checks
from video_downloader.downloader import DownloaderService
from video_downloader.errors import VideoDownloaderError

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


@app.command()
def doctor(
    output: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            help="Output directory to test for write access.",
            file_okay=False,
            dir_okay=True,
        ),
    ] = Path("downloads"),
) -> None:
    """Check whether the local environment is ready."""
    checks = run_environment_checks(output)
    console = Console()
    table = Table(title="Video Downloader environment")
    table.add_column("Component", style="bold")
    table.add_column("Status")
    table.add_column("Details")
    table.add_column("How to fix")

    for check in checks:
        status = "[green]PASS[/green]" if check.passed else "[red]FAIL[/red]"
        table.add_row(check.component, status, check.detail, check.remedy or "-")

    console.print(table)

    failed_count = sum(not check.passed for check in checks)
    if failed_count:
        console.print(f"[red]Environment is not ready: {failed_count} check(s) failed.[/red]")
        raise typer.Exit(code=1)

    console.print("[green]Environment is ready.[/green]")


@app.command()
def download(
    url: Annotated[str, typer.Argument(help="Public video URL to download.")],
    output: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            help="Directory in which to save the video.",
            file_okay=False,
            dir_okay=True,
        ),
    ] = Path("downloads"),
) -> None:
    """Download one public video at the best available combined quality."""
    try:
        file_path = DownloaderService().download(url, output)
    except VideoDownloaderError as exc:
        typer.secho(f"Download failed: {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    typer.secho(f"Downloaded to: {file_path}", fg=typer.colors.GREEN)


@app.command()
def info(
    url: Annotated[str, typer.Argument(help="Public video URL to inspect.")],
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Print machine-readable JSON."),
    ] = False,
) -> None:
    """Read video metadata without downloading the media."""
    try:
        metadata = DownloaderService().get_metadata(url)
    except VideoDownloaderError as exc:
        typer.secho(f"Metadata failed: {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    if json_output:
        typer.echo(json.dumps(asdict(metadata), ensure_ascii=False, indent=2))
        return

    table = Table(title="Video metadata", show_header=False)
    table.add_column("Field", style="bold")
    table.add_column("Value")
    rows = (
        ("Title", metadata.title),
        ("Platform", metadata.platform),
        ("Uploader", metadata.uploader or "unknown"),
        ("Duration", _format_duration(metadata.duration_seconds)),
        ("Video ID", metadata.id),
    )
    for label, value in rows:
        table.add_row(label, Text(value))
    Console().print(table)


def _format_duration(duration_seconds: int | None) -> str:
    if duration_seconds is None:
        return "unknown"
    hours, remainder = divmod(duration_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
