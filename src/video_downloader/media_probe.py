"""FFmpeg availability and ffprobe-based output verification."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from video_downloader.errors import FfmpegMissingError, MediaValidationError


@dataclass(frozen=True, slots=True)
class MediaProbeResult:
    """Streams relevant to validating a downloaded file."""

    video_streams: int
    audio_streams: int
    height: int | None
    format_name: str | None


class MediaProbe:
    """Locate FFmpeg tools and verify media streams with ffprobe."""

    def ensure_tools(self) -> None:
        missing = [name for name in ("ffmpeg", "ffprobe") if shutil.which(name) is None]
        if missing:
            names = " and ".join(missing)
            raise FfmpegMissingError(
                f"Missing {names}. Install FFmpeg and ensure ffmpeg/ffprobe are in PATH."
            )

    def inspect(self, file_path: Path) -> MediaProbeResult:
        ffprobe = shutil.which("ffprobe")
        if ffprobe is None:
            raise FfmpegMissingError(
                "Missing ffprobe. Install FFmpeg and ensure ffmpeg/ffprobe are in PATH."
            )

        command = [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "stream=codec_type,height:format=format_name",
            "-of",
            "json",
            str(file_path),
        ]
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )
        except subprocess.TimeoutExpired as exc:
            raise MediaValidationError("ffprobe timed out while reading the output file.") from exc
        except OSError as exc:
            raise MediaValidationError(f"Could not run ffprobe: {exc}") from exc
        if completed.returncode != 0:
            detail = completed.stderr.strip() or "unknown ffprobe error"
            raise MediaValidationError(f"ffprobe could not read the output file: {detail}")

        try:
            payload: dict[str, Any] = json.loads(completed.stdout)
        except (json.JSONDecodeError, TypeError) as exc:
            raise MediaValidationError("ffprobe returned invalid JSON.") from exc

        streams = payload.get("streams") or []
        video_streams = [stream for stream in streams if stream.get("codec_type") == "video"]
        audio_streams = [stream for stream in streams if stream.get("codec_type") == "audio"]
        heights = [
            stream["height"]
            for stream in video_streams
            if isinstance(stream.get("height"), int)
        ]
        format_name = (payload.get("format") or {}).get("format_name")
        return MediaProbeResult(
            video_streams=len(video_streams),
            audio_streams=len(audio_streams),
            height=max(heights, default=None),
            format_name=str(format_name) if format_name is not None else None,
        )

    def verify(self, file_path: Path, require_audio: bool) -> MediaProbeResult:
        result = self.inspect(file_path)
        if result.video_streams == 0:
            raise MediaValidationError("Downloaded output does not contain a video stream.")
        if require_audio and result.audio_streams == 0:
            raise MediaValidationError(
                "The source has audio but the downloaded output has no audio stream."
            )
        return result


def source_has_audio(metadata: dict[str, Any]) -> bool:
    """Return whether yt-dlp metadata advertises at least one audio stream."""
    if _has_codec(metadata.get("acodec")):
        return True
    return any(
        isinstance(media_format, dict) and _has_codec(media_format.get("acodec"))
        for media_format in metadata.get("formats") or []
    )


def _has_codec(codec: Any) -> bool:
    return codec not in (None, "", "none")
