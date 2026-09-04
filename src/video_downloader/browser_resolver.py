"""Browser-assisted stream resolver for platforms with complex anti-bot measures."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class BrowserResolverError(Exception):
    """Raised when browser-assisted resolution fails."""


@dataclass(frozen=True, slots=True)
class DouyinMediaInfo:
    title: str
    video_id: str
    duration_seconds: int | None
    uploader: str | None
    direct_url: str
    raw_dict: dict[str, Any]


def resolve_douyin_via_browser(
    video_url: str,
    timeout_seconds: int = 15,
) -> DouyinMediaInfo:
    """Launch a browser briefly to capture the Douyin aweme_detail response."""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options as ChromeOptions
        from selenium.webdriver.edge.options import Options as EdgeOptions
    except ImportError as exc:
        raise BrowserResolverError("Selenium is required. Run: pip install selenium") from exc

    drivers_to_try = [
        ("chrome", ChromeOptions, webdriver.Chrome),
        ("edge", EdgeOptions, webdriver.Edge),
    ]

    driver: Any = None
    last_error: Exception | None = None
    for _browser_name, options_cls, driver_cls in drivers_to_try:
        try:
            options = options_cls()
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--window-size=1000,700")
            options.page_load_strategy = "eager"
            options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
            driver = driver_cls(options=options)
            break
        except Exception as exc:
            last_error = exc
            continue

    if driver is None:
        raise BrowserResolverError(f"Could not launch browser: {last_error}")

    try:
        driver.set_page_load_timeout(timeout_seconds)
        try:
            driver.get(video_url)
        except Exception:
            pass

        # Give 5-6 seconds for video page JS to fire aweme/detail request
        start = time.time()
        detail_data: dict[str, Any] | None = None

        while time.time() - start < timeout_seconds:
            time.sleep(1)
            try:
                logs = driver.get_log("performance")
            except Exception:
                break

            for entry in logs:
                try:
                    msg = json.loads(entry["message"])["message"]
                    if msg.get("method") == "Network.responseReceived":
                        url = msg.get("params", {}).get("response", {}).get("url", "")
                        if "aweme/detail" in url or "aweme/v1/web/aweme/detail" in url:
                            req_id = msg["params"]["requestId"]
                            try:
                                res = driver.execute_cdp_cmd(
                                    "Network.getResponseBody",
                                    {"requestId": req_id},
                                )
                                body_str = res.get("body", "")
                                if body_str:
                                    parsed = json.loads(body_str)
                                    if "aweme_detail" in parsed and parsed["aweme_detail"]:
                                        detail_data = parsed["aweme_detail"]
                                        break
                            except Exception:
                                continue
                except Exception:
                    continue

            if detail_data:
                break

        if not detail_data:
            raise BrowserResolverError("Could not intercept video details from Douyin page.")

        # Save any captured cookies for future requests
        try:
            from video_downloader.cookie_fetcher import fetch_and_save_douyin_cookies  # noqa: F401
            cookies = driver.get_cookies()
            if cookies:
                cookie_path = Path.cwd() / "cookies.txt"
                lines = ["# Netscape HTTP Cookie File\n"]
                for c in cookies:
                    domain = c.get("domain", ".douyin.com")
                    if "douyin.com" in domain:
                        domain = ".douyin.com"
                    elif not domain.startswith("."):
                        domain = "." + domain
                    domain_specified = "TRUE" if domain.startswith(".") else "FALSE"
                    exp = int(c.get("expiry") or 2147483647)
                    name = c.get("name", "")
                    val = c.get("value", "")
                    if name:
                        lines.append(f"{domain}\t{domain_specified}\t/\tTRUE\t{exp}\t{name}\t{val}\n")
                cookie_path.write_text("".join(lines), encoding="utf-8")
        except Exception:
            pass

        title = detail_data.get("desc") or "douyin_video"
        video_id = str(detail_data.get("aweme_id") or "unknown")
        raw_duration = detail_data.get("duration")
        duration = int(raw_duration / 1000) if raw_duration else None
        uploader = detail_data.get("author", {}).get("nickname")

        play_addr = detail_data.get("video", {}).get("play_addr", {})
        url_list = play_addr.get("url_list", [])
        if not url_list:
            raise BrowserResolverError("No downloadable stream URLs found in video details.")

        direct_url = url_list[0]
        return DouyinMediaInfo(
            title=title,
            video_id=video_id,
            duration_seconds=duration,
            uploader=uploader,
            direct_url=direct_url,
            raw_dict=detail_data,
        )

    finally:
        try:
            driver.quit()
        except Exception:
            pass
