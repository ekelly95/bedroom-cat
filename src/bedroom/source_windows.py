"""Read what Windows is publishing, without stalling the room.

All WinRT work happens on a dedicated thread running its own asyncio loop, and
results reach the interface as Qt signals. The drawing never waits on Windows.

**Polling only, no event subscriptions.** The plan called for Windows change
events with polling as a safety net. Measurement showed polling alone catches
every change in under a second, and WinRT event callbacks arrive on arbitrary
threads, which is a real source of fragility for no gain in correctness — only
in latency, which does not matter for a room that breathes slowly.
"""

from __future__ import annotations

import asyncio

from PySide6.QtCore import QObject, QThread, Signal
from winrt.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionManager as SessionManager,
)
from winrt.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionPlaybackStatus as Status,
)
from winrt.windows.storage.streams import Buffer, InputStreamOptions

from .model import Controls, NowPlaying, PlaybackState, SessionInfo

_STATES = {
    Status.PLAYING: PlaybackState.PLAYING,
    Status.PAUSED: PlaybackState.PAUSED,
    Status.STOPPED: PlaybackState.STOPPED,
    Status.CLOSED: PlaybackState.STOPPED,
    Status.OPENED: PlaybackState.STOPPED,
    Status.CHANGING: PlaybackState.PLAYING,
}


def choose_session(
    sessions: list[SessionInfo], override: str | None
) -> SessionInfo | None:
    """Pick which session the room follows.

    Follows the session Windows itself names as current. Measured behaviour: a
    newly started session takes that marker even against one already playing,
    pausing hands it to whatever is still playing, and with nothing playing it
    stays put — which is what the room wants.

    Explicitly *not* "the first session reporting PLAYING". Several sessions
    linger routinely, and when two really are playing that rule picks an
    arbitrary one by enumeration order.

    Its one stale case — resuming an already-paused session while another keeps
    playing — is what `override` is for.
    """
    if not sessions:
        return None
    if override:
        for session in sessions:
            if session.app_id == override:
                return session
    for session in sessions:
        if session.is_current:
            return session
    return sessions[0]


class WindowsSource(QObject):
    """Owns the worker thread and hands out NowPlaying updates."""

    updated = Signal(object)  # NowPlaying | None
    sessions_changed = Signal(list)  # list[SessionInfo]
    failed = Signal(str)

    def __init__(self, poll_seconds: float = 0.7) -> None:
        super().__init__()
        self._poll_seconds = poll_seconds
        self._override: str | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._running = False
        self._manager = None

        # Artwork bytes are only re-read when the track changes. Windows
        # republishes the same thumbnail every poll, and reading the stream is
        # far and away the most expensive thing here.
        self._art_key: tuple | None = None
        self._art: bytes | None = None

        self._thread = QThread()
        self.moveToThread(self._thread)
        self._thread.started.connect(self._run)

    def start(self) -> None:
        self._running = True
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        self._thread.quit()
        self._thread.wait(2000)

    def set_override(self, app_id: str | None) -> None:
        self._override = app_id

    @property
    def override(self) -> str | None:
        return self._override

    def send(self, command: str) -> None:
        """Queue a transport command onto the worker's loop."""
        loop = self._loop
        if loop is None or not self._running:
            return
        asyncio.run_coroutine_threadsafe(self._send(command), loop)

    # ------------------------------------------------------------ worker ---

    def _run(self) -> None:
        try:
            asyncio.run(self._loop_forever())
        except Exception as exc:  # noqa: BLE001 - surfaced to the interface
            self.failed.emit(f"{type(exc).__name__}: {exc}")

    async def _loop_forever(self) -> None:
        self._loop = asyncio.get_running_loop()
        try:
            self._manager = await SessionManager.request_async()
        except OSError as exc:
            self.failed.emit(f"Windows would not hand over its media sessions: {exc}")
            return

        while self._running:
            try:
                await self._poll_once()
            except Exception as exc:  # noqa: BLE001 - one bad poll must not end the loop
                # A player closing mid-read is normal; keep going. Deliberately
                # broader than OSError: anything that escapes here used to reach
                # `_run`, which ends the loop, and the room then holds whatever it
                # last saw for as long as it stays open.
                self.failed.emit(f"{type(exc).__name__}: {exc}")
            await asyncio.sleep(self._poll_seconds)

    async def _poll_once(self) -> None:
        raw = list(self._manager.get_sessions())
        current = self._manager.get_current_session()
        current_id = current.source_app_user_model_id if current else None

        infos: list[SessionInfo] = []
        by_id: dict[str, object] = {}
        for session in raw:
            # Per session, not per poll. Reading a session that is closing throws,
            # and one guard around the whole loop meant a single dying background
            # player abandoned the poll for every healthy one — the room then sat
            # on old information for as long as that session kept failing.
            try:
                app_id = session.source_app_user_model_id or "(unknown)"
                state = _STATES.get(
                    session.get_playback_info().playback_status, PlaybackState.STOPPED
                )
                props = await session.try_get_media_properties_async()
            except Exception as exc:  # noqa: BLE001 - skip the bad player, keep the rest
                self.failed.emit(f"{type(exc).__name__}: {exc}")
                continue
            infos.append(
                SessionInfo(
                    app_id=app_id,
                    title=props.title or "",
                    state=state,
                    is_current=app_id == current_id,
                )
            )
            by_id[app_id] = (session, props, state)

        self.sessions_changed.emit(infos)

        chosen = choose_session(infos, self._override)
        if chosen is None:
            self._art_key = None
            self._art = None
            self.updated.emit(None)
            return

        session, props, state = by_id[chosen.app_id]
        info = session.get_playback_info()
        controls = info.controls

        now = NowPlaying(
            app_id=chosen.app_id,
            title=props.title or "",
            artist=props.artist or "",
            album=props.album_title or "",
            state=state,
            artwork=None,
            controls=Controls(
                play=bool(controls.is_play_enabled),
                pause=bool(controls.is_pause_enabled),
                next=bool(controls.is_next_enabled),
                previous=bool(controls.is_previous_enabled),
            ),
        )

        if now.track_key != self._art_key:
            self._art_key = now.track_key
            self._art = await self._read_artwork(props.thumbnail)
        self.updated.emit(
            NowPlaying(
                app_id=now.app_id,
                title=now.title,
                artist=now.artist,
                album=now.album,
                state=now.state,
                artwork=self._art,
                controls=now.controls,
            )
        )

    async def _read_artwork(self, thumbnail) -> bytes | None:
        if thumbnail is None:
            return None
        try:
            stream = await thumbnail.open_read_async()
            if stream.size == 0:
                return None
            # Read from the buffer ReadAsync hands back, not the one passed in:
            # the contract says an implementation may return a different buffer,
            # and every player tested here happens to return the same one. Falling
            # back keeps the tested behaviour if a binding returns nothing.
            supplied = Buffer(stream.size)
            filled = await stream.read_async(
                supplied, stream.size, InputStreamOptions.READ_AHEAD
            )
            buffer = filled if filled is not None else supplied
            return bytes(memoryview(buffer))[: buffer.length]
        except OSError:
            return None

    async def _send(self, command: str) -> None:
        if self._manager is None:
            return
        infos = [
            SessionInfo(
                app_id=s.source_app_user_model_id or "(unknown)",
                title="",
                state=PlaybackState.STOPPED,
                is_current=bool(
                    self._manager.get_current_session()
                    and s.source_app_user_model_id
                    == self._manager.get_current_session().source_app_user_model_id
                ),
            )
            for s in self._manager.get_sessions()
        ]
        chosen = choose_session(infos, self._override)
        if chosen is None:
            return
        for session in self._manager.get_sessions():
            if (session.source_app_user_model_id or "(unknown)") != chosen.app_id:
                continue
            try:
                match command:
                    case "playpause":
                        await session.try_toggle_play_pause_async()
                    case "next":
                        await session.try_skip_next_async()
                    case "previous":
                        await session.try_skip_previous_async()
            except OSError as exc:
                self.failed.emit(f"{command} failed: {exc}")
            return
