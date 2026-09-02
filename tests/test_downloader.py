from pathlib import Path

import pytest

from video_downloader.downloader import DownloaderService
from video_downloader.errors import InvalidUrlError, LoginRequiredError, NetworkError
from video_downloader.progress import ProgressStatus


class FakeAdapter:
    def __init__(self, result: Path) -> None:
        self.result = result
        self.calls: list[tuple[str, Path, str | None, str]] = []

    def download(
        self,
        url: str,
        output_dir: Path,
        filename: str | None = None,
        quality: str = "best",
    ) -> Path:
        self.calls.append((url, output_dir, filename, quality))
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
    assert adapter.calls == [("https://example.com/video", tmp_path, None, "best")]


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
        ("https://example.com/video", tmp_path, "Tên tùy chỉnh 🎬", "best")
    ]


def test_service_passes_requested_quality_to_adapter(tmp_path: Path) -> None:
    adapter = FakeAdapter(tmp_path / "video.mp4")

    DownloaderService(adapter=adapter).download(
        "https://example.com/video", tmp_path, quality="720"
    )

    assert adapter.calls == [("https://example.com/video", tmp_path, None, "720")]


def test_service_normalizes_url_and_maps_metadata(tmp_path: Path) -> None:
    adapter = FakeAdapter(tmp_path / "unused.mp4")

    metadata = DownloaderService(adapter=adapter).get_metadata(
        " HTTPS://WWW.INSTAGRAM.COM:443/reel/abc#comments "
    )

    assert adapter.metadata_url == "https://www.instagram.com/reel/abc"
    assert metadata.id == "abc"
    assert metadata.platform == "instagram"


def test_service_retries_network_errors_with_exponential_backoff(tmp_path: Path) -> None:
    class FlakyAdapter(FakeAdapter):
        def download(self, *args, **kwargs) -> Path:
            if len(self.calls) < 2:
                self.calls.append((args[0], args[1], args[2], args[3]))
                raise NetworkError("temporary timeout")
            return super().download(*args, **kwargs)

    sleeps: list[float] = []
    events = []
    adapter = FlakyAdapter(tmp_path / "video.mp4")
    service = DownloaderService(
        adapter=adapter,
        progress_callback=events.append,
        max_attempts=3,
        backoff_seconds=1,
        sleeper=sleeps.append,
    )

    result = service.download("https://example.com/video", tmp_path)

    assert result == tmp_path / "video.mp4"
    assert len(adapter.calls) == 3
    assert sleeps == [1, 2]
    assert [event.status for event in events].count(ProgressStatus.RETRYING) == 2
    assert events[-1].status is ProgressStatus.COMPLETED


def test_service_stops_after_finite_network_retries(tmp_path: Path) -> None:
    class OfflineAdapter(FakeAdapter):
        def download(self, *args, **kwargs) -> Path:
            self.calls.append((args[0], args[1], args[2], args[3]))
            raise NetworkError("network unreachable")

    adapter = OfflineAdapter(tmp_path / "unused.mp4")
    with pytest.raises(NetworkError):
        DownloaderService(
            adapter=adapter,
            max_attempts=3,
            backoff_seconds=0,
            sleeper=lambda _delay: None,
        ).download("https://example.com/video", tmp_path)

    assert len(adapter.calls) == 3


def test_service_does_not_retry_login_required(tmp_path: Path) -> None:
    class PrivateAdapter(FakeAdapter):
        def download(self, *args, **kwargs) -> Path:
            self.calls.append((args[0], args[1], args[2], args[3]))
            raise LoginRequiredError("private video")

    adapter = PrivateAdapter(tmp_path / "unused.mp4")
    sleeps: list[float] = []
    with pytest.raises(LoginRequiredError):
        DownloaderService(adapter=adapter, sleeper=sleeps.append).download(
            "https://example.com/private", tmp_path
        )

    assert len(adapter.calls) == 1
    assert sleeps == []
