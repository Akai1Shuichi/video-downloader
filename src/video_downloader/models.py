"""Internal data models independent from yt-dlp dictionaries."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

Quality = Literal["best", "1080", "720", "480"]
Platform = Literal["facebook", "instagram", "tiktok", "douyin", "other"]


@dataclass(frozen=True, slots=True)
class DownloadRequest:
    """Normalized request used to download one video."""

    url: str
    quality: Quality = "best"
    output_dir: Path = Path("downloads")
    filename_template: str | None = None


@dataclass(frozen=True, slots=True)
class VideoMetadata:
    """Metadata exposed by the application."""

    id: str
    source_url: str
    platform: Platform
    title: str
    uploader: str | None = None
    duration_seconds: int | None = None
    thumbnail_url: str | None = None
    available_heights: list[int] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class DownloadResult:
    """Result returned by a complete download workflow."""

    success: bool
    file_path: Path | None = None
    metadata: VideoMetadata | None = None

