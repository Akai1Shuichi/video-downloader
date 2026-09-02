"""Download orchestration independent from the CLI."""

from pathlib import Path
from typing import Any, Protocol

from video_downloader.adapters.yt_dlp_adapter import YtDlpAdapter
from video_downloader.errors import DownloadError
from video_downloader.metadata import map_video_metadata
from video_downloader.models import DownloadRequest, Quality, VideoMetadata
from video_downloader.url_utils import normalize_url


class DownloadAdapter(Protocol):
    """Interface required by the download service."""

    def download(
        self,
        url: str,
        output_dir: Path,
        filename: str | None = None,
        quality: Quality = "best",
    ) -> Path: ...

    def get_metadata(self, url: str) -> dict[str, Any]: ...


class DownloaderService:
    """Validate a basic request and delegate it to a download adapter."""

    def __init__(self, adapter: DownloadAdapter | None = None) -> None:
        self._adapter = adapter or YtDlpAdapter()

    def download(
        self,
        url: str,
        output_dir: Path = Path("downloads"),
        filename: str | None = None,
        quality: Quality = "best",
    ) -> Path:
        request = DownloadRequest(
            url=normalize_url(url),
            quality=quality,
            output_dir=output_dir,
            filename_template=filename,
        )

        try:
            request.output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            message = f"Could not create output directory '{request.output_dir}': {exc}"
            raise DownloadError(message) from exc

        if not request.output_dir.is_dir():
            raise DownloadError(f"Output path is not a directory: {request.output_dir}")

        return self._adapter.download(
            request.url,
            request.output_dir,
            request.filename_template,
            request.quality,
        )

    def get_metadata(self, url: str) -> VideoMetadata:
        """Read and map metadata without downloading media."""
        normalized_url = normalize_url(url)
        raw_metadata = self._adapter.get_metadata(normalized_url)
        return map_video_metadata(raw_metadata, normalized_url)
