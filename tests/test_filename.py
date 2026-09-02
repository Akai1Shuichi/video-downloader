from pathlib import Path

from video_downloader.filename import MAX_STEM_BYTES, build_safe_stem, sanitize_filename_component


def test_sanitize_removes_cross_platform_invalid_characters() -> None:
    result = sanitize_filename_component('  video: <demo>/part\\name?*|"  ')

    assert result == "video_ _demo__part_name____"
    assert not any(character in result for character in '<>:"/\\|?*')


def test_sanitize_preserves_vietnamese_and_emoji() -> None:
    assert sanitize_filename_component("  Đi chơi ở Viêng Chăn 🎬  ") == "Đi chơi ở Viêng Chăn 🎬"


def test_safe_stem_blocks_path_traversal_and_absolute_paths() -> None:
    stem = build_safe_stem("ignored", "abc123", "/tmp/../../outside\\video")

    assert "/" not in stem
    assert "\\" not in stem
    assert ".." not in stem
    assert not Path(stem).is_absolute()
    assert stem.endswith("[abc123]")


def test_safe_stem_is_limited_by_utf8_bytes_without_breaking_emoji() -> None:
    stem = build_safe_stem("🎬" * 200, "video-id")

    assert len(stem.encode("utf-8")) <= MAX_STEM_BYTES
    assert "�" not in stem
    assert stem.endswith("[video-id]")


def test_same_title_with_different_ids_does_not_collide() -> None:
    first = build_safe_stem("Same title", "id-one")
    second = build_safe_stem("Same title", "id-two")

    assert first != second


def test_requested_qualities_do_not_reuse_the_same_filename() -> None:
    best = build_safe_stem("Title", "id")
    capped = build_safe_stem("Title", "id", quality_label="720p")

    assert best != capped
    assert capped == "Title [720p] [id]"


def test_windows_reserved_name_is_prefixed() -> None:
    assert sanitize_filename_component("CON") == "_CON"
