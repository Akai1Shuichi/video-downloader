"""Cookie management and format normalization."""

from __future__ import annotations

import tempfile
from pathlib import Path


def get_default_cookie_file() -> Path | None:
    """Look for an existing cookie file in working directory or project root."""
    candidates = [
        Path.cwd() / "cookies.txt",
        Path.cwd() / "cookie.txt",
        Path(__file__).resolve().parents[2] / "cookies.txt",
        Path(__file__).resolve().parents[2] / "cookie.txt",
    ]
    for candidate in candidates:
        if candidate.is_file() and candidate.stat().st_size > 0:
            return candidate
    return None


def convert_raw_to_netscape(content: str, default_domain: str = ".douyin.com") -> str:
    """Convert a raw cookie string (e.g. from browser F12) to Netscape format."""
    lines = [
        "# Netscape HTTP Cookie File",
        "# Converted by video-downloader",
    ]
    # Split by semicolon or newline
    normalized = content.replace("\r\n", "\n").replace("\r", "\n")
    tokens: list[str] = []
    for line in normalized.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        tokens.extend(part.strip() for part in line.split(";") if part.strip())

    for token in tokens:
        if "=" not in token:
            continue
        key, _, val = token.partition("=")
        key = key.strip()
        val = val.strip()
        if key:
            lines.append(f"{default_domain}\tTRUE\t/\tTRUE\t2147483647\t{key}\t{val}")

    return "\n".join(lines) + "\n"


def ensure_netscape_cookie_file(cookie_path: Path) -> str:
    """Return a path to a Netscape-compliant cookie file.

    If the provided file already is Netscape format, returns its string path.
    Otherwise converts the raw cookie string to a temporary Netscape file.
    """
    try:
        content = cookie_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return str(cookie_path.resolve())

    if "# Netscape HTTP Cookie File" in content or "\t" in content:
        return str(cookie_path.resolve())

    # Raw string format (e.g. key1=value1; key2=value2)
    converted = convert_raw_to_netscape(content)
    tmp = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        delete=False,
        prefix="vd_cookies_",
        suffix=".txt",
    )
    with tmp:
        tmp.write(converted)
    return tmp.name
