from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from video_downloader.cookie_fetcher import (
    CookieFetcherError,
    fetch_and_save_douyin_cookies,
)


def test_fetch_and_save_douyin_cookies_success(tmp_path: Path) -> None:
    fake_driver = MagicMock()
    fake_driver.get_cookies.return_value = [
        {
            "name": "ttwid",
            "value": "test_ttwid_123",
            "domain": ".douyin.com",
            "expiry": 2000000000,
        },
        {
            "name": "s_v_web_id",
            "value": "verify_123",
            "domain": ".douyin.com",
            "expiry": 2000000000,
        },
    ]

    target = tmp_path / "test_cookies.txt"

    with patch("selenium.webdriver.Chrome", return_value=fake_driver):
        result = fetch_and_save_douyin_cookies(output_path=target, timeout_seconds=2)
        assert result == target
        assert target.is_file()
        content = target.read_text(encoding="utf-8")
        assert "# Netscape HTTP Cookie File" in content
        assert "ttwid" in content
        assert "s_v_web_id" in content


def test_fetch_and_save_douyin_cookies_no_driver() -> None:
    with (
        patch("selenium.webdriver.Chrome", side_effect=RuntimeError("Chrome missing")),
        patch("selenium.webdriver.Edge", side_effect=RuntimeError("Edge missing")),
    ):
        with pytest.raises(CookieFetcherError, match="Could not launch"):
            fetch_and_save_douyin_cookies(timeout_seconds=1)
