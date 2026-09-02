"""Environment checks used by the ``doctor`` command."""

from __future__ import annotations

import importlib
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

MINIMUM_PYTHON = (3, 10)


@dataclass(frozen=True, slots=True)
class EnvironmentCheck:
    """Result of one environment check."""

    component: str
    passed: bool
    detail: str
    remedy: str = ""


def check_python(version_info: tuple[int, int, int] | None = None) -> EnvironmentCheck:
    """Check whether the running Python satisfies the supported version."""
    current = version_info or sys.version_info[:3]
    version = ".".join(str(part) for part in current)
    passed = current[:2] >= MINIMUM_PYTHON
    remedy = "Install Python 3.10 or newer and recreate the virtual environment."
    return EnvironmentCheck("Python", passed, version, "" if passed else remedy)


def check_yt_dlp() -> EnvironmentCheck:
    """Import yt-dlp and report its installed version."""
    try:
        version_module = importlib.import_module("yt_dlp.version")
    except (ImportError, ModuleNotFoundError) as exc:
        return EnvironmentCheck(
            "yt-dlp",
            False,
            f"cannot import ({exc})",
            "Run: python -m pip install -e '.[dev]'",
        )

    version = getattr(version_module, "__version__", "version unknown")
    return EnvironmentCheck("yt-dlp", True, str(version))


def check_executable(name: str) -> EnvironmentCheck:
    """Check whether an executable can be resolved from PATH."""
    executable = shutil.which(name)
    if executable:
        return EnvironmentCheck(name, True, executable)

    return EnvironmentCheck(
        name,
        False,
        "not found in PATH",
        f"Install {name} and add its executable directory to PATH.",
    )


def check_output_directory(output_dir: Path) -> EnvironmentCheck:
    """Verify that the output directory exists and accepts a temporary file."""
    resolved = output_dir.expanduser().resolve()
    remedy = f"Create the directory and grant write permission: {resolved}"

    if not resolved.exists():
        return EnvironmentCheck("Output directory", False, f"does not exist: {resolved}", remedy)
    if not resolved.is_dir():
        return EnvironmentCheck("Output directory", False, f"not a directory: {resolved}", remedy)

    try:
        with tempfile.TemporaryFile(dir=resolved):
            pass
    except OSError as exc:
        return EnvironmentCheck("Output directory", False, f"not writable ({exc})", remedy)

    return EnvironmentCheck("Output directory", True, f"writable: {resolved}")


def run_environment_checks(output_dir: Path) -> list[EnvironmentCheck]:
    """Run every prerequisite check in display order."""
    return [
        check_python(),
        check_yt_dlp(),
        check_executable("ffmpeg"),
        check_executable("ffprobe"),
        check_output_directory(output_dir),
    ]

