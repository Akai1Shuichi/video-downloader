from pathlib import Path

import pytest

from video_downloader.downloader import DownloaderService
from video_downloader.errors import InvalidUrlError


class FakeAdapter:
    def __init__(self, result: Path) -> None:
        self.result = result
        self.calls: list[tuple[str, Path, str | None]] = []

    def download(self, url: str, output_dir: Path, filename: str | None = None) -> Path:
        self.calls.append((url, output_dir, filename))
        return self.result

    def get_metadata(self, url: str):
        self.metadata_url = url
        return {"id": "abc", "title": "Example", "extractor_key": "Instagram"}


def test_service_downloads_to_requested_directory(tmp_path: Path) -> None:
    expected = tmp_path / "video.mp4"
    adapter = FakeAdapter(expected)
    service = DownloaderService(adapter=adapter)

    result = service.download("https://example.com/video", tmp_path)

    assert result == expected
    assert adapter.calls == [("https://example.com/video", tmp_path, None)]


@pytest.mark.parametrize("url", ["", "example.com/video", "ftp://example.com/video"])
def test_service_rejects_invalid_url(url: str, tmp_path: Path) -> None:
    service = DownloaderService(adapter=FakeAdapter(tmp_path / "unused.mp4"))

    with pytest.raises(InvalidUrlError, match="http"):
        service.download(url, tmp_path)


def test_service_creates_output_directory(tmp_path: Path) -> None:
    output_dir = tmp_path / "new" / "downloads"
    adapter = FakeAdapter(output_dir / "video.mp4")

    DownloaderService(adapter=adapter).download("https://example.com/video", output_dir)

    assert output_dir.is_dir()


def test_service_passes_custom_filename_to_adapter(tmp_path: Path) -> None:
    adapter = FakeAdapter(tmp_path / "video.mp4")

    DownloaderService(adapter=adapter).download(
        "https://example.com/video", tmp_path, "Tên tùy chỉnh 🎬"
    )

    assert adapter.calls == [
        ("https://example.com/video", tmp_path, "Tên tùy chỉnh 🎬")
    ]


def test_service_normalizes_url_and_maps_metadata(tmp_path: Path) -> None:
    adapter = FakeAdapter(tmp_path / "unused.mp4")

    metadata = DownloaderService(adapter=adapter).get_metadata(
        " HTTPS://WWW.INSTAGRAM.COM:443/reel/abc#comments "
    )

    assert adapter.metadata_url == "https://www.instagram.com/reel/abc"
    assert metadata.id == "abc"
    assert metadata.platform == "instagram"
