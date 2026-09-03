"""Offline contract tests covering all four MVP platforms."""

from pathlib import Path

import pytest

from video_downloader.adapters.yt_dlp_adapter import YtDlpAdapter
from video_downloader.downloader import DownloaderService
from video_downloader.media_probe import MediaProbeResult

PLATFORM_CASES = (
    ("facebook", "https://fb.watch/AbCdEf12/", "Facebook"),
    ("instagram", "https://www.instagram.com/reel/AbCdEf12/", "Instagram"),
    ("tiktok", "https://vm.tiktok.com/ZMAbCdEf/", "TikTok"),
    ("douyin", "https://v.douyin.com/AbCdEf12/", "Douyin"),
)


class FakeMediaProbe:
    def ensure_tools(self) -> None:
        pass

    def verify(self, _file_path: Path, require_audio: bool) -> MediaProbeResult:
        assert require_audio is True
        return MediaProbeResult(video_streams=1, audio_streams=1, height=720, format_name="mp4")


@pytest.mark.parametrize(("platform", "url", "extractor_key"), PLATFORM_CASES)
def test_platform_metadata_and_download_contract_is_fully_offline(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    platform: str,
    url: str,
    extractor_key: str,
) -> None:
    """Exercise normalization, metadata mapping and adapter download with a mocked yt-dlp."""
    downloaded_file = tmp_path / f"{platform}.mp4"
    captured_download_options: list[dict[str, object]] = []

    class FakeYoutubeDL:
        def __init__(self, options: dict[str, object]) -> None:
            self.options = options
            self.params = options

        def __enter__(self):
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def extract_info(self, requested_url: str, *, download: bool):
            assert requested_url == url
            metadata = {
                "id": f"{platform}-id",
                "title": f"Public {platform} video",
                "extractor_key": extractor_key,
                "uploader": "public-account",
                "duration": 12,
                "formats": [
                    {"height": 480, "vcodec": "h264", "acodec": "none"},
                    {"height": 720, "vcodec": "h264", "acodec": "none"},
                    {"vcodec": "none", "acodec": "aac"},
                ],
            }
            assert download is False
            return metadata

        def process_info(self, metadata: dict[str, object]) -> None:
            captured_download_options.append(self.options)
            downloaded_file.write_bytes(b"mock media")
            metadata["filepath"] = str(downloaded_file)

        def prepare_filename(self, _info: dict[str, object]) -> str:
            return str(downloaded_file)

    monkeypatch.setattr("video_downloader.adapters.yt_dlp_adapter.YoutubeDL", FakeYoutubeDL)
    service = DownloaderService(adapter=YtDlpAdapter(media_probe=FakeMediaProbe()))

    metadata = service.get_metadata(url)
    result = service.download(url, tmp_path, quality="720")

    assert metadata.platform == platform
    assert metadata.available_heights == [480, 720]
    assert result == downloaded_file.resolve()
    assert captured_download_options[0]["noplaylist"] is True
    assert "[height<=720]" in str(captured_download_options[0]["format"])
    if platform == "tiktok":
        assert str(captured_download_options[0]["impersonate"]) == "chrome"
    else:
        assert "impersonate" not in captured_download_options[0]
