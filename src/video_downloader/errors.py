"""Application-level exceptions shown by the CLI."""


class VideoDownloaderError(Exception):
    """Base class for expected, user-facing download errors."""


class InvalidUrlError(VideoDownloaderError):
    """Raised when a URL cannot be passed safely to the downloader."""


class DownloadError(VideoDownloaderError):
    """Raised when yt-dlp cannot complete a download."""

