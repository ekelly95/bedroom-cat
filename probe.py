"""Report exactly what Windows tells us about currently-playing media.

This is the Step 1 spike: it answers whether the players this was built for
actually publish usable now-playing information, and it stays in the repo
afterwards as a diagnostic for when a player stops cooperating.

Run it, then play something in Brave, Spotify and foobar2000 in turn:

    uv run python probe.py

It reprints only when something changes, so you can leave it running and watch
fields appear (or fail to) as you skip tracks.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import sys
import time
from dataclasses import dataclass, field
from datetime import timedelta

from winrt.windows.media.control import (
    GlobalSystemMediaTransportControlsSession as Session,
)
from winrt.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionManager as SessionManager,
)
from winrt.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionPlaybackStatus as PlaybackStatus,
)
from winrt.windows.storage.streams import Buffer, InputStreamOptions

STATUS_NAMES = {
    PlaybackStatus.CLOSED: "CLOSED",
    PlaybackStatus.OPENED: "OPENED",
    PlaybackStatus.CHANGING: "CHANGING",
    PlaybackStatus.STOPPED: "STOPPED",
    PlaybackStatus.PLAYING: "PLAYING",
    PlaybackStatus.PAUSED: "PAUSED",
}


@dataclass
class Artwork:
    """What we managed to learn about a session's thumbnail."""

    present: bool = False
    byte_count: int | None = None
    content_type: str | None = None
    detected_format: str | None = None
    dimensions: tuple[int, int] | None = None
    read_error: str | None = None

    def describe(self) -> str:
        if not self.present:
            return "none"
        if self.read_error:
            return f"PRESENT but unreadable — {self.read_error}"
        bits = [f"{self.byte_count:,} bytes"]
        if self.detected_format:
            bits.append(self.detected_format)
        if self.dimensions:
            bits.append(f"{self.dimensions[0]}x{self.dimensions[1]}")
        if self.content_type:
            bits.append(f"content-type {self.content_type}")
        return "PRESENT  " + "  ".join(bits)


@dataclass
class Snapshot:
    app_id: str
    is_current: bool
    status: str
    title: str
    artist: str
    album: str
    album_artist: str
    track_number: int | None
    position: timedelta
    duration: timedelta
    artwork: Artwork = field(default_factory=Artwork)
    controls: dict[str, bool] = field(default_factory=dict)
    error: str | None = None

    def identity(self) -> tuple:
        """Everything except position — position changes constantly and would
        make every poll look like a change."""
        return (
            self.app_id,
            self.is_current,
            self.status,
            self.title,
            self.artist,
            self.album,
            self.album_artist,
            self.track_number,
            self.duration,
            self.artwork.describe(),
            tuple(sorted(self.controls.items())),
            self.error,
        )


def _image_format(data: bytes) -> str | None:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if data.startswith(b"GIF8"):
        return "gif"
    if data.startswith(b"BM"):
        return "bmp"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None


def _jpeg_dimensions(data: bytes) -> tuple[int, int] | None:
    i = 2  # skip the SOI marker
    while i + 9 <= len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker == 0xFF:
            i += 1  # fill byte, not a marker of its own
            continue
        # Standalone markers carry no length field to skip over.
        if marker in (0x01, 0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        # SOF0-SOF15 hold the frame size. DHT/JPG/DAC sit in the same numeric
        # range but are not frame headers.
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            return (
                int.from_bytes(data[i + 7 : i + 9], "big"),
                int.from_bytes(data[i + 5 : i + 7], "big"),
            )
        segment = int.from_bytes(data[i + 2 : i + 4], "big")
        if segment < 2:
            return None  # malformed, and advancing by it would not terminate
        i += 2 + segment
    return None


def _image_dimensions(data: bytes, fmt: str | None) -> tuple[int, int] | None:
    """Read width/height straight from the file header.

    Deliberately dependency-free: the spike should not need Pillow or Qt just to
    tell us how big an album cover is.
    """
    size: tuple[int, int] | None = None
    if fmt == "png" and len(data) >= 24:
        size = (
            int.from_bytes(data[16:20], "big"),
            int.from_bytes(data[20:24], "big"),
        )
    elif fmt == "gif" and len(data) >= 10:
        size = (
            int.from_bytes(data[6:8], "little"),
            int.from_bytes(data[8:10], "little"),
        )
    elif fmt == "jpeg":
        size = _jpeg_dimensions(data)
    # A truncated header parses to zeroes rather than raising, so treat a
    # zero dimension as "could not tell" instead of reporting a 0x0 cover.
    if size is None or size[0] <= 0 or size[1] <= 0:
        return None
    return size


async def _read_artwork(thumbnail) -> Artwork:
    if thumbnail is None:
        return Artwork(present=False)
    art = Artwork(present=True)
    try:
        stream = await thumbnail.open_read_async()
        art.content_type = getattr(stream, "content_type", None) or None
        size = stream.size
        if size == 0:
            art.read_error = "stream reported zero bytes"
            return art
        buffer = Buffer(size)
        await stream.read_async(buffer, size, InputStreamOptions.READ_AHEAD)
        data = bytes(memoryview(buffer))[: buffer.length]
        art.byte_count = len(data)
        art.detected_format = _image_format(data)
        art.dimensions = _image_dimensions(data, art.detected_format)
        if art.detected_format is None:
            art.read_error = "bytes read, but not a format we recognise"
    except OSError as exc:
        art.read_error = f"{type(exc).__name__}: {exc}"
    return art


def _controls(session: Session) -> dict[str, bool]:
    c = session.get_playback_info().controls
    return {
        "play": bool(c.is_play_enabled),
        "pause": bool(c.is_pause_enabled),
        "next": bool(c.is_next_enabled),
        "prev": bool(c.is_previous_enabled),
        "stop": bool(c.is_stop_enabled),
        "seek": bool(c.is_playback_position_enabled),
    }


async def _snapshot(session: Session, current_id: str | None) -> Snapshot:
    app_id = session.source_app_user_model_id or "(no app id)"
    try:
        info = session.get_playback_info()
        timeline = session.get_timeline_properties()
        props = await session.try_get_media_properties_async()
        return Snapshot(
            app_id=app_id,
            is_current=app_id == current_id,
            status=STATUS_NAMES.get(info.playback_status, str(info.playback_status)),
            title=props.title or "",
            artist=props.artist or "",
            album=props.album_title or "",
            album_artist=props.album_artist or "",
            track_number=props.track_number or None,
            position=timeline.position,
            duration=timeline.end_time,
            artwork=await _read_artwork(props.thumbnail),
            controls=_controls(session),
        )
    except OSError as exc:
        return Snapshot(
            app_id=app_id,
            is_current=app_id == current_id,
            status="?",
            title="",
            artist="",
            album="",
            album_artist="",
            track_number=None,
            position=timedelta(),
            duration=timedelta(),
            error=f"{type(exc).__name__}: {exc}",
        )


def _clock(delta: timedelta) -> str:
    total = int(delta.total_seconds())
    if total < 0:
        return "-:--"
    return f"{total // 60}:{total % 60:02d}"


def _render_compact(snapshots: list[Snapshot]) -> str:
    """One line per session, for watching which one Windows calls current.

    The app defaults to Windows' own current session, so what matters is how
    that marker moves as you switch between players — not the metadata.
    """
    if not snapshots:
        return "  (no sessions)"
    lines = []
    for s in snapshots:
        marker = "->" if s.is_current else "  "
        title = (s.title or "(no title)")[:44]
        lines.append(f"  {marker} {s.app_id:18s} {s.status:8s} {title}")
    return "\n".join(lines)


def _render(snapshots: list[Snapshot]) -> str:
    if not snapshots:
        return (
            "  no media sessions at all\n"
            "  (nothing is publishing to Windows right now — start playback somewhere)"
        )
    lines = []
    for s in snapshots:
        lines.append(f"  {'>' if s.is_current else ' '} {s.app_id}")
        if s.error:
            lines.append(f"      FAILED     {s.error}")
            continue
        lines.append(f"      state      {s.status}")
        lines.append(f"      title      {s.title or '(empty)'}")
        lines.append(f"      artist     {s.artist or '(empty)'}")
        lines.append(f"      album      {s.album or '(empty)'}")
        if s.album_artist:
            lines.append(f"      alb.artist {s.album_artist}")
        if s.track_number:
            lines.append(f"      track no   {s.track_number}")
        lines.append(f"      position   {_clock(s.position)} / {_clock(s.duration)}")
        lines.append(f"      artwork    {s.artwork.describe()}")
        lines.append(
            "      controls   "
            + " ".join(f"{k}={'y' if v else 'n'}" for k, v in s.controls.items())
        )
        lines.append("")
    return "\n".join(lines).rstrip()


async def _collect(manager: SessionManager) -> list[Snapshot]:
    current = manager.get_current_session()
    current_id = current.source_app_user_model_id if current else None
    return [await _snapshot(s, current_id) for s in manager.get_sessions()]


async def run(interval: float, once: bool, compact: bool) -> None:
    manager = await SessionManager.request_async()
    started = time.monotonic()
    print("Watching Windows media sessions. Ctrl+C to stop.\n", flush=True)
    last: object = object()
    tick = 0
    while True:
        snapshots = await _collect(manager)
        if compact:
            # Ignore position-only churn, but react to the current marker moving.
            identity = tuple(
                (s.app_id, s.is_current, s.status, s.title) for s in snapshots
            )
        else:
            identity = tuple(s.identity() for s in snapshots)
        if identity != last:
            last = identity
            elapsed = time.monotonic() - started
            print(
                f"--- change #{tick}  |  t+{elapsed:6.1f}s  |  {len(snapshots)} session(s) ---",
                flush=True,
            )
            print(_render_compact(snapshots) if compact else _render(snapshots), flush=True)
            print(flush=True)
            tick += 1
        if once:
            return
        await asyncio.sleep(interval)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true", help="print one snapshot and exit")
    parser.add_argument("--interval", type=float, default=1.0, help="seconds between polls")
    parser.add_argument(
        "--compact",
        action="store_true",
        help="one line per session, showing which one Windows calls current",
    )
    args = parser.parse_args()
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(run(args.interval, args.once, args.compact))
    return 0


if __name__ == "__main__":
    sys.exit(main())
