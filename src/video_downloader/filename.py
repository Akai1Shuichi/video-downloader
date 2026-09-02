"""Cross-platform safe filename construction."""

import re
import unicodedata

INVALID_CHARACTERS = re.compile(r'[<>:"/\\|?*\x00-\x1f\x7f]')
REPEATED_WHITESPACE = re.compile(r"\s+")
REPEATED_DOTS = re.compile(r"\.{2,}")
WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{number}" for number in range(1, 10)),
    *(f"LPT{number}" for number in range(1, 10)),
}
MAX_STEM_BYTES = 180


def sanitize_filename_component(value: str, max_bytes: int = MAX_STEM_BYTES) -> str:
    """Sanitize one filename component while preserving Unicode and emoji."""
    normalized = unicodedata.normalize("NFC", value)
    sanitized = INVALID_CHARACTERS.sub("_", normalized)
    sanitized = REPEATED_DOTS.sub(".", sanitized)
    sanitized = REPEATED_WHITESPACE.sub(" ", sanitized).strip(" .")

    if not sanitized:
        sanitized = "video"
    if sanitized.upper() in WINDOWS_RESERVED_NAMES:
        sanitized = f"_{sanitized}"

    truncated = _truncate_utf8(sanitized, max_bytes).rstrip(" .")
    return truncated or "video"


def build_safe_stem(title: str, video_id: str, custom_name: str | None = None) -> str:
    """Build a bounded filename stem that always contains the video ID."""
    safe_id = sanitize_filename_component(video_id, max_bytes=48)
    suffix = f" [{safe_id}]"
    title_budget = max(1, MAX_STEM_BYTES - len(suffix.encode("utf-8")))
    safe_title = sanitize_filename_component(custom_name or title, max_bytes=title_budget)
    return f"{safe_title}{suffix}"


def _truncate_utf8(value: str, max_bytes: int) -> str:
    encoded = value.encode("utf-8")
    if len(encoded) <= max_bytes:
        return value
    return encoded[:max_bytes].decode("utf-8", errors="ignore")

