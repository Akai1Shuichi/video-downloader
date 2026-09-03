"""URL validation, normalization, and preliminary platform detection."""

import re
from urllib.parse import SplitResult, urlsplit, urlunsplit

from video_downloader.errors import InvalidUrlError
from video_downloader.models import Platform

PLATFORM_DOMAINS: tuple[tuple[Platform, tuple[str, ...]], ...] = (
    ("facebook", ("facebook.com", "fb.watch")),
    ("instagram", ("instagram.com",)),
    ("tiktok", ("tiktok.com",)),
    ("douyin", ("douyin.com", "iesdouyin.com")),
)

_DOUYIN_VIDEO_PATH = re.compile(r"^/video/(?P<video_id>\d+)/?$")
_MAX_UNSIGNED_64_BIT_ID = (1 << 64) - 1


def normalize_url(value: str) -> str:
    """Return a canonical HTTP(S) URL or raise a user-facing error."""
    raw_url = value.strip()
    try:
        parsed = urlsplit(raw_url)
        port = parsed.port
    except ValueError as exc:
        raise InvalidUrlError(f"Invalid URL: {exc}") from exc

    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https"}:
        raise InvalidUrlError("URL must start with http:// or https://.")
    if parsed.username is not None or parsed.password is not None:
        raise InvalidUrlError("URL must not contain embedded credentials.")
    if not parsed.hostname:
        raise InvalidUrlError("URL must include a valid hostname.")

    try:
        hostname = parsed.hostname.rstrip(".").encode("idna").decode("ascii").lower()
    except UnicodeError as exc:
        raise InvalidUrlError("URL contains an invalid hostname.") from exc
    if not hostname or any(character.isspace() for character in hostname):
        raise InvalidUrlError("URL must include a valid hostname.")

    display_hostname = f"[{hostname}]" if ":" in hostname else hostname
    is_default_port = (scheme == "http" and port == 80) or (scheme == "https" and port == 443)
    netloc = display_hostname if port is None or is_default_port else f"{display_hostname}:{port}"
    normalized = SplitResult(scheme, netloc, parsed.path or "/", parsed.query, "")
    _validate_platform_url(normalized)
    return urlunsplit(normalized)


def _validate_platform_url(parsed: SplitResult) -> None:
    """Reject structurally impossible platform URLs before extractor errors obscure them."""
    hostname = parsed.hostname or ""
    if hostname != "douyin.com" and not hostname.endswith(".douyin.com"):
        return

    match = _DOUYIN_VIDEO_PATH.fullmatch(parsed.path)
    if match and int(match.group("video_id")) > _MAX_UNSIGNED_64_BIT_ID:
        raise InvalidUrlError(
            "Invalid Douyin video ID. Check the copied URL; the video ID is too large."
        )


def detect_platform(url: str) -> Platform:
    """Classify known platform domains without making a network request."""
    hostname = urlsplit(normalize_url(url)).hostname or ""
    for platform, domains in PLATFORM_DOMAINS:
        if any(hostname == domain or hostname.endswith(f".{domain}") for domain in domains):
            return platform
    return "other"
