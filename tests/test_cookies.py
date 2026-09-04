from pathlib import Path

from video_downloader.cookies import (
    convert_raw_to_netscape,
    ensure_netscape_cookie_file,
)


def test_convert_raw_to_netscape() -> None:
    raw = "s_v_web_id=verify_123; ttwid=test_ttwid"
    converted = convert_raw_to_netscape(raw)
    assert "# Netscape HTTP Cookie File" in converted
    assert "s_v_web_id\tverify_123" in converted
    assert "ttwid\ttest_ttwid" in converted
    assert ".douyin.com" in converted


def test_ensure_netscape_preserves_netscape_file(tmp_path: Path) -> None:
    netscape_content = "# Netscape HTTP Cookie File\n.douyin.com\tTRUE\t/\tTRUE\t0\tkey\tval\n"
    cookie_file = tmp_path / "cookies.txt"
    cookie_file.write_text(netscape_content, encoding="utf-8")

    result = ensure_netscape_cookie_file(cookie_file)
    assert result == str(cookie_file.resolve())


def test_ensure_netscape_converts_raw_file(tmp_path: Path) -> None:
    raw_content = "s_v_web_id=abc1234; odin_tt=xyz5678"
    cookie_file = tmp_path / "raw_cookies.txt"
    cookie_file.write_text(raw_content, encoding="utf-8")

    result = ensure_netscape_cookie_file(cookie_file)
    result_path = Path(result)
    assert result_path.is_file()
    text = result_path.read_text(encoding="utf-8")
    assert "# Netscape HTTP Cookie File" in text
    assert "s_v_web_id\tabc1234" in text
    result_path.unlink()
