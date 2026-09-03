"""Opt-in smoke tests against user-supplied public URLs.

These tests are deliberately skipped unless ``--run-network`` is passed. No live URL is
committed because social-media URLs expire, disappear, or change privacy state frequently.
"""

import os
from pathlib import Path
from typing import cast

import pytest

from video_downloader.downloader import DownloaderService
from video_downloader.errors import LoginRequiredError, VideoUnavailableError
from video_downloader.media_probe import MediaProbe
from video_downloader.models import Browser

PLATFORM_URL_VARIABLES = {
    "facebook": "VD_SMOKE_FACEBOOK_URL",
    "instagram": "VD_SMOKE_INSTAGRAM_URL",
    "tiktok": "VD_SMOKE_TIKTOK_URL",
    "douyin": "VD_SMOKE_DOUYIN_URL",
}

pytestmark = pytest.mark.network


def _required_url(variable: str) -> str:
    value = os.environ.get(variable)
    if not value:
        pytest.skip(f"set {variable} to a public test video URL")
    return value


def _service(platform: str | None = None) -> DownloaderService:
    if platform not in {"tiktok", "douyin"}:
        return DownloaderService()
    browser = os.environ.get("VD_SMOKE_COOKIES_FROM_BROWSER")
    if not browser:
        return DownloaderService()
    return DownloaderService(
        cookies_from_browser=cast(Browser, browser),
        browser_profile=os.environ.get("VD_SMOKE_BROWSER_PROFILE"),
    )


@pytest.mark.parametrize(("platform", "variable"), PLATFORM_URL_VARIABLES.items())
def test_public_platform_metadata_download_and_audio(
    tmp_path: Path,
    platform: str,
    variable: str,
) -> None:
    url = _required_url(variable)
    service = _service(platform)

    metadata = service.get_metadata(url)
    file_path = service.download(url, tmp_path / platform)
    media = MediaProbe().inspect(file_path)

    assert metadata.platform == platform
    assert metadata.id != "unknown"
    assert file_path.stat().st_size > 0
    assert media.video_streams > 0
    assert media.audio_streams > 0


@pytest.mark.parametrize("quality", ["best", "720"])
def test_live_quality_selection(tmp_path: Path, quality: str) -> None:
    url = _required_url("VD_SMOKE_QUALITY_URL")

    file_path = DownloaderService().download(url, tmp_path / quality, quality=quality)
    media = MediaProbe().inspect(file_path)

    assert media.video_streams > 0
    if quality == "720" and media.height is not None:
        assert media.height <= 720


def test_live_quality_falls_back_below_720(tmp_path: Path) -> None:
    url = _required_url("VD_SMOKE_FALLBACK_URL")
    service = DownloaderService()
    metadata = service.get_metadata(url)
    heights = [height for height in metadata.available_heights if height > 0]
    if not heights or max(heights) >= 720:
        pytest.skip("fallback sample must expose video only below 720p")

    file_path = service.download(url, tmp_path / "fallback", quality="720")
    media = MediaProbe().inspect(file_path)

    assert media.video_streams > 0
    assert media.height is None or media.height < 720


def test_deleted_or_private_video_is_classified() -> None:
    url = _required_url("VD_SMOKE_UNAVAILABLE_URL")

    with pytest.raises((VideoUnavailableError, LoginRequiredError)):
        DownloaderService(max_attempts=1).get_metadata(url)
