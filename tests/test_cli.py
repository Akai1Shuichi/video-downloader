import json
from pathlib import Path

from typer.testing import CliRunner

from video_downloader import __version__
from video_downloader.cli import app
from video_downloader.errors import DownloadError, FfmpegMissingError
from video_downloader.models import VideoMetadata
from video_downloader.progress import ProgressEvent, ProgressStatus

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
        def __init__(self, **_kwargs) -> None:
            pass

        def download(
            self, url: str, output: Path, filename: str | None, quality: str
        ) -> Path:
            assert url == "https://example.com/video"
            assert output == tmp_path
            assert filename is None
            assert quality == "best"
            return downloaded_file

    monkeypatch.setattr("video_downloader.cli.DownloaderService", FakeService)

    result = runner.invoke(app, ["download", "https://example.com/video", "-o", str(tmp_path)])

    assert result.exit_code == 0
    assert str(downloaded_file) in result.stdout


def test_download_command_hides_traceback_for_expected_error(monkeypatch) -> None:
    class FakeService:
        def __init__(self, **_kwargs) -> None:
            pass

        def download(
            self, _url: str, _output: Path, _filename: str | None, _quality: str
        ) -> Path:
            raise DownloadError("video unavailable")

    monkeypatch.setattr("video_downloader.cli.DownloaderService", FakeService)

    result = runner.invoke(app, ["download", "https://example.com/missing"])

    assert result.exit_code == 1
    assert "Download failed [UNKNOWN_ERROR]: video unavailable" in result.stdout
    assert "Traceback" not in result.stdout


def test_download_command_accepts_custom_filename(monkeypatch, tmp_path: Path) -> None:
    downloaded_file = tmp_path / "Tên tùy chỉnh 🎬 [abc].mp4"

    class FakeService:
        def __init__(self, **_kwargs) -> None:
            pass

        def download(
            self, _url: str, output: Path, filename: str | None, quality: str
        ) -> Path:
            assert output == tmp_path
            assert filename == "Tên tùy chỉnh 🎬"
            assert quality == "best"
            return downloaded_file

    monkeypatch.setattr("video_downloader.cli.DownloaderService", FakeService)

    result = runner.invoke(
        app,
        [
            "download",
            "https://example.com/video",
            "--output",
            str(tmp_path),
            "--filename",
            "Tên tùy chỉnh 🎬",
        ],
    )

    assert result.exit_code == 0
    assert str(downloaded_file) in result.stdout


def test_download_command_accepts_quality(monkeypatch, tmp_path: Path) -> None:
    class FakeService:
        def __init__(self, **_kwargs) -> None:
            pass

        def download(
            self, _url: str, _output: Path, _filename: str | None, quality: str
        ) -> Path:
            assert quality == "720"
            return tmp_path / "video.mp4"

    monkeypatch.setattr("video_downloader.cli.DownloaderService", FakeService)

    result = runner.invoke(app, ["download", "https://example.com/video", "--quality", "720"])

    assert result.exit_code == 0


def test_download_passes_browser_cookie_source(monkeypatch, tmp_path: Path) -> None:
    class FakeService:
        def __init__(self, **kwargs) -> None:
            assert kwargs["cookies_from_browser"] == "chrome"
            assert kwargs["browser_profile"] == "Default"

        def download(self, *_args) -> Path:
            return tmp_path / "video.mp4"

    monkeypatch.setattr("video_downloader.cli.DownloaderService", FakeService)

    result = runner.invoke(
        app,
        [
            "download",
            "https://www.douyin.com/video/123",
            "--cookies-from-browser",
            "chrome",
            "--browser-profile",
            "Default",
        ],
    )

    assert result.exit_code == 0


def test_browser_profile_requires_cookie_source() -> None:
    result = runner.invoke(
        app,
        ["info", "https://www.douyin.com/video/123", "--browser-profile", "Default"],
    )

    assert result.exit_code == 2
    assert "requires --cookies-from-browser" in result.stderr


def test_download_command_rejects_unknown_quality() -> None:
    result = runner.invoke(app, ["download", "https://example.com/video", "--quality", "4k"])

    assert result.exit_code == 2


def test_download_command_reports_missing_ffmpeg_separately(monkeypatch) -> None:
    class FakeService:
        def __init__(self, **_kwargs) -> None:
            pass

        def download(self, *_args) -> Path:
            raise FfmpegMissingError("Missing ffmpeg. Install FFmpeg and add it to PATH.")

    monkeypatch.setattr("video_downloader.cli.DownloaderService", FakeService)

    result = runner.invoke(app, ["download", "https://example.com/video"])

    assert result.exit_code == 8
    assert "Missing ffmpeg" in result.stdout
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
        def __init__(self, **_kwargs) -> None:
            pass

        def get_metadata(self, _url: str) -> VideoMetadata:
            return _metadata()

    monkeypatch.setattr("video_downloader.cli.DownloaderService", FakeService)

    result = runner.invoke(app, ["info", "https://example.com/video"])

    assert result.exit_code == 0
    for value in ("A [demo] video", "tiktok", "creator", "00:01:24", "abc123"):
        assert value in result.stdout


def test_info_command_outputs_json(monkeypatch) -> None:
    class FakeService:
        def __init__(self, **_kwargs) -> None:
            pass

        def get_metadata(self, _url: str) -> VideoMetadata:
            return _metadata()

    monkeypatch.setattr("video_downloader.cli.DownloaderService", FakeService)

    result = runner.invoke(app, ["info", "https://example.com/video", "--json"])

    assert result.exit_code == 0
    assert "Status:" not in result.stdout
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


def test_download_displays_progress_lifecycle(monkeypatch, tmp_path: Path) -> None:
    class FakeService:
        def __init__(self, progress_callback=None) -> None:
            self.callback = progress_callback

        def download(self, *_args) -> Path:
            self.callback(ProgressEvent(ProgressStatus.READING_METADATA))
            self.callback(
                ProgressEvent(
                    ProgressStatus.DOWNLOADING,
                    downloaded_bytes=50,
                    total_bytes=100,
                    speed=10,
                    eta=5,
                )
            )
            self.callback(ProgressEvent(ProgressStatus.MERGING))
            self.callback(ProgressEvent(ProgressStatus.COMPLETED))
            return tmp_path / "video.mp4"

    monkeypatch.setattr("video_downloader.cli.DownloaderService", FakeService)

    result = runner.invoke(app, ["download", "https://example.com/video"])

    assert result.exit_code == 0
    for text in ("Reading metadata", "50.0%", "Merging", "Completed", "Downloaded to"):
        assert text in result.stdout


def test_download_quiet_hides_progress_but_keeps_result(monkeypatch, tmp_path: Path) -> None:
    class FakeService:
        def __init__(self, progress_callback=None) -> None:
            assert progress_callback is None

        def download(self, *_args) -> Path:
            return tmp_path / "video.mp4"

    monkeypatch.setattr("video_downloader.cli.DownloaderService", FakeService)

    result = runner.invoke(app, ["download", "https://example.com/video", "--quiet"])

    assert result.exit_code == 0
    assert "Status:" not in result.stdout
    assert "Downloading:" not in result.stdout
    assert "Downloaded to:" in result.stdout


def test_download_handles_keyboard_interrupt(monkeypatch) -> None:
    class FakeService:
        def __init__(self, **_kwargs) -> None:
            pass

        def download(self, *_args) -> Path:
            raise KeyboardInterrupt

    monkeypatch.setattr("video_downloader.cli.DownloaderService", FakeService)

    result = runner.invoke(app, ["download", "https://example.com/video"])

    assert result.exit_code == 130
    assert "cancelled by user" in result.stdout
    assert "Traceback" not in result.stdout


def test_unexpected_error_is_hidden_without_debug(monkeypatch) -> None:
    class FakeService:
        def __init__(self, **_kwargs) -> None:
            pass

        def download(self, *_args) -> Path:
            raise RuntimeError("internal secret detail")

    monkeypatch.setattr("video_downloader.cli.DownloaderService", FakeService)

    result = runner.invoke(app, ["download", "https://example.com/video"])

    assert result.exit_code == 1
    assert "UNKNOWN_ERROR" in result.stdout
    assert "internal secret detail" not in result.stdout


def test_debug_preserves_unexpected_exception(monkeypatch) -> None:
    class FakeService:
        def __init__(self, **_kwargs) -> None:
            pass

        def download(self, *_args) -> Path:
            raise RuntimeError("debug detail")

    monkeypatch.setattr("video_downloader.cli.DownloaderService", FakeService)

    result = runner.invoke(app, ["download", "https://example.com/video", "--debug"])

    assert isinstance(result.exception, RuntimeError)
    assert str(result.exception) == "debug detail"
