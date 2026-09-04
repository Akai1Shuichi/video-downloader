import json
from unittest.mock import MagicMock, patch

import pytest

from video_downloader.browser_resolver import (
    BrowserResolverError,
    DouyinMediaInfo,
    resolve_douyin_via_browser,
)


def test_resolve_douyin_via_browser_success() -> None:
    fake_driver = MagicMock()
    mock_detail = {
        "desc": "Test video title",
        "aweme_id": "7667904915150294278",
        "duration": 12000,
        "author": {"nickname": "TestCreator"},
        "video": {
            "play_addr": {
                "url_list": ["https://example.com/video.mp4"]
            }
        },
    }
    performance_log = [
        {
            "message": json.dumps({
                "message": {
                    "method": "Network.responseReceived",
                    "params": {
                        "requestId": "req-1",
                        "response": {
                            "url": "https://www.douyin.com/aweme/v1/web/aweme/detail/?aweme_id=7667904915150294278"
                        },
                    },
                }
            })
        }
    ]

    fake_driver.get_log.return_value = performance_log
    fake_driver.execute_cdp_cmd.return_value = {
        "body": json.dumps({"aweme_detail": mock_detail})
    }
    fake_driver.get_cookies.return_value = []

    with patch("selenium.webdriver.Chrome", return_value=fake_driver):
        info = resolve_douyin_via_browser(
            "https://www.douyin.com/video/7667904915150294278",
            timeout_seconds=2,
        )
        assert isinstance(info, DouyinMediaInfo)
        assert info.title == "Test video title"
        assert info.video_id == "7667904915150294278"
        assert info.duration_seconds == 12
        assert info.uploader == "TestCreator"
        assert info.direct_url == "https://example.com/video.mp4"


def test_resolve_douyin_via_browser_no_browser() -> None:
    with (
        patch("selenium.webdriver.Chrome", side_effect=RuntimeError("Chrome missing")),
        patch("selenium.webdriver.Edge", side_effect=RuntimeError("Edge missing")),
    ):
        with pytest.raises(BrowserResolverError, match="Could not launch browser"):
            resolve_douyin_via_browser("https://www.douyin.com/video/123", timeout_seconds=1)
