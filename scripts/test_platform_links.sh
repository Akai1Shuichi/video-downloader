#!/usr/bin/env bash
set -euo pipefail

# Có thể override bất kỳ URL/profile nào bằng biến môi trường trước khi chạy script.
export VD_SMOKE_FACEBOOK_URL="${VD_SMOKE_FACEBOOK_URL:-https://www.facebook.com/share/r/17WCorFRPB/}"
export VD_SMOKE_INSTAGRAM_URL="${VD_SMOKE_INSTAGRAM_URL:-https://www.instagram.com/reel/DcEtkSDsKw-/?utm_source=ig_web_copy_link&igsi=NTc4MTIwNjQ2YQ==}"
export VD_SMOKE_TIKTOK_URL="${VD_SMOKE_TIKTOK_URL:-https://www.tiktok.com/@quytrunggg/video/7680944552802323733?is_from_webapp=1&sender_device=pc}"
export VD_SMOKE_DOUYIN_URL="${VD_SMOKE_DOUYIN_URL:-https://www.douyin.com/video/7667904915150294278}"
export VD_SMOKE_COOKIES_FROM_BROWSER="${VD_SMOKE_COOKIES_FROM_BROWSER:-chrome}"
export VD_SMOKE_BROWSER_PROFILE="${VD_SMOKE_BROWSER_PROFILE:-Default}"

platform="${1:-all}"
if [[ $# -gt 0 ]]; then
    shift
fi

case "$platform" in
    all)
        selection="public_platform_metadata_download_and_audio"
        ;;
    facebook|instagram|tiktok|douyin)
        selection="public_platform_metadata_download_and_audio and ${platform}"
        ;;
    *)
        echo "Usage: $0 [all|facebook|instagram|tiktok|douyin] [pytest options...]" >&2
        exit 2
        ;;
esac

echo "Running Phase 7 smoke test: ${platform}"
if [[ "$platform" == "all" || "$platform" == "tiktok" || "$platform" == "douyin" ]]; then
    echo "Browser cookies: ${VD_SMOKE_COOKIES_FROM_BROWSER}:${VD_SMOKE_BROWSER_PROFILE}"
    echo "If TikTok/Douyin rejects stale cookies, open the video in that profile and retry."
fi

exec python -m pytest \
    --run-network \
    -m network \
    -k "$selection" \
    -v \
    "$@"
