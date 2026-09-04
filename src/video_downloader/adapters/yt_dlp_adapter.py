"""Thin adapter around the yt-dlp Python API."""

from pathlib import Path
from typing import Any

from yt_dlp import YoutubeDL
from yt_dlp.networking.impersonate import ImpersonateTarget
from yt_dlp.utils import YoutubeDLError

from video_downloader.cookies import ensure_netscape_cookie_file, get_default_cookie_file
from video_downloader.errors import MediaValidationError, WriteError, map_external_error
from video_downloader.filename import build_safe_stem
from video_downloader.format_selector import select_format
from video_downloader.media_probe import MediaProbe, source_has_audio
from video_downloader.models import Browser, Quality
from video_downloader.progress import (
    ProgressCallback,
    ProgressEvent,
    ProgressStatus,
    event_from_yt_dlp,
)
from video_downloader.url_utils import detect_platform

CHROME_IMPERSONATION = ImpersonateTarget("chrome")


class _SilentLogger:
    def debug(self, _message: str) -> None:
        pass

    def info(self, _message: str) -> None:
        pass

    def warning(self, _message: str) -> None:
        pass

    def error(self, _message: str) -> None:
        pass


class YtDlpAdapter:
    """Download one video through ``yt_dlp.YoutubeDL``."""

    def __init__(
        self,
        media_probe: MediaProbe | None = None,
        progress_callback: ProgressCallback | None = None,
        cookies_from_browser: Browser | None = None,
        browser_profile: str | None = None,
        cookies_file: Path | None = None,
    ) -> None:
        self._media_probe = media_probe or MediaProbe()
        self._progress_callback = progress_callback
        self._browser_cookies = (
            (cookies_from_browser, browser_profile, None, None)
            if cookies_from_browser
            else None
        )
        cookie_path = cookies_file or (
            get_default_cookie_file() if not cookies_from_browser else None
        )
        self._cookies_file = ensure_netscape_cookie_file(cookie_path) if cookie_path else None

    def get_metadata(self, url: str) -> dict[str, Any]:
        """Extract metadata without downloading media."""
        options: dict[str, Any] = {
            "extractor_retries": 0,
            "logger": _SilentLogger(),
            "no_warnings": True,
            "noplaylist": True,
            "quiet": True,
            "socket_timeout": 20,
            "skip_download": True,
        }
        if detect_platform(url) in {"tiktok", "douyin"}:
            options["impersonate"] = CHROME_IMPERSONATION
        if self._cookies_file:
            options["cookiefile"] = self._cookies_file
        elif self._browser_cookies:
            options["cookiesfrombrowser"] = self._browser_cookies
        try:
            with YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=False)
        except YoutubeDLError as exc:
            mapped_error = map_external_error(exc)
            if detect_platform(url) == "douyin":
                try:
                    return self._get_douyin_metadata_via_browser(url)
                except Exception:
                    raise mapped_error from exc
            raise mapped_error from exc

        if not info:
            raise map_external_error(RuntimeError("yt-dlp returned no video information."))
        return info

    def download(
        self,
        url: str,
        output_dir: Path,
        filename: str | None = None,
        quality: Quality = "best",
    ) -> Path:
        self._media_probe.ensure_tools()
        format_selection = select_format(quality)
        options: dict[str, Any] = {
            "continuedl": True,
            "extractor_retries": 0,
            "file_access_retries": 0,
            "format": format_selection.selector,
            "format_sort": format_selection.sort,
            "fragment_retries": 0,
            "logger": _SilentLogger(),
            "merge_output_format": "mp4",
            "no_progress": True,
            "no_warnings": True,
            "noplaylist": True,
            "nopart": False,
            "overwrites": False,
            "retries": 0,
            "socket_timeout": 20,
        }
        if detect_platform(url) in {"tiktok", "douyin"}:
            options["impersonate"] = CHROME_IMPERSONATION
        if self._cookies_file:
            options["cookiefile"] = self._cookies_file
        elif self._browser_cookies:
            options["cookiesfrombrowser"] = self._browser_cookies
        if self._progress_callback:
            options["progress_hooks"] = [self._on_progress]
            options["postprocessor_hooks"] = [self._on_postprocessor]

        try:
            with YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    raise map_external_error(
                        RuntimeError("yt-dlp returned no video information.")
                    )
                safe_stem = build_safe_stem(
                    title=str(info.get("title") or "video"),
                    video_id=str(info.get("id") or "unknown"),
                    custom_name=filename,
                    quality_label=f"{quality}p" if quality != "best" else None,
                )
                ydl.params["outtmpl"] = {
                    "default": str(output_dir / f"{safe_stem}.%(ext)s")
                }
                ydl.process_info(info)
                file_path = self._resolve_file_path(ydl, info, output_dir, safe_stem)
        except YoutubeDLError as exc:
            mapped_error = map_external_error(exc)
            if detect_platform(url) == "douyin":
                try:
                    return self._download_douyin_via_browser(
                        url, output_dir, filename, quality
                    )
                except Exception:
                    raise mapped_error from exc
            raise mapped_error from exc
        except OSError as exc:
            raise WriteError(f"Could not write the downloaded file: {exc}") from exc

        file_path = self._ensure_inside_output(file_path, output_dir)
        if not file_path.is_file() or file_path.stat().st_size == 0:
            message = f"Download finished but no valid output file was found: {file_path}"
            raise WriteError(message)
        self._emit(ProgressEvent(ProgressStatus.VERIFYING))
        probe_result = self._media_probe.verify(
            file_path,
            require_audio=source_has_audio(info),
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
    def _ensure_inside_output(file_path: Path, output_dir: Path) -> Path:
        resolved_file = file_path.resolve()
        resolved_output = output_dir.resolve()
        if not resolved_file.is_relative_to(resolved_output):
            raise WriteError("yt-dlp returned a file outside the selected output directory.")
        return resolved_file

    def _on_progress(self, data: dict[str, object]) -> None:
        event = event_from_yt_dlp(data)
        if event:
            self._emit(event)

    def _on_postprocessor(self, data: dict[str, object]) -> None:
        if data.get("status") == "started" and data.get("postprocessor") == "Merger":
            self._emit(ProgressEvent(ProgressStatus.MERGING))

    def _emit(self, event: ProgressEvent) -> None:
        if self._progress_callback:
            self._progress_callback(event)

    def _get_douyin_metadata_via_browser(self, url: str) -> dict[str, Any]:
        from video_downloader.browser_resolver import resolve_douyin_via_browser

        media_info = resolve_douyin_via_browser(url)
        return {
            "id": media_info.video_id,
            "title": media_info.title,
            "platform": "douyin",
            "uploader": media_info.uploader or "unknown",
            "duration": media_info.duration_seconds,
            "formats": [{"format_id": "direct", "ext": "mp4", "height": 1080}],
            "webpage_url": url,
        }

    def _download_douyin_via_browser(
        self,
        url: str,
        output_dir: Path,
        filename: str | None = None,
        quality: Quality = "best",
    ) -> Path:
        from curl_cffi import requests

        from video_downloader.browser_resolver import resolve_douyin_via_browser

        media_info = resolve_douyin_via_browser(url)
        safe_stem = build_safe_stem(
            title=media_info.title,
            video_id=media_info.video_id,
            custom_name=filename,
            quality_label=f"{quality}p" if quality != "best" else None,
        )
        file_path = output_dir / f"{safe_stem}.mp4"
        self._emit(ProgressEvent(ProgressStatus.DOWNLOADING))
        headers = {"Referer": "https://www.douyin.com/"}
        response = requests.get(media_info.direct_url, headers=headers, impersonate="chrome")
        file_path.write_bytes(response.content)

        file_path = self._ensure_inside_output(file_path, output_dir)
        if not file_path.is_file() or file_path.stat().st_size == 0:
            message = f"Download finished but no valid output file was found: {file_path}"
            raise WriteError(message)

        self._emit(ProgressEvent(ProgressStatus.VERIFYING))
        self._media_probe.verify(file_path, require_audio=True)
        return file_path
