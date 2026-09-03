"""yt-dlp format selection rules for supported quality levels."""

from dataclasses import dataclass

from video_downloader.models import Quality

QUALITY_HEIGHTS: dict[Quality, int | None] = {
    "best": None,
    "1080": 1080,
    "720": 720,
    "480": 480,
}


@dataclass(frozen=True, slots=True)
class FormatSelection:
    """Format expression and stable preference order passed to yt-dlp."""

    selector: str
    sort: list[str]
    maximum_height: int | None


def select_format(quality: Quality) -> FormatSelection:
    """Select the best video and audio without exceeding a requested height."""
    maximum_height = QUALITY_HEIGHTS[quality]
    if maximum_height is None:
        selector = "bv*+ba/b"
    else:
        height_filter = f"[height<={maximum_height}]"
        unknown_height_fallback = f"[height<=?{maximum_height}]"
        selector = (
            f"bv*{height_filter}+ba/b{height_filter}/"
            f"bv*{unknown_height_fallback}+ba/b{unknown_height_fallback}"
        )

    return FormatSelection(
        selector=selector,
        # Prefer broadly playable H.264 before resolution. TikTok commonly offers its
        # highest-resolution streams only as HEVC; many players then expose just the
        # MP3 audio track and make the downloaded MP4 appear audio-only.
        sort=["vcodec:h264", "res", "fps", "acodec:aac", "ext:mp4:m4a"],
        maximum_height=maximum_height,
    )
