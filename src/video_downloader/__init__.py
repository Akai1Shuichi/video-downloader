"""Video Downloader package."""

from __future__ import annotations

import os
from pathlib import Path

__version__ = "0.1.0"


def _ensure_binaries_in_path() -> None:
    """Add local binaries directory to PATH if present."""
    candidates = [
        Path(__file__).resolve().parents[2] / "binaries",
        Path.cwd() / "binaries",
    ]
    for candidate in candidates:
        if candidate.is_dir():
            candidate_str = str(candidate.resolve())
            path_env = os.environ.get("PATH", "")
            current_paths = [p.rstrip(r"\/") for p in path_env.split(os.pathsep) if p]
            if candidate_str.rstrip(r"\/") not in current_paths:
                os.environ["PATH"] = candidate_str + os.pathsep + path_env
            break


def _ensure_unicode_io() -> None:
    """Ensure standard output handles Unicode (e.g. CJK filenames) on Windows."""
    import sys

    if sys.platform == "win32":
        try:
            if hasattr(sys.stdout, "reconfigure"):
                sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            if hasattr(sys.stderr, "reconfigure"):
                sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


_ensure_binaries_in_path()
_ensure_unicode_io()

