"""Download orchestration independent from the CLI."""

import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol, TypeVar

from video_downloader.adapters.yt_dlp_adapter import YtDlpAdapter
from video_downloader.errors import VideoDownloaderError, WriteError
from video_downloader.metadata import map_video_metadata
from video_downloader.models import Browser, DownloadRequest, Quality, VideoMetadata
from video_downloader.progress import ProgressCallback, ProgressEvent, ProgressStatus
from video_downloader.url_utils import normalize_url

T = TypeVar("T")


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

    def __init__(
        self,
        adapter: DownloadAdapter | None = None,
        progress_callback: ProgressCallback | None = None,
        max_attempts: int = 3,
        backoff_seconds: float = 1.0,
        sleeper: Callable[[float], None] = time.sleep,
        cookies_from_browser: Browser | None = None,
        browser_profile: str | None = None,
    ) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        self._progress_callback = progress_callback
        self._adapter = adapter or YtDlpAdapter(
            progress_callback=progress_callback,
            cookies_from_browser=cookies_from_browser,
            browser_profile=browser_profile,
        )
        self._max_attempts = max_attempts
        self._backoff_seconds = backoff_seconds
        self._sleeper = sleeper

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
            raise WriteError(message) from exc

        if not request.output_dir.is_dir():
            raise WriteError(f"Output path is not a directory: {request.output_dir}")

        result = self._with_retry(
            lambda: self._adapter.download(
                request.url,
                request.output_dir,
                request.filename_template,
                request.quality,
            )
        )
        self._emit(ProgressEvent(ProgressStatus.COMPLETED))
        return result

    def get_metadata(self, url: str) -> VideoMetadata:
        """Read and map metadata without downloading media."""
        normalized_url = normalize_url(url)
        raw_metadata = self._with_retry(lambda: self._adapter.get_metadata(normalized_url))
        return map_video_metadata(raw_metadata, normalized_url)

    def _with_retry(self, operation: Callable[[], T]) -> T:
        for attempt in range(1, self._max_attempts + 1):
            self._emit(ProgressEvent(ProgressStatus.READING_METADATA))
            try:
                return operation()
            except VideoDownloaderError as exc:
                if not exc.retryable or attempt >= self._max_attempts:
                    raise
                delay = self._backoff_seconds * (2 ** (attempt - 1))
                self._emit(
                    ProgressEvent(
                        ProgressStatus.RETRYING,
                        attempt=attempt + 1,
                        max_attempts=self._max_attempts,
                        delay_seconds=delay,
                        message=f"[{exc.code.value}] {exc}",
                    )
                )
                self._sleeper(delay)
        raise RuntimeError("retry loop exited unexpectedly")

    def _emit(self, event: ProgressEvent) -> None:
        if self._progress_callback:
            self._progress_callback(event)
