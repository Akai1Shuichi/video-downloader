from pathlib import Path

from typer.testing import CliRunner

from video_downloader.cli import app
from video_downloader.doctor import EnvironmentCheck, check_output_directory, check_python

runner = CliRunner()


def test_python_check_accepts_supported_version() -> None:
    result = check_python((3, 10, 0))

    assert result.passed is True
    assert result.detail == "3.10.0"


def test_python_check_rejects_old_version() -> None:
    result = check_python((3, 9, 18))

    assert result.passed is False
    assert "Python 3.10" in result.remedy


def test_output_directory_must_exist(tmp_path: Path) -> None:
    result = check_output_directory(tmp_path / "missing")

    assert result.passed is False
    assert "does not exist" in result.detail


def test_output_directory_is_writable(tmp_path: Path) -> None:
    result = check_output_directory(tmp_path)

    assert result.passed is True
    assert "writable" in result.detail


def test_doctor_returns_zero_when_all_checks_pass(monkeypatch) -> None:
    checks = [EnvironmentCheck("Python", True, "3.12.0")]
    monkeypatch.setattr("video_downloader.cli.run_environment_checks", lambda _output: checks)

    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0
    assert "Python" in result.stdout
    assert "PASS" in result.stdout
    assert "Environment is ready." in result.stdout


def test_doctor_returns_nonzero_and_remedy_on_failure(monkeypatch) -> None:
    checks = [EnvironmentCheck("ffmpeg", False, "not found in PATH", "Install ffmpeg.")]
    monkeypatch.setattr("video_downloader.cli.run_environment_checks", lambda _output: checks)

    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 1
    assert "FAIL" in result.stdout
    assert "Install ffmpeg." in result.stdout
    assert "Environment is not ready" in result.stdout
