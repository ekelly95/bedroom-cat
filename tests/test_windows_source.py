"""One broken player must not take the room down with it.

Almost nothing in `source_windows` can be tested — it talks to Windows. `_poll_once`
is the exception: it only reaches the world through `self._manager`, so a fake
manager can stand in for one, and that happens to be where the damage was.
"""

from __future__ import annotations

import asyncio

from PySide6.QtCore import Qt
from winrt.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionPlaybackStatus as Status,
)

from bedroom.model import PlaybackState
from bedroom.source_windows import WindowsSource


class FakeProperties:
    def __init__(self, title: str) -> None:
        self.title = title
        self.artist = "An Artist"
        self.album_title = "An Album"
        self.thumbnail = None


class FakeControls:
    is_play_enabled = True
    is_pause_enabled = True
    is_next_enabled = True
    is_previous_enabled = False


class FakePlaybackInfo:
    def __init__(self, status) -> None:
        self.playback_status = status
        self.controls = FakeControls()


class FakeSession:
    """A media session. `breaks` makes it throw the way a closing player does."""

    def __init__(self, app_id: str, *, breaks: bool = False, status=Status.PLAYING) -> None:
        self.source_app_user_model_id = app_id
        self._breaks = breaks
        self._status = status

    def get_playback_info(self):
        if self._breaks:
            raise OSError("the session went away mid-read")
        return FakePlaybackInfo(self._status)

    async def try_get_media_properties_async(self):
        if self._breaks:
            raise OSError("the session went away mid-read")
        return FakeProperties(f"Track from {self.source_app_user_model_id}")


class FakeManager:
    def __init__(self, sessions: list[FakeSession], current: FakeSession | None) -> None:
        self._sessions = sessions
        self._current = current

    def get_sessions(self):
        return list(self._sessions)

    def get_current_session(self):
        return self._current


def poll(sessions: list[FakeSession], current: FakeSession | None):
    """Run one poll against a fake manager and collect what it emitted.

    Direct connections on purpose. `WindowsSource` moves itself onto its worker
    thread in `__init__`, so an automatic connection would queue these onto a
    loop that is never started here and nothing would arrive.
    """
    source = WindowsSource()
    source._manager = FakeManager(sessions, current)

    seen: dict[str, object] = {"sessions": None, "now": None, "failures": []}
    direct = Qt.ConnectionType.DirectConnection
    source.sessions_changed.connect(
        lambda infos: seen.__setitem__("sessions", infos), direct
    )
    source.updated.connect(lambda now: seen.__setitem__("now", now), direct)
    source.failed.connect(lambda msg: seen["failures"].append(msg), direct)

    asyncio.run(source._poll_once())
    return seen


def test_a_healthy_session_is_reported() -> None:
    good = FakeSession("Spotify.exe")
    seen = poll([good], good)

    assert [s.app_id for s in seen["sessions"]] == ["Spotify.exe"]
    assert seen["now"] is not None
    assert seen["now"].state is PlaybackState.PLAYING


def test_one_broken_session_does_not_hide_the_healthy_ones() -> None:
    """The failure this is here for: a dying background player froze the room.

    Every session used to be read inside one guard, so a single session throwing
    abandoned the whole poll — no `sessions_changed`, no `updated`. A player that
    kept failing therefore held the room on old information indefinitely, even
    though the one being listened to was perfectly healthy.
    """
    good = FakeSession("Spotify.exe")
    bad = FakeSession("Ghost.exe", breaks=True)
    seen = poll([bad, good], good)

    assert [s.app_id for s in seen["sessions"]] == ["Spotify.exe"], (
        "the healthy player should still be reported"
    )
    assert seen["now"] is not None, "the room should still have been given a frame"
    assert seen["now"].app_id == "Spotify.exe"
    assert seen["failures"], "the broken player should still be surfaced, not swallowed"


def test_every_session_broken_still_finishes_the_poll() -> None:
    """No sessions and no *usable* sessions have to look the same to the room."""
    bad = FakeSession("Ghost.exe", breaks=True)
    seen = poll([bad], bad)

    assert seen["sessions"] == []
    assert seen["now"] is None, "an empty room, not a stale one"
