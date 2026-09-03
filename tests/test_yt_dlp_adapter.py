from pathlib import Path

import pytest
from yt_dlp.utils import DownloadError as YtDlpDownloadError

from video_downloader.adapters.yt_dlp_adapter import YtDlpAdapter
from video_downloader.errors import DownloadError, FfmpegMissingError, VideoUnavailableError
from video_downloader.media_probe import MediaProbeResult
from video_downloader.progress import ProgressStatus


class FakeMediaProbe:
    def __init__(self, height: int = 720) -> None:
        self.verified: list[tuple[Path, bool]] = []
        self.height = height

    def ensure_tools(self) -> None:
        pass

    def verify(self, file_path: Path, require_audio: bool) -> MediaProbeResult:
        self.verified.append((file_path, require_audio))
        return MediaProbeResult(1, int(require_audio), self.height, "mp4")


def test_adapter_uses_best_format_and_returns_downloaded_path(
    monkeypatch, tmp_path: Path
) -> None:
    downloaded_file = tmp_path / "example.mp4"
    downloaded_file.write_bytes(b"video")
    captured_options = []

    class FakeYoutubeDL:
        def __init__(self, options) -> None:
            captured_options.append(options)
            self.params = options

        def __enter__(self):
            return self

        def __exit__(self, *_args) -> None:
            return None

        def extract_info(self, url: str, *, download: bool):
            assert url == "https://example.com/video"
            assert download is False
            return {
                "id": "abc",
                "title": "Example",
                "formats": [{"acodec": "aac"}],
            }

        def process_info(self, info) -> None:
            info["filepath"] = str(downloaded_file)

    monkeypatch.setattr("video_downloader.adapters.yt_dlp_adapter.YoutubeDL", FakeYoutubeDL)

    media_probe = FakeMediaProbe()
    result = YtDlpAdapter(media_probe=media_probe).download(
        "https://example.com/video", tmp_path, quality="720"
    )

    download_options = captured_options[0]
    assert download_options["format"] == (
        "bv*[height<=720]+ba/b[height<=720]/"
        "bv*[height<=?720]+ba/b[height<=?720]"
    )
    assert download_options["format_sort"][2:] == [
        "vcodec:h264",
        "acodec:aac",
        "ext:mp4:m4a",
    ]
    assert download_options["merge_output_format"] == "mp4"
    assert download_options["noplaylist"] is True
    assert download_options["outtmpl"]["default"].startswith(str(tmp_path))
    assert download_options["overwrites"] is False
    assert download_options["continuedl"] is True
    assert download_options["nopart"] is False
    assert download_options["retries"] == 0
    assert download_options["fragment_retries"] == 0
    assert download_options["extractor_retries"] == 0
    assert "[720p] [abc]" in download_options["outtmpl"]["default"]
    assert result == downloaded_file.resolve()
    assert media_probe.verified == [(downloaded_file.resolve(), True)]


def test_adapter_converts_yt_dlp_error(monkeypatch, tmp_path: Path) -> None:
    class FailingYoutubeDL:
        def __init__(self, _options) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args) -> None:
            return None

        def extract_info(self, _url: str, *, download: bool):
            raise YtDlpDownloadError("ERROR: video unavailable")

    monkeypatch.setattr("video_downloader.adapters.yt_dlp_adapter.YoutubeDL", FailingYoutubeDL)

    with pytest.raises(VideoUnavailableError, match="video unavailable"):
        YtDlpAdapter().download("https://example.com/video", tmp_path)


def test_adapter_reads_metadata_without_downloading(monkeypatch) -> None:
    captured_options = {}

    class FakeYoutubeDL:
        def __init__(self, options) -> None:
            captured_options.update(options)

        def __enter__(self):
            return self

        def __exit__(self, *_args) -> None:
            return None

        def extract_info(self, url: str, *, download: bool):
            assert url == "https://www.tiktok.com/@creator/video/123"
            assert download is False
            return {"id": "abc", "title": "Example"}

    monkeypatch.setattr("video_downloader.adapters.yt_dlp_adapter.YoutubeDL", FakeYoutubeDL)

    result = YtDlpAdapter().get_metadata("https://www.tiktok.com/@creator/video/123")

    assert result["id"] == "abc"
    assert str(captured_options["impersonate"]) == "chrome"
    assert captured_options["skip_download"] is True
    assert captured_options["noplaylist"] is True


def test_adapter_rejects_resolved_file_outside_output(tmp_path: Path) -> None:
    outside_file = tmp_path.parent / "outside.mp4"

    with pytest.raises(DownloadError, match="outside the selected output"):
        YtDlpAdapter._ensure_inside_output(outside_file, tmp_path)


def test_adapter_stops_before_extraction_when_ffmpeg_is_missing(tmp_path: Path) -> None:
    class MissingMediaProbe(FakeMediaProbe):
        def ensure_tools(self) -> None:
            raise FfmpegMissingError("Missing ffmpeg")

    with pytest.raises(FfmpegMissingError, match="Missing ffmpeg"):
        YtDlpAdapter(media_probe=MissingMediaProbe()).download(
            "https://example.com/video", tmp_path
        )


def test_adapter_rejects_unknown_height_fallback_above_cap(
    monkeypatch, tmp_path: Path
) -> None:
    downloaded_file = tmp_path / "too-large.mp4"
    downloaded_file.write_bytes(b"video")

    class FakeYoutubeDL:
        def __init__(self, _options) -> None:
            self.params = _options

        def __enter__(self):
            return self

        def __exit__(self, *_args) -> None:
            return None

        def extract_info(self, _url: str, *, download: bool):
            if not download:
                return {"id": "abc", "title": "Unknown dimensions"}

        def process_info(self, info) -> None:
            info["filepath"] = str(downloaded_file)

    monkeypatch.setattr("video_downloader.adapters.yt_dlp_adapter.YoutubeDL", FakeYoutubeDL)

    with pytest.raises(DownloadError, match="1080p.*720p limit"):
        YtDlpAdapter(media_probe=FakeMediaProbe(height=1080)).download(
            "https://example.com/video", tmp_path, quality="720"
        )


def test_adapter_emits_download_merge_and_verify_events(monkeypatch, tmp_path: Path) -> None:
    downloaded_file = tmp_path / "merged.mp4"
    downloaded_file.write_bytes(b"video")

    class FakeYoutubeDL:
        def __init__(self, options) -> None:
            self.options = options
            self.params = options

        def __enter__(self):
            return self

        def __exit__(self, *_args) -> None:
            return None

        def extract_info(self, _url: str, *, download: bool):
            assert download is False
            return {"id": "abc", "title": "Example"}

        def process_info(self, info) -> None:
            self.options["progress_hooks"][0](
                {
                    "status": "downloading",
                    "downloaded_bytes": 50,
                    "total_bytes": 100,
                    "speed": 10,
                    "eta": 5,
                }
            )
            self.options["postprocessor_hooks"][0](
                {"status": "started", "postprocessor": "Merger"}
            )
            info["filepath"] = str(downloaded_file)

    monkeypatch.setattr("video_downloader.adapters.yt_dlp_adapter.YoutubeDL", FakeYoutubeDL)
    events = []

    YtDlpAdapter(
        media_probe=FakeMediaProbe(),
        progress_callback=events.append,
    ).download("https://example.com/video", tmp_path)

    assert [event.status for event in events] == [
        ProgressStatus.DOWNLOADING,
        ProgressStatus.MERGING,
        ProgressStatus.VERIFYING,
    ]
