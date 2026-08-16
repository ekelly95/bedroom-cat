"""Tests for the parts of the spike that can be checked without live playback."""

from __future__ import annotations

import struct
import sys
from datetime import timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from probe import _clock, _image_dimensions, _image_format  # noqa: E402


def _png(width: int, height: int) -> bytes:
    return (
        b"\x89PNG\r\n\x1a\n"
        + struct.pack(">I", 13)
        + b"IHDR"
        + struct.pack(">II", width, height)
        + b"\x08\x06\x00\x00\x00"
    )


def _jpeg(width: int, height: int, *, fill: bytes = b"") -> bytes:
    # SOI, a JFIF APP0 we should skip over, then an SOF0 carrying the size.
    app0 = b"\xff\xe0" + struct.pack(">H", 16) + b"JFIF\x00" + b"\x00" * 9
    sof0 = b"\xff\xc0" + struct.pack(">H", 17) + b"\x08" + struct.pack(">HH", height, width)
    return b"\xff\xd8" + app0 + fill + sof0 + b"\x00" * 8


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (_png(1, 1), "png"),
        (_jpeg(1, 1), "jpeg"),
        (b"GIF89a" + b"\x00" * 10, "gif"),
        (b"BM" + b"\x00" * 20, "bmp"),
        (b"RIFF\x00\x00\x00\x00WEBPVP8 ", "webp"),
        (b"not an image at all", None),
        (b"", None),
    ],
)
def test_image_format(data: bytes, expected: str | None) -> None:
    assert _image_format(data) == expected


def test_png_dimensions() -> None:
    assert _image_dimensions(_png(640, 480), "png") == (640, 480)


def test_jpeg_dimensions_skips_app0_segment() -> None:
    assert _image_dimensions(_jpeg(300, 300), "jpeg") == (300, 300)


def test_jpeg_dimensions_handles_spotify_sized_cover() -> None:
    assert _image_dimensions(_jpeg(640, 640), "jpeg") == (640, 640)


def test_gif_dimensions_are_little_endian() -> None:
    data = b"GIF89a" + struct.pack("<HH", 120, 90) + b"\x00" * 8
    assert _image_dimensions(data, "gif") == (120, 90)


def test_jpeg_dimensions_skip_fill_bytes_between_markers() -> None:
    assert _image_dimensions(_jpeg(300, 300, fill=b"\xff\xff\xff"), "jpeg") == (300, 300)


def test_jpeg_dimensions_skip_a_restart_marker_carrying_no_length() -> None:
    assert _image_dimensions(_jpeg(64, 64, fill=b"\xff\xd0"), "jpeg") == (64, 64)


def test_jpeg_dimensions_give_up_rather_than_loop_on_a_bad_segment_length() -> None:
    broken = b"\xff\xd8" + b"\xff\xe0" + struct.pack(">H", 0) + b"\x00" * 32
    assert _image_dimensions(broken, "jpeg") is None


def test_dimensions_return_none_on_truncated_data() -> None:
    assert _image_dimensions(b"\x89PNG\r\n\x1a\n", "png") is None
    assert _image_dimensions(b"\xff\xd8\xff", "jpeg") is None
    assert _image_dimensions(b"GIF89a", "gif") is None


def test_dimensions_return_none_rather_than_a_zero_sized_cover() -> None:
    assert _image_dimensions(_png(0, 0), "png") is None


def test_dimensions_return_none_for_unknown_format() -> None:
    assert _image_dimensions(b"whatever", None) is None


@pytest.mark.parametrize(
    ("seconds", "expected"),
    [(0, "0:00"), (5, "0:05"), (65, "1:05"), (3725, "62:05")],
)
def test_clock_formats_as_minutes_and_seconds(seconds: int, expected: str) -> None:
    assert _clock(timedelta(seconds=seconds)) == expected


def test_clock_handles_players_that_report_no_duration() -> None:
    assert _clock(timedelta(seconds=-1)) == "-:--"


def test_winrt_buffer_supports_the_slice_we_rely_on() -> None:
    """The artwork read does `bytes(memoryview(buffer))[:buffer.length]`.

    A Buffer's capacity and its length are different numbers, and reading past
    the length would hand Qt trailing zero bytes instead of an image, so this
    pins the mechanic rather than the API's existence.
    """
    from winrt.windows.storage.streams import Buffer

    buffer = Buffer(32)
    assert buffer.capacity == 32
    assert buffer.length == 0
    assert bytes(memoryview(buffer))[: buffer.length] == b""
