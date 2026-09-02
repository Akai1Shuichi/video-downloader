"""Thin adapter around the yt-dlp Python API."""

from pathlib import Path
from typing import Any

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError as YtDlpDownloadError

from video_downloader.errors import DownloadError, MediaValidationError
from video_downloader.filename import build_safe_stem
from video_downloader.format_selector import select_format
from video_downloader.media_probe import MediaProbe, source_has_audio
from video_downloader.models import Quality


class YtDlpAdapter:
    """Download one video through ``yt_dlp.YoutubeDL``."""

    def __init__(self, media_probe: MediaProbe | None = None) -> None:
        self._media_probe = media_probe or MediaProbe()

    def get_metadata(self, url: str) -> dict[str, Any]:
        """Extract metadata without downloading media."""
        options: dict[str, Any] = {
            "noplaylist": True,
            "quiet": True,
            "skip_download": True,
        }
        try:
            with YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=False)
        except YtDlpDownloadError as exc:
            raise DownloadError(self._clean_error_message(exc)) from exc

        if not info:
            raise DownloadError("yt-dlp did not return information about the video.")
        return info

    def download(
        self,
        url: str,
        output_dir: Path,
        filename: str | None = None,
        quality: Quality = "best",
    ) -> Path:
        self._media_probe.ensure_tools()
        metadata = self.get_metadata(url)
        format_selection = select_format(quality)
        safe_stem = build_safe_stem(
            title=str(metadata.get("title") or "video"),
            video_id=str(metadata.get("id") or "unknown"),
            custom_name=filename,
            quality_label=f"{quality}p" if quality != "best" else None,
        )
        options: dict[str, Any] = {
            "continuedl": True,
            "format": format_selection.selector,
            "format_sort": format_selection.sort,
            "merge_output_format": "mp4",
            "noplaylist": True,
            "nopart": False,
            "outtmpl": str(output_dir / f"{safe_stem}.%(ext)s"),
            "overwrites": False,
        }

        try:
            with YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=True)
                if not info:
                    raise DownloadError("yt-dlp did not return information about the video.")
                file_path = self._resolve_file_path(ydl, info, output_dir, safe_stem)
        except YtDlpDownloadError as exc:
            raise DownloadError(self._clean_error_message(exc)) from exc
        except OSError as exc:
            raise DownloadError(f"Could not write the downloaded file: {exc}") from exc

        file_path = self._ensure_inside_output(file_path, output_dir)
        if not file_path.is_file() or file_path.stat().st_size == 0:
            message = f"Download finished but no valid output file was found: {file_path}"
            raise DownloadError(message)
        probe_result = self._media_probe.verify(
            file_path,
            require_audio=source_has_audio(metadata),
        )
        if (
            format_selection.maximum_height is not None
            and probe_result.height is not None
            and probe_result.height > format_selection.maximum_height
        ):
            raise MediaValidationError(
                f"Downloaded video is {probe_result.height}p, which exceeds the requested "
                f"{format_selection.maximum_height}p limit."
            )
        return file_path

    @staticmethod
    def _resolve_file_path(
        ydl: YoutubeDL,
        info: dict[str, Any],
        output_dir: Path,
        safe_stem: str,
    ) -> Path:
        final_path = info.get("filepath")
        if final_path and Path(final_path).is_file():
            return Path(final_path)

        requested_downloads = info.get("requested_downloads") or []
        if requested_downloads:
            downloaded_path = requested_downloads[0].get("filepath")
            if downloaded_path and Path(downloaded_path).is_file():
                return Path(downloaded_path)

        filename = info.get("_filename") or ydl.prepare_filename(info)
        if filename and Path(filename).is_file():
            return Path(filename)

        candidates = [
            path
            for path in output_dir.glob(f"{safe_stem}.*")
            if path.is_file() and path.suffix not in {".part", ".ytdl"}
        ]
        if candidates:
            return max(candidates, key=lambda path: path.stat().st_mtime)
        return Path(filename)

    @staticmethod
    def _clean_error_message(error: Exception) -> str:
        message = str(error).strip()
        return message.removeprefix("ERROR: ") or "yt-dlp could not download this URL."

    @staticmethod
    def _ensure_inside_output(file_path: Path, output_dir: Path) -> Path:
        resolved_file = file_path.resolve()
        resolved_output = output_dir.resolve()
        if not resolved_file.is_relative_to(resolved_output):
            raise DownloadError("yt-dlp returned a file outside the selected output directory.")
        return resolved_file
