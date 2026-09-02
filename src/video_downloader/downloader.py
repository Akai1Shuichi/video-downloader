"""Download orchestration independent from the CLI."""

from pathlib import Path
from typing import Protocol
from urllib.parse import urlparse

from video_downloader.adapters.yt_dlp_adapter import YtDlpAdapter
from video_downloader.errors import DownloadError, InvalidUrlError


class DownloadAdapter(Protocol):
    """Interface required by the download service."""

    def download(self, url: str, output_dir: Path) -> Path: ...


class DownloaderService:
    """Validate a basic request and delegate it to a download adapter."""

    def __init__(self, adapter: DownloadAdapter | None = None) -> None:
        self._adapter = adapter or YtDlpAdapter()

    def download(self, url: str, output_dir: Path = Path("downloads")) -> Path:
        parsed_url = urlparse(url)
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            raise InvalidUrlError("URL must be a complete http:// or https:// address.")

        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise DownloadError(f"Could not create output directory '{output_dir}': {exc}") from exc

        if not output_dir.is_dir():
            raise DownloadError(f"Output path is not a directory: {output_dir}")

        return self._adapter.download(url, output_dir)
