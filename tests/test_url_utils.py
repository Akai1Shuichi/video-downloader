import pytest

from video_downloader.errors import InvalidUrlError
from video_downloader.url_utils import detect_platform, normalize_url


def test_normalize_url_canonicalizes_scheme_hostname_and_fragment() -> None:
    result = normalize_url("  HTTPS://WWW.TIKTOK.COM:443/@User/video/123?lang=vi#comments  ")

    assert result == "https://www.tiktok.com/@User/video/123?lang=vi"


@pytest.mark.parametrize(
    "url",
    [
        "",
        "www.instagram.com/reel/abc",
        "ftp://facebook.com/video/123",
        "https:///missing-host",
        "https://user:secret@tiktok.com/video/123",
    ],
)
def test_normalize_url_rejects_invalid_input(url: str) -> None:
    with pytest.raises(InvalidUrlError):
        normalize_url(url)


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://www.facebook.com/watch/?v=1", "facebook"),
        ("https://fb.watch/abc/", "facebook"),
        ("https://www.instagram.com/reel/abc/", "instagram"),
        ("https://vm.tiktok.com/abc/", "tiktok"),
        ("https://v.douyin.com/abc/", "douyin"),
        ("https://example.com/video", "other"),
        ("https://facebook.com.evil.example/video", "other"),
    ],
)
def test_detect_platform_including_short_links(url: str, expected: str) -> None:
    assert detect_platform(url) == expected

