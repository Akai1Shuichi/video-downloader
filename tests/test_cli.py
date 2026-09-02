from typer.testing import CliRunner

from video_downloader import __version__
from video_downloader.cli import app

runner = CliRunner()


def test_package_has_version() -> None:
    assert __version__ == "0.1.0"


def test_version_option() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert result.stdout.strip() == f"video-downloader {__version__}"
