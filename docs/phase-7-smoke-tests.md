# Phase 7 — Smoke test bốn nền tảng

Bộ unit test mặc định luôn chạy offline. Fixture chung chặn kết nối socket ngoài ý muốn;
các bài test có mạng được đánh dấu `network`, bị skip mặc định và chỉ chạy khi truyền
`--run-network`.

## Chuẩn bị URL release

Chỉ dùng video công khai mà bạn sở hữu hoặc có quyền tải. Không commit URL mẫu vào repo.
Trước mỗi release, khai báo URL còn hoạt động trong shell:

```bash
export VD_SMOKE_FACEBOOK_URL='https://www.facebook.com/...'
export VD_SMOKE_INSTAGRAM_URL='https://www.instagram.com/reel/...'
export VD_SMOKE_TIKTOK_URL='https://www.tiktok.com/@.../video/...'
export VD_SMOKE_DOUYIN_URL='https://www.douyin.com/video/...'
export VD_SMOKE_COOKIES_FROM_BROWSER='chrome'
export VD_SMOKE_BROWSER_PROFILE='Default'

# Một URL dùng thử best và 720p.
export VD_SMOKE_QUALITY_URL="$VD_SMOKE_TIKTOK_URL"

# Video có độ phân giải cao nhất thấp hơn 720p để xác minh fallback.
export VD_SMOKE_FALLBACK_URL='https://...'

# URL video đã xóa hoặc chuyển private để xác minh phân loại lỗi.
export VD_SMOKE_UNAVAILABLE_URL='https://...'
```

Integration test dùng browser cookies cho TikTok và Douyin; Facebook/Instagram vẫn chạy
không cookie.

Có thể dùng short link cho một hay nhiều biến nền tảng để đồng thời kiểm tra redirect.

## Chạy

```bash
# Không truy cập Internet; phù hợp CI mặc định.
pytest

# Chỉ bộ smoke test dùng mạng. Test thiếu biến môi trường sẽ được skip rõ ràng.
pytest --run-network -m network -v
```

Mỗi test nền tảng đọc metadata, tải file `best`, rồi dùng ffprobe xác nhận có cả video và
audio. Bộ test chất lượng tải `best`, `720`, kiểm tra giới hạn chiều cao và một nguồn cần
fallback. URL sai đã được kiểm tra offline; `VD_SMOKE_UNAVAILABLE_URL` kiểm tra video đã
xóa/private.

## Biên bản trước release

Ghi ngày chạy và URL (hoặc mã tham chiếu nội bộ) để xác nhận mẫu vẫn public tại thời điểm
release.

| Ngày | Nền tảng / tình huống | Metadata | Download | Video | Audio | Kết quả |
| --- | --- | --- | --- | --- | --- | --- |
| YYYY-MM-DD | Facebook | ☐ | ☐ | ☐ | ☐ | ☐ |
| YYYY-MM-DD | Instagram Reel | ☐ | ☐ | ☐ | ☐ | ☐ |
| YYYY-MM-DD | TikTok | ☐ | ☐ | ☐ | ☐ | ☐ |
| YYYY-MM-DD | Douyin | ☐ | ☐ | ☐ | ☐ | ☐ |
| YYYY-MM-DD | Short link | ☐ | ☐ | ☐ | ☐ | ☐ |
| YYYY-MM-DD | `best` / `720` / fallback | — | ☐ | ☐ | ☐ | ☐ |
| YYYY-MM-DD | URL sai | — | — | — | — | ☐ |
| YYYY-MM-DD | Video đã xóa/private | — | — | — | — | ☐ |

### Kết quả ngày 2026-09-03

| Nền tảng / tình huống | Metadata | Download | Video | Audio | Kết quả |
| --- | --- | --- | --- | --- | --- |
| Facebook short link | ✓ | ✓ | ✓ | ✓ | PASS |
| Instagram Reel | ✓ | ✓ | ✓ | ✓ | PASS |
| TikTok `/video/` | ✓ | ✓ | ✓ | ✓ | PASS sau khi bật Chrome impersonation |
| Douyin original URL + Chrome cookies | ✓ | ✓ | ✓ | ✓ | PASS, output HEVC 720p + AAC |
| Douyin signed CDN streams | — | ✓ | ✓ | ✓ | Ghép H.264 1080p + AAC thành công |
| `best` | ✓ | ✓ | ✓ | ✓ | PASS trên Facebook và Instagram |
| `720` trên mẫu Facebook | ✓ | ✗ | ✓ | ✓ | Output 1280p bị hậu kiểm chặn đúng |
| Fallback dưới 720p | — | — | — | — | Chưa có mẫu nguồn phù hợp |
| URL sai | — | — | — | — | PASS, `INVALID_URL`, exit code 2 |

Không lưu URL đầy đủ trong biên bản. Các URL do người chạy cung cấp chỉ được truyền qua
biến môi trường. Mẫu TikTok `/photo/` ban đầu không được tính là video; mẫu `/video/` thay
thế đã tải thành công ở 1080×1920, có video HEVC và audio MP3. Original URL Douyin đã tải
thành công bằng cookie từ Chrome profile `Default`; output 1280×720 có video HEVC và audio
AAC. Còn cần một nguồn có độ phân giải tối đa dưới 720p để hoàn tất kiểm thử fallback.

Hai signed CDN URL Douyin do người chạy lấy từ DevTools đã được kiểm tra khi còn hiệu lực:
video H.264 1920×1080 và audio AAC đều dài khoảng 436,7 giây, ghép bằng stream copy thành
công. Không lưu signed URL vào repo vì token có thời hạn; smoke chính thức dùng original
URL cùng `--cookies-from-browser chrome --browser-profile Default`.
