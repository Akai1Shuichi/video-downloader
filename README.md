# Video Downloader

Python CLI tải video công khai bằng `yt-dlp` và FFmpeg. Dự án yêu cầu Python 3.10 trở lên.

> Chỉ tải nội dung công khai mà bạn sở hữu hoặc có quyền tải. Tool không vượt đăng nhập,
> DRM hay cơ chế bảo vệ của nền tảng.

## Cài đặt cho môi trường phát triển

FFmpeg và ffprobe phải có trong `PATH`.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

Kiểm tra cài đặt:

```bash
video-downloader --version
video-downloader doctor
video-downloader info "URL"
video-downloader download "URL"
ruff check .
pytest
```

Mặc định, `doctor` kiểm tra quyền ghi của thư mục `./downloads`. Có thể kiểm tra một thư
mục khác bằng `video-downloader doctor --output <thư-mục>`.

Tải một video public ở chất lượng kết hợp tốt nhất mà nguồn cung cấp:

```bash
video-downloader download "URL"
video-downloader download "URL" --output ./my-downloads
video-downloader download "URL" --filename "Tên tùy chỉnh 🎬"
video-downloader download "URL" --quality 720
video-downloader download "URL" --quiet
```

Nếu Douyin yêu cầu fresh cookies, dùng cookie trực tiếp từ profile trình duyệt đang mở
được video. Tool chỉ chuyển cookie trong bộ nhớ cho `yt-dlp`, không in hoặc lưu cookie:

```bash
video-downloader info "DOUYIN_URL" \
  --cookies-from-browser chrome --browser-profile Default
video-downloader download "DOUYIN_URL" \
  --cookies-from-browser chrome --browser-profile Default
```

Các browser hỗ trợ gồm Brave, Chrome, Chromium, Edge, Firefox, Opera, Safari, Vivaldi và
Whale. Nếu cookie database đang bị khóa, hãy đóng hẳn browser rồi chạy lại. Chỉ dùng
profile của chính bạn và không chia sẻ file cookie.

Sau khi thành công, command in ra đường dẫn tuyệt đối của file đã tải.

Tên file được làm sạch để chạy trên Windows, macOS và Linux, nhưng vẫn giữ Unicode và
emoji. Video ID luôn được thêm vào tên để hai video trùng tiêu đề không ghi đè nhau.
`--filename` chỉ đặt phần tên cơ sở; path tuyệt đối, `../` và ký tự phân cách thư mục sẽ
bị vô hiệu hóa. Nếu file hoàn chỉnh đã tồn tại, tool dùng lại file đó và không ghi đè.
File `.part` được giữ lại để yt-dlp tiếp tục tải ở lần chạy sau.

`--quality` nhận `best`, `1080`, `720` hoặc `480`; mặc định là `best`. Với một mức số,
tool chọn bản tốt nhất không vượt quá mức đó và tự fallback xuống bản thấp hơn. Khi nguồn
cung cấp các stream riêng, yt-dlp gọi FFmpeg để ghép video và audio, ưu tiên MP4/H.264/AAC.
Sau tải, ffprobe bắt buộc xác nhận có video stream và có audio stream nếu nguồn có audio.

Trong chế độ thường, CLI hiển thị trạng thái đọc metadata, phần trăm, dung lượng, tốc độ,
ETA, bước ghép FFmpeg và bước xác minh. `--quiet` ẩn các trạng thái trung gian nhưng vẫn
in đường dẫn kết quả. Lỗi mạng tạm thời và rate limit được thử tối đa 3 lần với backoff
1 rồi 2 giây; URL sai, video không tồn tại và nội dung cần đăng nhập không được retry.
`Ctrl+C` kết thúc sạch với exit code 130. Dùng `--debug` khi cần traceback để điều tra lỗi.

### Error code và exit code

| Error code | Exit code | Ý nghĩa |
| --- | ---: | --- |
| `UNKNOWN_ERROR` | 1 | Lỗi chưa phân loại |
| `INVALID_URL` | 2 | URL không hợp lệ |
| `UNSUPPORTED_SITE` | 3 | yt-dlp không hỗ trợ URL |
| `VIDEO_UNAVAILABLE` | 4 | Video đã xóa hoặc không tồn tại |
| `LOGIN_REQUIRED` | 5 | Nội dung private hoặc cần đăng nhập |
| `RATE_LIMITED` | 6 | Nền tảng giới hạn tần suất |
| `NETWORK_ERROR` | 7 | Timeout hoặc lỗi mạng tạm thời |
| `FFMPEG_MISSING` | 8 | Thiếu FFmpeg hoặc ffprobe |
| `POSTPROCESS_ERROR` | 9 | Ghép hoặc xác minh media thất bại |
| `WRITE_ERROR` | 10 | Không thể ghi output |

Đọc metadata mà không tải video:

```bash
video-downloader info "URL"
video-downloader info "URL" --json
```

Kết quả gồm video ID, tiêu đề, nền tảng, người đăng, thời lượng, thumbnail và các độ phân
giải mà nguồn cung cấp. Tool nhận diện sơ bộ Facebook, Instagram, TikTok, Douyin và dùng
`other` cho các website khác.

## Kiểm thử

`pytest` chỉ chạy bộ test offline và chủ động chặn kết nối mạng ngoài ý muốn. Smoke test
Facebook, Instagram, TikTok và Douyin là opt-in, nhận URL public qua biến môi trường để
không lưu các URL dễ hết hạn trong repo:

```bash
pytest
pytest --run-network -m network -v
```

Xem [checklist smoke test Phase 7](docs/phase-7-smoke-tests.md) để cấu hình URL, kiểm tra
`best`, `720`, fallback, short link, video đã xóa/private và ghi biên bản trước release.

Chạy nhanh bốn URL smoke test hiện tại (metadata, download, video và audio):

```bash
./scripts/test_platform_links.sh
./scripts/test_platform_links.sh tiktok
./scripts/test_platform_links.sh douyin
```

Tham số đầu tiên nhận `all`, `facebook`, `instagram`, `tiktok` hoặc `douyin`. Có thể
override URL/profile bằng các biến `VD_SMOKE_*` được mô tả trong checklist Phase 7.
