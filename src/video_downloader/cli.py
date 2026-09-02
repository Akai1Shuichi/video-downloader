"""Command-line interface for Video Downloader."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from video_downloader import __version__
from video_downloader.doctor import run_environment_checks

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
