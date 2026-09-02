# VIDEO DOWNLOADER — ROADMAP MVP 1 (PYTHON CLI)

> Tài liệu triển khai tuần tự từ nền tảng đến phiên bản MVP 1 có thể sử dụng được.
>
> Phạm vi sử dụng: chỉ tải nội dung công khai hoặc nội dung mà người dùng sở hữu/có quyền tải. Không vượt DRM, không vượt đăng nhập, không khai thác nội dung riêng tư và không né cơ chế bảo vệ của nền tảng.

---

## 1. Mục tiêu MVP 1

Xây dựng một tool Python chạy trên máy cá nhân, nhận URL video và tải video từ:

- Facebook
- Instagram
- TikTok
- Douyin
- Các website khác mà `yt-dlp` hỗ trợ có thể hoạt động như tính năng thử nghiệm, nhưng chưa cam kết trong MVP 1.

Luồng sử dụng cơ bản:

```text
Người dùng nhập URL
        ↓
Kiểm tra và chuẩn hóa URL
        ↓
Nhận diện nền tảng
        ↓
Đọc metadata video
        ↓
Chọn định dạng/chất lượng
        ↓
Tải video và audio
        ↓
FFmpeg ghép hoặc chuyển container nếu cần
        ↓
Lưu file + trả kết quả
```

### Kết quả người dùng cần nhận được

- Một file video phát được, ưu tiên MP4.
- Tên file an toàn, không chứa ký tự lỗi trên Windows/macOS/Linux.
- Thông báo tiến trình tải.
- Thông báo lỗi dễ hiểu nếu URL không hợp lệ, video không tồn tại hoặc nền tảng từ chối truy cập.
- Metadata cơ bản: tiêu đề, nền tảng, người đăng, thời lượng, thumbnail và URL gốc.

---

## 2. Phạm vi và giới hạn

### Có trong MVP 1

- Python CLI chạy local.
- Tải một video công khai từ một URL tại một thời điểm.
- Tự nhận diện Facebook, Instagram, TikTok và Douyin.
- Xem metadata trước khi tải.
- Chọn chất lượng: `best`, `1080`, `720`, `480`.
- Chọn thư mục đầu ra.
- Hiển thị phần trăm, tốc độ tải và thời gian còn lại khi nguồn cung cấp đủ dữ liệu.
- Ghép video/audio bằng FFmpeg khi chúng được cung cấp thành hai luồng riêng.
- Ghi log kỹ thuật để debug, nhưng không làm lộ cookie hoặc dữ liệu nhạy cảm.
- Có unit test và một bộ smoke test URL thủ công.

### Chưa có trong MVP 1

- Giao diện web, desktop hoặc mobile.
- API public.
- Tải playlist, album hoặc toàn bộ profile.
- Tải đồng thời nhiều video.
- Hàng đợi, Redis, worker hoặc cloud storage.
- Đăng nhập tự động, vượt CAPTCHA, vượt DRM hoặc tải nội dung riêng tư.
- Cam kết video không watermark. Tool lưu nội dung mà nguồn hợp lệ cung cấp.
- Re-encode video nặng; MVP chỉ ghép/remux khi có thể.

---

## 3. Công nghệ đề xuất

| Thành phần | Lựa chọn | Vai trò |
| --- | --- | --- |
| Ngôn ngữ | Python 3.10+ | Lõi ứng dụng |
| Extractor/downloader | `yt-dlp` | Đọc metadata, chọn format và tải media |
| Media processing | FFmpeg + ffprobe | Ghép audio/video, kiểm tra file đầu ra |
| CLI | Typer | Command và tham số dễ mở rộng |
| Hiển thị | Rich | Progress bar, bảng metadata, thông báo lỗi |
| Cấu hình | `pyproject.toml` + biến môi trường | Quản lý package và cấu hình runtime |
| Kiểm thử | pytest | Unit test và integration test |
| Lint/format | Ruff | Format và kiểm tra lỗi tĩnh |

### Nguyên tắc kiến trúc

1. Không tự viết scraper cho từng nền tảng trong MVP 1.
2. Bọc `yt-dlp` sau một lớp `DownloaderService` để sau này có thể thay hoặc bổ sung extractor.
3. Logic CLI không gọi thẳng `yt-dlp`; CLI chỉ tạo request và gọi service.
4. Phân biệt rõ lỗi của người dùng, lỗi mạng, lỗi nền tảng và lỗi hệ thống.
5. Không coi tên miền là bằng chứng duy nhất; kết quả extractor trả về mới là nguồn xác nhận chính.

---

## 4. Kiến trúc MVP 1

```text
CLI
 ├─ download <url>
 ├─ info <url>
 └─ doctor
       ↓
URL Validator + Platform Detector
       ↓
Downloader Service
       ↓
yt-dlp Adapter
       ↓
FFmpeg / ffprobe
       ↓
Local File Storage + Logs
```

### Trách nhiệm của từng phần

| Module | Trách nhiệm |
| --- | --- |
| `cli.py` | Nhận command, option và hiển thị kết quả |
| `models.py` | Các model request, metadata và result |
| `url_utils.py` | Kiểm tra scheme, hostname, chuẩn hóa URL và nhận diện nền tảng sơ bộ |
| `downloader.py` | Điều phối metadata, chọn format, tải file và trả kết quả chuẩn hóa |
| `yt_dlp_adapter.py` | Chuyển request nội bộ thành option của `yt-dlp` |
| `format_selector.py` | Tạo quy tắc format theo chất lượng người dùng chọn |
| `progress.py` | Chuyển progress hook thành event cho CLI |
| `errors.py` | Error code và exception riêng của ứng dụng |
| `media_probe.py` | Dùng ffprobe xác minh file video đầu ra |
| `filename.py` | Làm sạch và giới hạn độ dài tên file |
| `config.py` | Thư mục output, timeout, retry và log level |

### Cấu trúc thư mục đề xuất

```text
video-downloader/
├── pyproject.toml
├── README.md
├── .gitignore
├── src/
│   └── video_downloader/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py
│       ├── config.py
│       ├── models.py
│       ├── errors.py
│       ├── downloader.py
│       ├── format_selector.py
│       ├── progress.py
│       ├── media_probe.py
│       ├── filename.py
│       ├── url_utils.py
│       └── adapters/
│           ├── __init__.py
│           └── yt_dlp_adapter.py
├── tests/
│   ├── unit/
│   │   ├── test_url_utils.py
│   │   ├── test_filename.py
│   │   └── test_format_selector.py
│   └── integration/
│       └── test_public_samples.py
├── downloads/
└── logs/
```

`downloads/` và `logs/` phải được đưa vào `.gitignore`.

---

## 5. Giao diện CLI dự kiến

### Kiểm tra môi trường

```bash
video-downloader doctor
```

Kết quả cần kiểm tra:

- Phiên bản Python.
- Có import được `yt-dlp` không.
- Có tìm thấy `ffmpeg` và `ffprobe` trong PATH không.
- Thư mục output có quyền ghi không.

### Xem thông tin video

```bash
video-downloader info "https://www.tiktok.com/..."
```

Kết quả:

```text
Platform : TikTok
Title    : Example title
Uploader : Example account
Duration : 00:01:24
Formats  : best, 1080p, 720p, 480p
```

### Tải video

```bash
video-downloader download "https://www.instagram.com/reel/..."
```

### Chọn chất lượng và thư mục

```bash
video-downloader download "URL" --quality 1080 --output ./downloads
```

### Option tối thiểu

| Option | Giá trị | Mặc định |
| --- | --- | --- |
| `--quality` | `best`, `1080`, `720`, `480` | `best` |
| `--output`, `-o` | Đường dẫn thư mục | `./downloads` |
| `--filename` | Template tên file | `%(title)s [%(id)s].%(ext)s` |
| `--quiet` | Ẩn progress | `false` |
| `--json` | Trả kết quả dạng JSON | `false` |

---

## 6. Data model nền tảng

Các model nên độc lập với dictionary thô của `yt-dlp`.

### `DownloadRequest`

```text
url: str
quality: best | 1080 | 720 | 480
output_dir: Path
filename_template: str | None
```

### `VideoMetadata`

```text
id: str
source_url: str
platform: str
title: str
uploader: str | None
duration_seconds: int | None
thumbnail_url: str | None
available_heights: list[int]
```

### `DownloadResult`

```text
success: bool
file_path: Path | None
metadata: VideoMetadata | None
bytes_written: int | None
error_code: str | None
message: str
```

---

## 7. Quy tắc chọn format

Mục tiêu là lấy chất lượng tốt nhất không vượt quá giới hạn đã chọn và ưu tiên file phát tương thích rộng.

| Lựa chọn | Quy tắc |
| --- | --- |
| `best` | Video tốt nhất + audio tốt nhất, fallback sang format kết hợp tốt nhất |
| `1080` | Chất lượng tốt nhất có chiều cao `<= 1080` |
| `720` | Chất lượng tốt nhất có chiều cao `<= 720` |
| `480` | Chất lượng tốt nhất có chiều cao `<= 480` |

Ưu tiên output MP4, nhưng không được re-encode chỉ để ép MP4 nếu làm chậm đáng kể hoặc giảm chất lượng. Nếu video/audio tách rời, FFmpeg ghép thành một file. Luôn có fallback khi nền tảng không cung cấp đúng độ phân giải yêu cầu.

---

## 8. Error model

Không hiển thị toàn bộ traceback cho người dùng thông thường. Log kỹ thuật có thể lưu traceback khi bật debug.

| Error code | Ý nghĩa | Thông báo gợi ý |
| --- | --- | --- |
| `INVALID_URL` | URL sai hoặc scheme không hỗ trợ | URL không hợp lệ. Hãy dùng URL HTTPS đầy đủ. |
| `UNSUPPORTED_SITE` | Extractor không hỗ trợ nguồn | Nền tảng hoặc loại URL này chưa được hỗ trợ. |
| `VIDEO_UNAVAILABLE` | Video bị xóa, giới hạn vùng hoặc không công khai | Video không khả dụng hoặc không phải nội dung công khai. |
| `LOGIN_REQUIRED` | Nguồn yêu cầu phiên đăng nhập | Video yêu cầu đăng nhập; MVP 1 không xử lý nội dung này. |
| `RATE_LIMITED` | Nguồn giới hạn truy cập | Nền tảng đang giới hạn yêu cầu. Hãy thử lại sau. |
| `NETWORK_ERROR` | Timeout, DNS hoặc mất kết nối | Không thể kết nối tới nguồn video. |
| `FFMPEG_MISSING` | Không tìm thấy FFmpeg | Cần cài FFmpeg và thêm vào PATH. |
| `POSTPROCESS_ERROR` | Ghép/remux thất bại | Tải xong luồng media nhưng xử lý file thất bại. |
| `WRITE_ERROR` | Không ghi được file | Không thể ghi vào thư mục đầu ra. |
| `UNKNOWN_ERROR` | Lỗi chưa phân loại | Có lỗi không xác định; xem log debug. |

Quy ước exit code:

- `0`: thành công.
- `2`: input không hợp lệ.
- `3`: video/nền tảng không khả dụng.
- `4`: lỗi mạng hoặc rate limit.
- `5`: lỗi FFmpeg hoặc hệ thống file.
- `1`: lỗi chưa phân loại.

---

## 9. Lộ trình triển khai tuần tự

Chỉ chuyển sang bước tiếp theo khi tiêu chí hoàn thành của bước hiện tại đã đạt.

### Bước 0 — Khởi tạo nền tảng

Mức độ: dễ

Việc cần làm:

- [ ] Tạo project theo `src layout`.
- [ ] Khai báo Python 3.10+ trong `pyproject.toml`.
- [ ] Cài `yt-dlp`, Typer, Rich, pytest và Ruff.
- [ ] Cài FFmpeg trên máy phát triển.
- [ ] Tạo command `doctor`.
- [ ] Cấu hình `.gitignore` cho video, log, cache và môi trường ảo.

Tiêu chí hoàn thành:

- `python -m video_downloader doctor` chạy được.
- Tool phát hiện đúng trạng thái Python, `yt-dlp`, FFmpeg và ffprobe.
- `pytest` và `ruff check .` chạy không lỗi.

### Bước 1 — Tải được một video công khai

Mức độ: dễ

Việc cần làm:

- [ ] Tạo command `download <url>`.
- [ ] Gọi `yt_dlp.YoutubeDL` từ Python, không parse output text của subprocess.
- [ ] Đặt output mặc định là `./downloads`.
- [ ] Tải `best` và cho phép `yt-dlp` dùng FFmpeg khi cần.
- [ ] Trả exit code khác 0 khi thất bại.

Tiêu chí hoàn thành:

- Tải thành công ít nhất một URL public đang hoạt động.
- File đầu ra tồn tại, có dung lượng lớn hơn 0 và phát được.
- URL sai không làm chương trình crash bằng traceback khó hiểu.

### Bước 2 — Chuẩn hóa URL và metadata

Mức độ: dễ → trung bình

Việc cần làm:

- [ ] Chỉ chấp nhận `http`/`https`; ưu tiên yêu cầu URL HTTPS đầy đủ.
- [ ] Chuẩn hóa hostname, loại fragment không cần thiết và giữ query cần cho video ID.
- [ ] Nhận diện sơ bộ `facebook`, `instagram`, `tiktok`, `douyin` hoặc `other`.
- [ ] Tạo `VideoMetadata` và mapper từ kết quả `yt-dlp`.
- [ ] Tạo command `info <url>` với chế độ không tải video.
- [ ] Thêm output `--json` để dễ tích hợp về sau.

Tiêu chí hoàn thành:

- `info` hiển thị ít nhất platform, title, uploader, duration và ID.
- Unit test bao phủ URL hợp lệ, URL sai, short link và hostname viết hoa.
- Không dùng regex để đoán toàn bộ cấu trúc URL của mọi nền tảng.

### Bước 3 — Tên file và quản lý output

Mức độ: trung bình

Việc cần làm:

- [ ] Làm sạch ký tự không hợp lệ trong tên file.
- [ ] Giới hạn độ dài tên, vẫn giữ video ID để tránh trùng.
- [ ] Ngăn tên file thoát khỏi thư mục output bằng `../` hoặc đường dẫn tuyệt đối.
- [ ] Tạo thư mục output nếu chưa có.
- [ ] Không ghi đè âm thầm; reuse file hoàn tất hoặc tạo tên an toàn theo chính sách đã chọn.
- [ ] Dọn file `.part` do lần tải lỗi nếu người dùng yêu cầu; mặc định giữ để resume.

Tiêu chí hoàn thành:

- Tên có emoji, dấu tiếng Việt và ký tự đặc biệt không làm tool crash.
- Hai video cùng title vẫn có file khác nhau nhờ ID.
- Không thể ghi file ra ngoài thư mục output thông qua tham số filename.

### Bước 4 — Chất lượng và FFmpeg

Mức độ: trung bình

Việc cần làm:

- [ ] Cài đặt lựa chọn `best`, `1080`, `720`, `480`.
- [ ] Có fallback nếu không có đúng chiều cao.
- [ ] Ưu tiên MP4/H.264/AAC khi nguồn cung cấp, nhưng không bắt buộc re-encode.
- [ ] Ghép audio/video bằng FFmpeg nếu cần.
- [ ] Dùng ffprobe xác minh file có video stream và duration hợp lệ.
- [ ] Phân loại rõ `FFMPEG_MISSING` và `POSTPROCESS_ERROR`.

Tiêu chí hoàn thành:

- `--quality 720` không chọn stream cao hơn 720p.
- File kết quả có video stream; nếu nguồn có audio thì output cũng có audio stream.
- Nếu FFmpeg thiếu, `doctor` và command tải trả hướng dẫn rõ ràng.

### Bước 5 — Progress, retry và lỗi thân thiện

Mức độ: trung bình → khó

Việc cần làm:

- [ ] Chuyển progress hook của downloader thành event nội bộ.
- [ ] Hiển thị trạng thái: reading metadata, downloading, merging, completed.
- [ ] Hiển thị phần trăm, tốc độ, dung lượng và ETA khi có dữ liệu.
- [ ] Retry hữu hạn cho timeout/lỗi mạng tạm thời.
- [ ] Không retry lỗi input, video private hoặc login required.
- [ ] Map lỗi kỹ thuật sang error model ở mục 8.
- [ ] Có `--quiet` cho script/CI.

Tiêu chí hoàn thành:

- CLI không treo im lặng trong một lượt tải bình thường.
- Retry có giới hạn và có backoff; không tạo vòng lặp vô hạn.
- `Ctrl+C` dừng sạch và không hiển thị traceback không cần thiết.

### Bước 6 — Kiểm thử bốn nền tảng mục tiêu

Mức độ: khó

Việc cần làm:

- [ ] Unit test URL, filename, format selector và error mapping.
- [ ] Mock `yt-dlp` trong unit test; unit test không phụ thuộc Internet.
- [ ] Tạo smoke-test checklist cho Facebook, Instagram, TikTok và Douyin.
- [ ] Với mỗi nền tảng, thử URL video thường và short link nếu có.
- [ ] Lưu fixture metadata đã ẩn dữ liệu nhạy cảm để test mapper.
- [ ] Đánh dấu integration test dùng mạng để không chạy mặc định trong CI.

Ma trận smoke test:

| Nền tảng | Metadata | Best | 720p/fallback | Audio | Tên file | Kết quả |
| --- | --- | --- | --- | --- | --- | --- |
| Facebook public video | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Instagram Reel public | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| TikTok public video | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Douyin public video | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |

Lưu ý: test URL public có thể bị xóa hoặc thay đổi. Danh sách test sống nên đặt ngoài source code và thay được mà không sửa logic ứng dụng.

### Bước 7 — Đóng gói MVP 1

Mức độ: trung bình

Việc cần làm:

- [ ] Tạo entry point `video-downloader` trong `pyproject.toml`.
- [ ] Viết README: cài Python, cài FFmpeg, cài package, ví dụ command.
- [ ] Thêm `--version`.
- [ ] Ghim khoảng phiên bản dependency hợp lý và tạo lock file theo package manager đã chọn.
- [ ] Thêm CI: Ruff + pytest trên ít nhất Linux và Windows.
- [ ] Chạy acceptance checklist cuối cùng.

Tiêu chí hoàn thành:

- Cài được project trong môi trường ảo sạch.
- Chạy được `video-downloader doctor`, `info` và `download`.
- Người khác có thể làm theo README để tải một video public mà không cần đọc source code.

---

## 10. Thứ tự commit gợi ý

Mỗi commit chỉ nên giải quyết một mục chính:

1. `chore: initialize python project`
2. `feat: add environment doctor command`
3. `feat: download one public video`
4. `feat: add URL validation and metadata command`
5. `feat: add safe output naming`
6. `feat: add quality selection and ffmpeg verification`
7. `feat: show download progress`
8. `feat: map downloader errors to user messages`
9. `test: add unit and platform smoke tests`
10. `docs: add installation and usage guide`

---

## 11. Acceptance checklist MVP 1

MVP 1 chỉ được xem là hoàn tất khi toàn bộ mục bắt buộc dưới đây đạt:

- [ ] Tool chạy bằng một command CLI rõ ràng.
- [ ] `doctor` phát hiện được thiếu FFmpeg.
- [ ] `info URL` đọc metadata mà không tải video.
- [ ] `download URL` tải được một video public hợp lệ.
- [ ] Có test thực tế cho Facebook, Instagram, TikTok và Douyin tại thời điểm release.
- [ ] Chọn được `best`, `1080`, `720`, `480` và có fallback.
- [ ] File video đầu ra phát được, có audio khi nguồn có audio.
- [ ] Tên file an toàn và không thoát khỏi output directory.
- [ ] Có progress và xử lý `Ctrl+C`.
- [ ] Lỗi URL, mạng, login required, rate limit, FFmpeg và ghi file có thông báo riêng.
- [ ] Không ghi cookie, header xác thực hoặc token vào log.
- [ ] Unit test chạy offline; network test được đánh dấu riêng.
- [ ] README đủ để cài và chạy trên máy sạch.

---

## 12. Rủi ro và cách xử lý

| Rủi ro | Ảnh hưởng | Cách xử lý trong MVP 1 |
| --- | --- | --- |
| Nền tảng đổi API/trang web | Extractor ngừng hoạt động | Cập nhật `yt-dlp`, giữ adapter mỏng, không vá scraper vội |
| Video yêu cầu đăng nhập | Không tải được | Báo `LOGIN_REQUIRED`; không tự động vượt đăng nhập |
| Short link redirect lỗi | Không nhận diện đúng | Cho extractor xử lý redirect; platform detector chỉ mang tính sơ bộ |
| Rate limit/CAPTCHA | Tải thất bại tạm thời | Retry hữu hạn với backoff, sau đó báo thử lại sau |
| Video/audio tách rời | File thiếu audio | Kiểm tra FFmpeg trước và xác minh output bằng ffprobe |
| Tên video quá dài/ký tự lạ | Không lưu được file | Sanitize, cắt độ dài và giữ video ID |
| URL public dùng trong test bị xóa | Test mạng thất bại giả | Tách smoke test khỏi unit test và cho phép thay fixture URL |
| Dependency lỗi thời | Hỗ trợ nền tảng giảm | Có lịch kiểm tra/cập nhật dependency và chạy lại smoke test |

---

## 13. Bảo mật và quyền sử dụng

- Chỉ chấp nhận URL có scheme `http` hoặc `https`; với phiên bản public sau này nên bắt buộc HTTPS.
- Không cho template tên file tạo đường dẫn tuyệt đối hoặc chứa path traversal.
- Không chạy shell command ghép chuỗi từ URL hoặc title của người dùng.
- Khi gọi FFmpeg trực tiếp, truyền argument dạng list và không bật `shell=True`.
- Không log cookie, Authorization header, query token hoặc nội dung xác thực.
- Không tải hoặc hướng dẫn vượt DRM, paywall, CAPTCHA, nội dung riêng tư hay quyền truy cập trái phép.
- Người dùng chịu trách nhiệm bảo đảm họ có quyền tải và sử dụng nội dung.

Nếu sau này bọc tool thành web/API, phải bổ sung chống SSRF, giới hạn dung lượng/thời lượng, timeout toàn job, quota, sandbox worker, kiểm tra MIME và cơ chế dọn file.

---

## 14. Nâng cấp sau MVP 1

Chỉ bắt đầu sau khi acceptance checklist MVP 1 đạt đầy đủ.

### MVP 2 — Local API

- FastAPI với endpoint tạo job, xem trạng thái và tải file.
- Job ID, trạng thái và lưu metadata.
- Giới hạn URL, dung lượng, thời lượng và timeout.
- Chưa cần queue phân tán; có thể dùng worker local đơn giản.

### MVP 3 — Web UI

- Form dán URL.
- Preview metadata/thumbnail.
- Chọn chất lượng.
- Progress realtime bằng polling hoặc Server-Sent Events.
- Lịch sử tải local.

### MVP 4 — Queue và production

- Redis + worker queue.
- Nhiều job đồng thời có giới hạn.
- Object storage, signed download URL và tự động xóa file hết hạn.
- Auth, quota, rate limit, observability và deploy container.

### MVP 5 — Adapter nâng cao

- Theo dõi tỷ lệ thành công theo extractor/nền tảng.
- Adapter riêng chỉ khi có nhu cầu thực tế mà `yt-dlp` không đáp ứng.
- Playlist/profile download theo giới hạn rõ ràng.
- Plugin architecture cho extractor bổ sung.

---

## 15. Kế hoạch thực hiện gợi ý trong 7 ngày

| Ngày | Mục tiêu | Đầu ra |
| --- | --- | --- |
| 1 | Bước 0 | Project, dependencies, `doctor` |
| 2 | Bước 1 | Tải được một video public |
| 3 | Bước 2–3 | Metadata, URL, tên file, output |
| 4 | Bước 4 | Quality selector, FFmpeg, ffprobe |
| 5 | Bước 5 | Progress, retry, error mapping |
| 6 | Bước 6 | Unit test và smoke test bốn nền tảng |
| 7 | Bước 7 | Packaging, README, CI, acceptance test |

---

## 16. Điểm bắt đầu nên làm ngay

Sprint đầu tiên chỉ gồm năm task:

1. Khởi tạo `pyproject.toml` và cấu trúc `src/`.
2. Viết `doctor` để kiểm tra Python, `yt-dlp`, FFmpeg và ffprobe.
3. Viết `download URL` cho happy path bằng `yt_dlp.YoutubeDL`.
4. Tải thử một video public và xác minh bằng ffprobe.
5. Commit kết quả trước khi thêm metadata, quality hoặc progress.

Không mở rộng sang API/web cho đến khi năm task này chạy ổn định.

---

## 17. Tài liệu kỹ thuật tham khảo

- [yt-dlp — repository và hướng dẫn embedding Python](https://github.com/yt-dlp/yt-dlp)
- [FFmpeg — tài liệu chính thức](https://ffmpeg.org/documentation.html)
- [FFmpeg — trang tải và hướng dẫn package](https://ffmpeg.org/download.html)

> `yt-dlp` và extractor của các nền tảng thay đổi thường xuyên. Trước mỗi bản release, cập nhật dependency trong môi trường test và chạy lại toàn bộ smoke test thay vì giả định một URL từng hoạt động sẽ luôn hoạt động.
