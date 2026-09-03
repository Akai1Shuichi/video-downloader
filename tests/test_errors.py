import pytest

from video_downloader.errors import (
    ErrorCode,
    InvalidUrlError,
    map_external_error,
)


@pytest.mark.parametrize(
    ("message", "expected_code", "expected_exit", "retryable"),
    [
        ("Unsupported URL: example", ErrorCode.UNSUPPORTED_SITE, 3, False),
        ("This video is unavailable", ErrorCode.VIDEO_UNAVAILABLE, 4, False),
        ("Private video: login required", ErrorCode.LOGIN_REQUIRED, 5, False),
        (
            "Fresh cookies (not necessarily logged in) are needed",
            ErrorCode.LOGIN_REQUIRED,
            5,
            False,
        ),
        ("HTTP Error 429: Too Many Requests", ErrorCode.RATE_LIMITED, 6, True),
        ("Connection reset by peer", ErrorCode.NETWORK_ERROR, 7, True),
        (
            "Unable to extract universal data for rehydration",
            ErrorCode.NETWORK_ERROR,
            7,
            True,
        ),
        ("HTTP Error 403: Forbidden", ErrorCode.NETWORK_ERROR, 7, True),
        ("ffmpeg not found", ErrorCode.FFMPEG_MISSING, 8, False),
        ("Postprocessing: conversion failed", ErrorCode.POSTPROCESS_ERROR, 9, False),
        ("Permission denied while writing", ErrorCode.WRITE_ERROR, 10, False),
        ("Something completely unexpected", ErrorCode.UNKNOWN_ERROR, 1, False),
    ],
)
def test_external_error_mapping(message, expected_code, expected_exit, retryable) -> None:
    error = map_external_error(RuntimeError(message))

    assert error.code is expected_code
    assert error.exit_code == expected_exit
    assert error.retryable is retryable


def test_all_required_error_codes_exist() -> None:
    assert {code.value for code in ErrorCode} == {
        "INVALID_URL",
        "UNSUPPORTED_SITE",
        "VIDEO_UNAVAILABLE",
        "LOGIN_REQUIRED",
        "RATE_LIMITED",
        "NETWORK_ERROR",
        "FFMPEG_MISSING",
        "POSTPROCESS_ERROR",
        "WRITE_ERROR",
        "UNKNOWN_ERROR",
    }
    assert InvalidUrlError("bad URL").exit_code == 2


def test_fresh_cookie_error_has_actionable_message() -> None:
    error = map_external_error(RuntimeError("Fresh cookies are needed"))

    assert error.code is ErrorCode.LOGIN_REQUIRED
    assert "Open and play the URL" in str(error)
    assert "retry immediately" in str(error)
