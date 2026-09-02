import json
from pathlib import Path

from typer.testing import CliRunner

from video_downloader import __version__
from video_downloader.cli import app
from video_downloader.errors import DownloadError
from video_downloader.models import VideoMetadata

runner = CliRunner()


def test_package_has_version() -> None:
    assert __version__ == "0.1.0"


def test_version_option() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert result.stdout.strip() == f"video-downloader {__version__}"


def test_download_command_prints_result(monkeypatch, tmp_path: Path) -> None:
    downloaded_file = tmp_path / "video [abc123].mp4"

    class FakeService:
        def download(self, url: str, output: Path) -> Path:
            assert url == "https://example.com/video"
            assert output == tmp_path
            return downloaded_file

    monkeypatch.setattr("video_downloader.cli.DownloaderService", FakeService)

    result = runner.invoke(app, ["download", "https://example.com/video", "-o", str(tmp_path)])

    assert result.exit_code == 0
    assert str(downloaded_file) in result.stdout


def test_download_command_hides_traceback_for_expected_error(monkeypatch) -> None:
    class FakeService:
        def download(self, _url: str, _output: Path) -> Path:
            raise DownloadError("video unavailable")

    monkeypatch.setattr("video_downloader.cli.DownloaderService", FakeService)

    result = runner.invoke(app, ["download", "https://example.com/missing"])

    assert result.exit_code == 1
    assert "Download failed: video unavailable" in result.stdout
    assert "Traceback" not in result.stdout


def _metadata() -> VideoMetadata:
    return VideoMetadata(
        id="abc123",
        source_url="https://www.tiktok.com/video/abc123",
        platform="tiktok",
        title="A [demo] video",
        uploader="creator",
        duration_seconds=84,
        thumbnail_url="https://example.com/thumb.jpg",
        available_heights=[480, 720],
    )


def test_info_command_displays_metadata(monkeypatch) -> None:
    class FakeService:
        def get_metadata(self, _url: str) -> VideoMetadata:
            return _metadata()

    monkeypatch.setattr("video_downloader.cli.DownloaderService", FakeService)

    result = runner.invoke(app, ["info", "https://example.com/video"])

    assert result.exit_code == 0
    for value in ("A [demo] video", "tiktok", "creator", "00:01:24", "abc123"):
        assert value in result.stdout


def test_info_command_outputs_json(monkeypatch) -> None:
    class FakeService:
        def get_metadata(self, _url: str) -> VideoMetadata:
            return _metadata()

    monkeypatch.setattr("video_downloader.cli.DownloaderService", FakeService)

    result = runner.invoke(app, ["info", "https://example.com/video", "--json"])

    assert result.exit_code == 0
    assert json.loads(result.stdout) == {
        "id": "abc123",
        "source_url": "https://www.tiktok.com/video/abc123",
        "platform": "tiktok",
        "title": "A [demo] video",
        "uploader": "creator",
        "duration_seconds": 84,
        "thumbnail_url": "https://example.com/thumb.jpg",
        "available_heights": [480, 720],
    }
