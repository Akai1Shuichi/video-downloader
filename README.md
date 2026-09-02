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
```

Sau khi thành công, command in ra đường dẫn tuyệt đối của file đã tải.

Tên file được làm sạch để chạy trên Windows, macOS và Linux, nhưng vẫn giữ Unicode và
emoji. Video ID luôn được thêm vào tên để hai video trùng tiêu đề không ghi đè nhau.
`--filename` chỉ đặt phần tên cơ sở; path tuyệt đối, `../` và ký tự phân cách thư mục sẽ
bị vô hiệu hóa. Nếu file hoàn chỉnh đã tồn tại, tool dùng lại file đó và không ghi đè.
File `.part` được giữ lại để yt-dlp tiếp tục tải ở lần chạy sau.

Đọc metadata mà không tải video:

```bash
video-downloader info "URL"
video-downloader info "URL" --json
```

Kết quả gồm video ID, tiêu đề, nền tảng, người đăng, thời lượng, thumbnail và các độ phân
giải mà nguồn cung cấp. Tool nhận diện sơ bộ Facebook, Instagram, TikTok, Douyin và dùng
`other` cho các website khác.
