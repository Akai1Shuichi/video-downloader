from pathlib import Path

from video_downloader.metadata import map_video_metadata
from video_downloader.models import DownloadRequest, DownloadResult, VideoMetadata


def test_map_video_metadata_uses_extractor_and_deduplicates_heights() -> None:
    raw = {
        "id": 123,
        "title": "A [demo] video",
        "extractor_key": "TikTok",
        "uploader": "creator",
        "duration": 84.9,
        "thumbnail": "https://cdn.example/thumbnail.jpg",
        "formats": [{"height": 720}, {"height": 1080}, {"height": 720}, {"height": None}],
    }

    result = map_video_metadata(raw, "https://example.com/shared-video")

    assert result == VideoMetadata(
        id="123",
        source_url="https://example.com/shared-video",
        platform="tiktok",
        title="A [demo] video",
        uploader="creator",
        duration_seconds=84,
        thumbnail_url="https://cdn.example/thumbnail.jpg",
        available_heights=[720, 1080],
    )


def test_models_represent_request_and_download_result() -> None:
    request = DownloadRequest(url="https://example.com/video")
    result = DownloadResult(success=True, file_path=Path("downloads/video.mp4"))

    assert request.quality == "best"
    assert request.output_dir == Path("downloads")
    assert result.success is True

