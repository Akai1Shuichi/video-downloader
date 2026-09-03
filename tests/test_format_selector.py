import pytest
from yt_dlp import YoutubeDL

from video_downloader.format_selector import select_format
from video_downloader.models import Quality


def test_best_quality_has_no_height_cap() -> None:
    result = select_format("best")

    assert result.selector == "bv*+ba/b"
    assert result.maximum_height is None


@pytest.mark.parametrize("quality", ["1080", "720", "480"])
def test_requested_quality_is_a_hard_maximum_with_lower_fallback(quality: Quality) -> None:
    result = select_format(quality)

    assert f"[height<={quality}]" in result.selector
    assert f"[height<=?{quality}]" in result.selector
    assert result.maximum_height == int(quality)
    YoutubeDL({"format": result.selector, "quiet": True})


def test_format_sort_prefers_h264_for_broad_playback_compatibility() -> None:
    result = select_format("720")

    assert result.sort == ["vcodec:h264", "res", "fps", "acodec:aac", "ext:mp4:m4a"]
