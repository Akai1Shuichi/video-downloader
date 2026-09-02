# TODO — VIDEO DOWNLOADER MVP 1

Tool Python CLI tải video công khai từ Facebook, Instagram, TikTok và Douyin bằng `yt-dlp` + FFmpeg.

> Làm tuần tự từ trên xuống. Chỉ chuyển phase khi toàn bộ mục **Hoàn thành khi** của phase hiện tại đã đạt.

---

## PHASE 0 — Khởi tạo project

- [x] Tạo project Python theo `src layout`.
- [x] Tạo `pyproject.toml` và yêu cầu Python 3.10+.
- [x] Cài dependencies: `yt-dlp`, `typer`, `rich`, `pytest`, `ruff`.
- [x] Cài FFmpeg và ffprobe trên máy phát triển.
- [x] Tạo `.gitignore` cho `.venv`, cache, log, `downloads/` và file media.
- [x] Tạo các thư mục `src/video_downloader`, `tests`, `downloads`, `logs`.
- [x] Tạo command `video-downloader --version`.

**Hoàn thành khi:**

- [x] Import được package `video_downloader`.
- [x] `ruff check .` chạy thành công.
- [x] `pytest` chạy thành công.

---

## PHASE 1 — Kiểm tra môi trường

- [x] Tạo command `video-downloader doctor`.
- [x] Kiểm tra phiên bản Python.
- [x] Kiểm tra có import được `yt-dlp`.
- [x] Kiểm tra `ffmpeg` có trong PATH.
- [x] Kiểm tra `ffprobe` có trong PATH.
- [x] Kiểm tra thư mục output có quyền ghi.
- [x] Hiển thị hướng dẫn sửa khi một dependency bị thiếu.

**Hoàn thành khi:**

- [x] `doctor` trả trạng thái rõ ràng cho từng thành phần.
- [x] Trả exit code khác `0` nếu môi trường chưa sẵn sàng.

---

## PHASE 2 — Tải video cơ bản

- [x] Tạo command `video-downloader download <url>`.
- [x] Tạo `DownloaderService`.
- [x] Tạo adapter gọi `yt_dlp.YoutubeDL` từ Python.
- [x] Tải format `best` trong phiên bản đầu tiên.
- [x] Lưu file mặc định vào `./downloads`.
- [x] Cho phép truyền `--output` hoặc `-o`.
- [x] Trả đường dẫn file sau khi tải thành công.
- [x] Xử lý URL sai mà không in traceback khó hiểu.

**Hoàn thành khi:**

- [x] Tải thành công ít nhất một video public.
- [x] File đầu ra tồn tại, có dung lượng lớn hơn `0` và phát được.

---

## PHASE 3 — URL và metadata

- [x] Chỉ chấp nhận URL `http` hoặc `https`.
- [x] Chuẩn hóa URL và hostname.
- [x] Nhận diện sơ bộ Facebook, Instagram, TikTok, Douyin hoặc `other`.
- [x] Tạo model `DownloadRequest`.
- [x] Tạo model `VideoMetadata`.
- [x] Tạo model `DownloadResult`.
- [x] Map dữ liệu thô của `yt-dlp` sang các model nội bộ.
- [x] Tạo command `video-downloader info <url>`.
- [x] Hiển thị title, platform, uploader, duration và video ID.
- [x] Thêm option `--json`.

**Hoàn thành khi:**

- [x] `info` đọc được metadata mà không tải video.
- [x] Có unit test cho URL hợp lệ, URL sai và short link.

---

## PHASE 4 — Tên file và output an toàn

- [ ] Làm sạch ký tự không hợp lệ trong tên file.
- [ ] Giới hạn độ dài tên file.
- [ ] Giữ video ID trong tên để tránh trùng.
- [ ] Hỗ trợ chữ tiếng Việt và emoji.
- [ ] Ngăn `../`, path traversal và đường dẫn tuyệt đối trong filename.
- [ ] Tự tạo output directory nếu chưa tồn tại.
- [ ] Xác định chính sách khi file đã tồn tại.
- [ ] Giữ file `.part` để có thể resume tải.

**Hoàn thành khi:**

- [ ] Title có ký tự đặc biệt không làm tool crash.
- [ ] Không thể ghi file ra ngoài output directory.
- [ ] Hai video cùng title không ghi đè lên nhau.

---

## PHASE 5 — Chọn chất lượng và FFmpeg

- [ ] Thêm `--quality best`.
- [ ] Thêm `--quality 1080`.
- [ ] Thêm `--quality 720`.
- [ ] Thêm `--quality 480`.
- [ ] Chọn format tốt nhất không vượt quá độ phân giải yêu cầu.
- [ ] Thêm fallback nếu nguồn không có đúng độ phân giải.
- [ ] Ưu tiên MP4/H.264/AAC khi nguồn cung cấp.
- [ ] Ghép video và audio bằng FFmpeg khi chúng là hai stream riêng.
- [ ] Dùng ffprobe kiểm tra output có video stream.
- [ ] Kiểm tra output có audio stream nếu nguồn có audio.

**Hoàn thành khi:**

- [ ] `--quality 720` không tải video cao hơn 720p.
- [ ] File ghép phát được cả hình và tiếng.
- [ ] Thiếu FFmpeg có thông báo lỗi riêng.

---

## PHASE 6 — Progress, retry và error handling

- [ ] Tạo progress hook cho `yt-dlp`.
- [ ] Hiển thị trạng thái đọc metadata.
- [ ] Hiển thị phần trăm, dung lượng, tốc độ và ETA khi tải.
- [ ] Hiển thị trạng thái ghép media.
- [ ] Hiển thị kết quả hoàn thành.
- [ ] Thêm `--quiet`.
- [ ] Retry hữu hạn cho timeout và lỗi mạng tạm thời.
- [ ] Thêm backoff giữa các lần retry.
- [ ] Không retry URL sai, video private hoặc login required.
- [ ] Xử lý `Ctrl+C` sạch sẽ.
- [ ] Không hiển thị traceback trừ khi bật debug.

### Error code cần có

- [ ] `INVALID_URL`
- [ ] `UNSUPPORTED_SITE`
- [ ] `VIDEO_UNAVAILABLE`
- [ ] `LOGIN_REQUIRED`
- [ ] `RATE_LIMITED`
- [ ] `NETWORK_ERROR`
- [ ] `FFMPEG_MISSING`
- [ ] `POSTPROCESS_ERROR`
- [ ] `WRITE_ERROR`
- [ ] `UNKNOWN_ERROR`

**Hoàn thành khi:**

- [ ] Mỗi nhóm lỗi có thông báo và exit code phù hợp.
- [ ] Retry không tạo vòng lặp vô hạn.
- [ ] CLI không treo im lặng khi đang xử lý.

---

## PHASE 7 — Kiểm thử bốn nền tảng

### Unit test offline

- [ ] Test URL validator.
- [ ] Test platform detector.
- [ ] Test filename sanitizer.
- [ ] Test format selector.
- [ ] Test metadata mapper.
- [ ] Test error mapper.
- [ ] Mock `yt-dlp`; unit test không gọi Internet.

### Smoke test thủ công

- [ ] Facebook public video: metadata + download + audio.
- [ ] Instagram public Reel: metadata + download + audio.
- [ ] TikTok public video: metadata + download + audio.
- [ ] Douyin public video: metadata + download + audio.
- [ ] Thử short link nếu nền tảng có short link.
- [ ] Thử `best`, `720` và fallback.
- [ ] Thử URL sai.
- [ ] Thử video đã xóa hoặc không public.
- [ ] Đánh dấu integration test dùng mạng để không chạy mặc định trong CI.

**Hoàn thành khi:**

- [ ] Cả bốn nền tảng có ít nhất một URL public hoạt động tại thời điểm release.
- [ ] Unit test chạy được khi không có Internet.

---

## PHASE 8 — Đóng gói MVP 1

- [ ] Tạo entry point `video-downloader`.
- [ ] Viết README hướng dẫn cài Python và FFmpeg.
- [ ] Viết ví dụ cho `doctor`, `info` và `download`.
- [ ] Ghim khoảng phiên bản dependency phù hợp.
- [ ] Tạo lock file theo package manager đã chọn.
- [ ] Thêm CI chạy Ruff và pytest.
- [ ] Test trên Linux.
- [ ] Test trên Windows.
- [ ] Cài thử trong một virtual environment sạch.
- [ ] Chạy lại toàn bộ smoke test trước release.
- [ ] Gắn version `0.1.0` cho MVP 1.

**Hoàn thành khi:**

- [ ] Người khác làm theo README và tải được một video public.
- [ ] `doctor`, `info`, `download` hoạt động trong môi trường sạch.
- [ ] Toàn bộ acceptance checklist bên dưới đã được tick.

---

## ACCEPTANCE CHECKLIST MVP 1

- [ ] Tool hoạt động bằng Python CLI.
- [ ] Hỗ trợ Facebook public video.
- [ ] Hỗ trợ Instagram public Reel.
- [ ] Hỗ trợ TikTok public video.
- [ ] Hỗ trợ Douyin public video.
- [ ] Xem metadata trước khi tải.
- [ ] Chọn được `best`, `1080`, `720`, `480`.
- [ ] Có fallback khi thiếu độ phân giải yêu cầu.
- [ ] File đầu ra phát được.
- [ ] Có audio khi nguồn có audio.
- [ ] Tên file và output path an toàn.
- [ ] Có progress, retry hữu hạn và xử lý `Ctrl+C`.
- [ ] Có thông báo riêng cho các lỗi chính.
- [ ] Không log cookie, token hoặc Authorization header.
- [ ] Unit test chạy offline.
- [ ] README đủ để cài và sử dụng.

---

## VIỆC LÀM NGAY — SPRINT ĐẦU TIÊN

Chưa làm web, API hoặc queue. Chỉ hoàn thành năm việc sau:

- [x] Khởi tạo `pyproject.toml` và cấu trúc `src/`.
- [x] Cài `yt-dlp`, Typer, Rich, pytest, Ruff và FFmpeg.
- [x] Viết command `doctor`.
- [x] Viết `download <url>` cho happy path.
- [x] Tải thử một video public và kiểm tra file bằng ffprobe.

---

## SAU MVP 1 — CHƯA LÀM

- [ ] MVP 2: FastAPI và job API local.
- [ ] MVP 3: Web UI, preview metadata và progress realtime.
- [ ] MVP 4: Redis, worker queue, object storage và deploy.
- [ ] MVP 5: Plugin/adapters riêng và tải playlist có giới hạn.

---

## DEFINITION OF DONE CHO MỖI TASK

Một task chỉ được tick khi:

- [ ] Code đã chạy đúng happy path.
- [ ] Lỗi chính đã được xử lý.
- [ ] Có test phù hợp hoặc checklist kiểm tra thủ công.
- [ ] `ruff check .` không báo lỗi.
- [ ] `pytest` chạy thành công.
- [ ] Không commit video, log, token hoặc dữ liệu nhạy cảm.
- [ ] Thay đổi quan trọng đã được ghi vào README.
