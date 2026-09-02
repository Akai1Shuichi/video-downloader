from pathlib import Path

import pytest

from video_downloader.downloader import DownloaderService
from video_downloader.errors import InvalidUrlError


class FakeAdapter:
    def __init__(self, result: Path) -> None:
        self.result = result
        self.calls: list[tuple[str, Path]] = []

    def download(self, url: str, output_dir: Path) -> Path:
        self.calls.append((url, output_dir))
        return self.result


def test_service_downloads_to_requested_directory(tmp_path: Path) -> None:
    expected = tmp_path / "video.mp4"
    adapter = FakeAdapter(expected)
    service = DownloaderService(adapter=adapter)

    result = service.download("https://example.com/video", tmp_path)

    assert result == expected
    assert adapter.calls == [("https://example.com/video", tmp_path)]


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
