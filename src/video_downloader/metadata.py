"""Mapping helpers for metadata returned by yt-dlp."""

from typing import Any

from video_downloader.models import Platform, VideoMetadata
from video_downloader.url_utils import detect_platform


def map_video_metadata(raw: dict[str, Any], source_url: str) -> VideoMetadata:
    """Map a yt-dlp info dictionary to the stable internal model."""
    formats = raw.get("formats") or []
    heights = sorted(
        {
            int(item["height"])
            for item in formats
            if isinstance(item, dict) and isinstance(item.get("height"), (int, float))
        }
    )
    duration = raw.get("duration")
    duration_seconds = int(duration) if isinstance(duration, (int, float)) else None
    uploader = raw.get("uploader") or raw.get("channel") or raw.get("uploader_id")

    return VideoMetadata(
        id=str(raw.get("id") or "unknown"),
        source_url=source_url,
        platform=_platform_from_info(raw, source_url),
        title=str(raw.get("title") or "Untitled video"),
        uploader=str(uploader) if uploader is not None else None,
        duration_seconds=duration_seconds,
        thumbnail_url=_optional_string(raw.get("thumbnail")),
        available_heights=heights,
    )


def _platform_from_info(raw: dict[str, Any], source_url: str) -> Platform:
    extractor = str(raw.get("extractor_key") or raw.get("extractor") or "").lower()
    for platform in ("facebook", "instagram", "tiktok", "douyin"):
        if platform in extractor:
            return platform  # type: ignore[return-value]
    return detect_platform(source_url)


def _optional_string(value: Any) -> str | None:
    return str(value) if value is not None else None

