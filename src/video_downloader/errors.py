"""Application-level exceptions shown by the CLI."""


class VideoDownloaderError(Exception):
    """Base class for expected, user-facing download errors."""


class InvalidUrlError(VideoDownloaderError):
    """Raised when a URL cannot be passed safely to the downloader."""


class DownloadError(VideoDownloaderError):
    """Raised when yt-dlp cannot complete a download."""


class FfmpegMissingError(DownloadError):
    """Raised when FFmpeg tools required for download are unavailable."""


class MediaValidationError(DownloadError):
    """Raised when ffprobe cannot validate the downloaded media."""
