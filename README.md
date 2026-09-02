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
ruff check .
pytest
```

Các command `doctor`, `info` và `download` sẽ được bổ sung trong những phase tiếp theo.

