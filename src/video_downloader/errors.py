"""Application error codes, exceptions, and yt-dlp error mapping."""

from enum import Enum


class ErrorCode(str, Enum):
    """Stable machine-readable error categories exposed by the CLI."""

    INVALID_URL = "INVALID_URL"
    UNSUPPORTED_SITE = "UNSUPPORTED_SITE"
    VIDEO_UNAVAILABLE = "VIDEO_UNAVAILABLE"
    LOGIN_REQUIRED = "LOGIN_REQUIRED"
    RATE_LIMITED = "RATE_LIMITED"
    NETWORK_ERROR = "NETWORK_ERROR"
    FFMPEG_MISSING = "FFMPEG_MISSING"
    POSTPROCESS_ERROR = "POSTPROCESS_ERROR"
    WRITE_ERROR = "WRITE_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


class VideoDownloaderError(Exception):
    """Base class for expected, user-facing errors."""

    code = ErrorCode.UNKNOWN_ERROR
    exit_code = 1
    retryable = False


class InvalidUrlError(VideoDownloaderError):
    code = ErrorCode.INVALID_URL
    exit_code = 2


class UnsupportedSiteError(VideoDownloaderError):
    code = ErrorCode.UNSUPPORTED_SITE
    exit_code = 3


class VideoUnavailableError(VideoDownloaderError):
    code = ErrorCode.VIDEO_UNAVAILABLE
    exit_code = 4


class LoginRequiredError(VideoDownloaderError):
    code = ErrorCode.LOGIN_REQUIRED
    exit_code = 5


class RateLimitedError(VideoDownloaderError):
    code = ErrorCode.RATE_LIMITED
    exit_code = 6
    retryable = True


class NetworkError(VideoDownloaderError):
    code = ErrorCode.NETWORK_ERROR
    exit_code = 7
    retryable = True


class DownloadError(VideoDownloaderError):
    """Fallback for a download failure without a narrower category."""


class FfmpegMissingError(DownloadError):
    code = ErrorCode.FFMPEG_MISSING
    exit_code = 8


class MediaValidationError(DownloadError):
    code = ErrorCode.POSTPROCESS_ERROR
    exit_code = 9


class PostprocessError(DownloadError):
    code = ErrorCode.POSTPROCESS_ERROR
    exit_code = 9


class WriteError(DownloadError):
    code = ErrorCode.WRITE_ERROR
    exit_code = 10


class UnknownError(VideoDownloaderError):
    code = ErrorCode.UNKNOWN_ERROR
    exit_code = 1


def map_external_error(error: Exception) -> VideoDownloaderError:
    """Convert an yt-dlp/system message into a stable application error."""
    message = _clean_message(error)
    lowered = message.lower()
    if "could not find" in lowered and "cookie" in lowered:
        return LoginRequiredError(
            "Could not find browser cookie database or profile. Please check your browser profile "
            "name, omit --browser-profile, try another browser (e.g. edge, firefox), or provide "
            "--cookies <file>."
        )
    if "could not copy" in lowered and "cookie database" in lowered:
        return LoginRequiredError(
            "Browser cookie database is currently locked by your open browser. "
            "Please close the browser completely and retry, or provide --cookies <file>."
        )
    if "fresh cookies" in lowered:
        return LoginRequiredError(
            "Douyin needs fresh browser cookies. Open and play the URL in the selected "
            "browser profile, close the browser completely, then retry immediately. "
            "Or run 'video-downloader fetch-cookie' to automatically capture cookies."
        )
    mappings: tuple[tuple[tuple[str, ...], type[VideoDownloaderError]], ...] = (
        (("ffmpeg not found", "ffprobe not found", "ffmpeg is not installed"), FfmpegMissingError),
        (
            ("too many requests", "rate limit", "http error 429", "status code 429"),
            RateLimitedError,
        ),
        (
            (
                "login required",
                "sign in",
                "log in",
                "private video",
                "video is private",
                "private content",
                "content is private",
                "authentication required",
                "cookies are required",
                "fresh cookies",
            ),
            LoginRequiredError,
        ),
        (("unsupported url", "no suitable extractor"), UnsupportedSiteError),
        (
            (
                "video unavailable",
                "video is unavailable",
                "not available",
                "has been removed",
                "has been deleted",
                "does not exist",
            ),
            VideoUnavailableError,
        ),
        (
            (
                "timed out",
                "timeout",
                "temporary failure",
                "connection reset",
                "connection refused",
                "network is unreachable",
                "unexpected response from webpage request",
                "unable to extract universal data for rehydration",
                "http error 403: forbidden",
                "http error 500",
                "http error 502",
                "http error 503",
                "http error 504",
            ),
            NetworkError,
        ),
        (
            (
                "permission denied",
                "no space left",
                "unable to write",
                "read-only file system",
                "disk quota exceeded",
            ),
            WriteError,
        ),
        (("postprocessing", "post-processing", "merger", "conversion failed"), PostprocessError),
    )
    for patterns, error_type in mappings:
        if any(pattern in lowered for pattern in patterns):
            return error_type(message)
    return UnknownError(message)


def _clean_message(error: Exception) -> str:
    message = str(error).strip().removeprefix("ERROR: ").strip()
    return message or "An unknown error occurred."
