"""An invented player, so the room is alive with nothing installed.

Never engaged automatically. With no real session the room enters a genuine
quiet state instead — if closing Spotify made fictional music appear, the app
would look broken.
"""

from __future__ import annotations

from dataclasses import dataclass

from .model import Controls, NowPlaying, PlaybackState

DEMO_APP_ID = "bedroom.demo"

_TRACKS = (
    ("Slow Hours", "The Long Way Home", "Afternoon Light"),
    ("Paper Windows", "Kestrel", "Second Storey"),
    ("Nothing Doing", "Marla Vance", "Quiet Machines"),
)


@dataclass
class DemoSource:
    """Cycles a handful of invented tracks on a fixed cadence."""

    seconds_per_track: float = 24.0
    _elapsed: float = 0.0
    _index: int = 0
    _playing: bool = True

    def advance(self, delta: float) -> bool:
        """Returns True when the track changed."""
        if not self._playing:
            return False
        self._elapsed += delta
        if self._elapsed < self.seconds_per_track:
            return False
        self._elapsed = 0.0
        self._index = (self._index + 1) % len(_TRACKS)
        return True

    def toggle(self) -> None:
        self._playing = not self._playing

    def skip(self, step: int) -> None:
        self._index = (self._index + step) % len(_TRACKS)
        self._elapsed = 0.0

    @property
    def cover_index(self) -> int:
        return self._index

    def now_playing(self) -> NowPlaying:
        title, artist, album = _TRACKS[self._index]
        return NowPlaying(
            app_id=DEMO_APP_ID,
            title=title,
            artist=artist,
            album=album,
            state=PlaybackState.PLAYING if self._playing else PlaybackState.PAUSED,
            controls=Controls(play=True, pause=True, next=True, previous=True),
        )
