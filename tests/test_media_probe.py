import json
import subprocess
from pathlib import Path

import pytest

from video_downloader.errors import FfmpegMissingError, MediaValidationError
from video_downloader.media_probe import MediaProbe, source_has_audio


def test_inspect_reads_video_audio_and_height(monkeypatch, tmp_path: Path) -> None:
    payload = {
        "streams": [
            {"codec_type": "video", "height": 720},
            {"codec_type": "audio"},
        ],
        "format": {"format_name": "mov,mp4"},
    }
    completed = subprocess.CompletedProcess([], 0, json.dumps(payload), "")
    monkeypatch.setattr("video_downloader.media_probe.shutil.which", lambda _name: "/bin/tool")
    monkeypatch.setattr("video_downloader.media_probe.subprocess.run", lambda *_a, **_k: completed)

    result = MediaProbe().inspect(tmp_path / "video.mp4")

    assert result.video_streams == 1
    assert result.audio_streams == 1
    assert result.height == 720
    assert result.format_name == "mov,mp4"


def test_verify_rejects_missing_required_audio(monkeypatch, tmp_path: Path) -> None:
    payload = {"streams": [{"codec_type": "video", "height": 480}]}
    completed = subprocess.CompletedProcess([], 0, json.dumps(payload), "")
    monkeypatch.setattr("video_downloader.media_probe.shutil.which", lambda _name: "/bin/tool")
    monkeypatch.setattr("video_downloader.media_probe.subprocess.run", lambda *_a, **_k: completed)

    with pytest.raises(MediaValidationError, match="source has audio"):
        MediaProbe().verify(tmp_path / "video.mp4", require_audio=True)


def test_verify_rejects_output_without_video(monkeypatch, tmp_path: Path) -> None:
    payload = {"streams": [{"codec_type": "audio"}]}
    completed = subprocess.CompletedProcess([], 0, json.dumps(payload), "")
    monkeypatch.setattr("video_downloader.media_probe.shutil.which", lambda _name: "/bin/tool")
    monkeypatch.setattr("video_downloader.media_probe.subprocess.run", lambda *_a, **_k: completed)

    with pytest.raises(MediaValidationError, match="video stream"):
        MediaProbe().verify(tmp_path / "audio-only.m4a", require_audio=False)


def test_ensure_tools_has_specific_missing_ffmpeg_error(monkeypatch) -> None:
    monkeypatch.setattr(
        "video_downloader.media_probe.shutil.which",
        lambda name: None if name == "ffmpeg" else "/usr/bin/ffprobe",
    )

    with pytest.raises(FfmpegMissingError, match="Missing ffmpeg"):
        MediaProbe().ensure_tools()


def test_source_audio_detection() -> None:
    assert source_has_audio({"formats": [{"acodec": "none"}, {"acodec": "aac"}]})
    assert not source_has_audio({"formats": [{"acodec": "none"}]})
