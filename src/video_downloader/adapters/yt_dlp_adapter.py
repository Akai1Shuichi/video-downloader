"""Thin adapter around the yt-dlp Python API."""

from pathlib import Path
from typing import Any

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError as YtDlpDownloadError

from video_downloader.errors import DownloadError


class YtDlpAdapter:
    """Download one video through ``yt_dlp.YoutubeDL``."""

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

    def download(self, url: str, output_dir: Path) -> Path:
        options: dict[str, Any] = {
            "format": "best",
            "noplaylist": True,
            "outtmpl": str(output_dir / "%(title)s [%(id)s].%(ext)s"),
        }

        try:
            with YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=True)
                if not info:
                    raise DownloadError("yt-dlp did not return information about the video.")
                file_path = self._resolve_file_path(ydl, info)
        except YtDlpDownloadError as exc:
            raise DownloadError(self._clean_error_message(exc)) from exc
        except OSError as exc:
            raise DownloadError(f"Could not write the downloaded file: {exc}") from exc

        if not file_path.is_file() or file_path.stat().st_size == 0:
            message = f"Download finished but no valid output file was found: {file_path}"
            raise DownloadError(message)
        return file_path.resolve()

    @staticmethod
    def _resolve_file_path(ydl: YoutubeDL, info: dict[str, Any]) -> Path:
        requested_downloads = info.get("requested_downloads") or []
        if requested_downloads:
            downloaded_path = requested_downloads[0].get("filepath")
            if downloaded_path:
                return Path(downloaded_path)

        filename = info.get("_filename") or ydl.prepare_filename(info)
        return Path(filename)

    @staticmethod
    def _clean_error_message(error: Exception) -> str:
        message = str(error).strip()
        return message.removeprefix("ERROR: ") or "yt-dlp could not download this URL."
