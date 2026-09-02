"""Progress events and terminal rendering."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

import typer


class ProgressStatus(str, Enum):
    READING_METADATA = "reading_metadata"
    DOWNLOADING = "downloading"
    MERGING = "merging"
    VERIFYING = "verifying"
    RETRYING = "retrying"
    COMPLETED = "completed"


@dataclass(frozen=True, slots=True)
class ProgressEvent:
    status: ProgressStatus
    downloaded_bytes: int | None = None
    total_bytes: int | None = None
    speed: float | None = None
    eta: int | None = None
    attempt: int | None = None
    max_attempts: int | None = None
    delay_seconds: float | None = None
    message: str | None = None

    @property
    def percent(self) -> float | None:
        if not self.total_bytes or self.downloaded_bytes is None:
            return None
        return min(100.0, self.downloaded_bytes * 100 / self.total_bytes)


ProgressCallback = Callable[[ProgressEvent], None]


class TerminalProgressReporter:
    """Render concise progress updates without exposing yt-dlp internals."""

    def __init__(self, minimum_percent_step: float = 5.0) -> None:
        self._minimum_percent_step = minimum_percent_step
        self._last_percent = -minimum_percent_step
        self._last_unknown_update = 0.0

    def __call__(self, event: ProgressEvent) -> None:
        if event.status is ProgressStatus.READING_METADATA:
            typer.echo("Status: Reading metadata...")
        elif event.status is ProgressStatus.DOWNLOADING:
            self._render_download(event)
        elif event.status is ProgressStatus.MERGING:
            typer.echo("Status: Merging video and audio with FFmpeg...")
        elif event.status is ProgressStatus.VERIFYING:
            typer.echo("Status: Verifying output with ffprobe...")
        elif event.status is ProgressStatus.RETRYING:
            delay = event.delay_seconds or 0
            typer.echo(
                f"Retry {event.attempt}/{event.max_attempts} in {delay:g}s: {event.message}"
            )
        elif event.status is ProgressStatus.COMPLETED:
            typer.echo("Status: Completed.")

    def _render_download(self, event: ProgressEvent) -> None:
        percent = event.percent
        now = time.monotonic()
        if percent is not None:
            if percent < self._last_percent:
                self._last_percent = -self._minimum_percent_step
            if percent < 100 and percent < self._last_percent + self._minimum_percent_step:
                return
            self._last_percent = percent
        elif now - self._last_unknown_update < 1:
            return
        else:
            self._last_unknown_update = now

        percent_text = f"{percent:5.1f}%" if percent is not None else "  ?.?%"
        downloaded = _format_bytes(event.downloaded_bytes)
        total = _format_bytes(event.total_bytes)
        speed = f"{_format_bytes(event.speed)}/s" if event.speed else "unknown"
        eta = _format_eta(event.eta)
        typer.echo(
            f"Downloading: {percent_text} | {downloaded} / {total} | {speed} | ETA {eta}"
        )


def event_from_yt_dlp(data: dict[str, object]) -> ProgressEvent | None:
    """Map one yt-dlp progress-hook dictionary to an internal event."""
    if data.get("status") != "downloading":
        return None
    return ProgressEvent(
        status=ProgressStatus.DOWNLOADING,
        downloaded_bytes=_as_int(data.get("downloaded_bytes")),
        total_bytes=_as_int(data.get("total_bytes") or data.get("total_bytes_estimate")),
        speed=_as_float(data.get("speed")),
        eta=_as_int(data.get("eta")),
    )


def _format_bytes(value: int | float | None) -> str:
    if value is None:
        return "unknown"
    amount = float(value)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if abs(amount) < 1024 or unit == "TiB":
            return f"{amount:.1f} {unit}"
        amount /= 1024
    return "unknown"


def _format_eta(value: int | None) -> str:
    if value is None:
        return "unknown"
    minutes, seconds = divmod(max(value, 0), 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes:02d}:{seconds:02d}"


def _as_int(value: object) -> int | None:
    return int(value) if isinstance(value, (int, float)) else None


def _as_float(value: object) -> float | None:
    return float(value) if isinstance(value, (int, float)) else None
