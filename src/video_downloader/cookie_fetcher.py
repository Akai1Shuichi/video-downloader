"""Automated browser cookie fetching for platforms requiring interactive sessions."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any


class CookieFetcherError(Exception):
    """Raised when cookie retrieval fails."""


def fetch_and_save_douyin_cookies(
    output_path: Path | None = None,
    timeout_seconds: int = 15,
) -> Path:
    """Launch a browser window briefly to obtain fresh Douyin session cookies.

    Args:
        output_path: Target path to save the cookies (defaults to ./cookies.txt).
        timeout_seconds: Max seconds to wait for cookies to generate.

    Returns:
        Path to the saved cookie file.
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options as ChromeOptions
        from selenium.webdriver.edge.options import Options as EdgeOptions
    except ImportError as exc:
        raise CookieFetcherError(
            "Selenium is required for automatic cookie fetching. "
            "Please run: pip install selenium"
        ) from exc

    driver: Any = None
    target_path = output_path or (Path.cwd() / "cookies.txt")

    # Try Chrome first, then Edge as fallback
    drivers_to_try = [
        ("chrome", ChromeOptions, webdriver.Chrome),
        ("edge", EdgeOptions, webdriver.Edge),
    ]

    last_error: Exception | None = None
    for _browser_name, options_cls, driver_cls in drivers_to_try:
        try:
            options = options_cls()
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--window-size=960,640")
            options.page_load_strategy = "eager"
            driver = driver_cls(options=options)
            break
        except Exception as exc:
            last_error = exc
            continue

    if driver is None:
        raise CookieFetcherError(
            f"Could not launch Chrome or Edge browser: {last_error}"
        )

    try:
        driver.set_page_load_timeout(timeout_seconds)
        try:
            driver.get("https://www.douyin.com")
        except Exception:
            # Eager strategy might raise timeout if streams continue, but DOM is loaded
            pass

        start_time = time.time()
        cookies: list[dict[str, Any]] = []
        while time.time() - start_time < timeout_seconds:
            time.sleep(1)
            try:
                cookies = driver.get_cookies()
            except Exception:
                break
            names = {c["name"] for c in cookies}
            if "ttwid" in names or "s_v_web_id" in names:
                # Allow an extra second for signature completion
                time.sleep(1)
                cookies = driver.get_cookies()
                break

        if not cookies:
            raise CookieFetcherError(
                "No cookies were received from Douyin. Check your internet connection."
            )

        # Build Netscape format cookies
        lines = [
            "# Netscape HTTP Cookie File",
            "# Automatically captured by video-downloader",
        ]
        for c in cookies:
            name = c.get("name", "")
            if not name:
                continue
            val = c.get("value", "")
            domain = c.get("domain", ".douyin.com")
            if "douyin.com" in domain:
                domain = ".douyin.com"
            elif not domain.startswith("."):
                domain = "." + domain
            domain_specified = "TRUE" if domain.startswith(".") else "FALSE"
            exp = int(c.get("expiry") or 2147483647)
            path = c.get("path", "/")
            secure = "TRUE" if c.get("secure") else "FALSE"
            prefix = "#HttpOnly_" if c.get("httpOnly") else ""
            lines.append(f"{prefix}{domain}\t{domain_specified}\t{path}\t{secure}\t{exp}\t{name}\t{val}")

        target_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return target_path

    finally:
        try:
            driver.quit()
        except Exception:
            pass
