from pathlib import Path

import pytest
from yt_dlp.utils import DownloadError as YtDlpDownloadError

from video_downloader.adapters.yt_dlp_adapter import YtDlpAdapter
from video_downloader.errors import DownloadError


def test_adapter_uses_best_format_and_returns_downloaded_path(
    monkeypatch, tmp_path: Path
) -> None:
    downloaded_file = tmp_path / "example.mp4"
    downloaded_file.write_bytes(b"video")
    captured_options = {}

    class FakeYoutubeDL:
        def __init__(self, options) -> None:
            captured_options.update(options)

        def __enter__(self):
            return self

        def __exit__(self, *_args) -> None:
            return None

        def extract_info(self, url: str, *, download: bool):
            assert url == "https://example.com/video"
            assert download is True
            return {"requested_downloads": [{"filepath": str(downloaded_file)}]}

    monkeypatch.setattr("video_downloader.adapters.yt_dlp_adapter.YoutubeDL", FakeYoutubeDL)

    result = YtDlpAdapter().download("https://example.com/video", tmp_path)

    assert captured_options["format"] == "best"
    assert captured_options["noplaylist"] is True
    assert captured_options["outtmpl"].startswith(str(tmp_path))
    assert result == downloaded_file.resolve()


def test_adapter_converts_yt_dlp_error(monkeypatch, tmp_path: Path) -> None:
    class FailingYoutubeDL:
        def __init__(self, _options) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args) -> None:
            return None

        def extract_info(self, _url: str, *, download: bool):
            raise YtDlpDownloadError("ERROR: video unavailable")

    monkeypatch.setattr("video_downloader.adapters.yt_dlp_adapter.YoutubeDL", FailingYoutubeDL)

    with pytest.raises(DownloadError, match="video unavailable"):
        YtDlpAdapter().download("https://example.com/video", tmp_path)


def test_adapter_reads_metadata_without_downloading(monkeypatch) -> None:
    captured_options = {}

    class FakeYoutubeDL:
        def __init__(self, options) -> None:
            captured_options.update(options)

        def __enter__(self):
            return self

        def __exit__(self, *_args) -> None:
            return None

        def extract_info(self, url: str, *, download: bool):
            assert url == "https://example.com/video"
            assert download is False
            return {"id": "abc", "title": "Example"}

    monkeypatch.setattr("video_downloader.adapters.yt_dlp_adapter.YoutubeDL", FakeYoutubeDL)

    result = YtDlpAdapter().get_metadata("https://example.com/video")

    assert result["id"] == "abc"
    assert captured_options["skip_download"] is True
    assert captured_options["noplaylist"] is True
