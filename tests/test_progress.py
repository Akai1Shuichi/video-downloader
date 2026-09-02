from video_downloader.progress import (
    ProgressEvent,
    ProgressStatus,
    TerminalProgressReporter,
    event_from_yt_dlp,
)


def test_progress_hook_maps_percentage_size_speed_and_eta() -> None:
    event = event_from_yt_dlp(
        {
            "status": "downloading",
            "downloaded_bytes": 5 * 1024 * 1024,
            "total_bytes": 10 * 1024 * 1024,
            "speed": 2 * 1024 * 1024,
            "eta": 5,
        }
    )

    assert event is not None
    assert event.percent == 50
    assert event.speed == 2 * 1024 * 1024
    assert event.eta == 5


def test_terminal_reporter_prints_human_readable_download(capsys) -> None:
    reporter = TerminalProgressReporter(minimum_percent_step=0)

    reporter(
        ProgressEvent(
            ProgressStatus.DOWNLOADING,
            downloaded_bytes=5 * 1024 * 1024,
            total_bytes=10 * 1024 * 1024,
            speed=2 * 1024 * 1024,
            eta=5,
        )
    )

    output = capsys.readouterr().out
    assert "50.0%" in output
    assert "5.0 MiB / 10.0 MiB" in output
    assert "2.0 MiB/s" in output
    assert "ETA 00:05" in output


def test_terminal_reporter_prints_lifecycle_and_retry(capsys) -> None:
    reporter = TerminalProgressReporter()
    reporter(ProgressEvent(ProgressStatus.READING_METADATA))
    reporter(ProgressEvent(ProgressStatus.MERGING))
    reporter(ProgressEvent(ProgressStatus.VERIFYING))
    reporter(
        ProgressEvent(
            ProgressStatus.RETRYING,
            attempt=2,
            max_attempts=3,
            delay_seconds=1,
            message="[NETWORK_ERROR] timeout",
        )
    )
    reporter(ProgressEvent(ProgressStatus.COMPLETED))

    output = capsys.readouterr().out
    for text in ("Reading metadata", "Merging", "Verifying", "Retry 2/3", "Completed"):
        assert text in output

