"""What the room needs to know about whatever is playing.

Deliberately not a mirror of the Windows API. Every player reports a different
subset — see the compatibility table in README.md — so this carries only the
fields the room actually uses, and every one of them is allowed to be absent.

Track position is not here at all. foobar2000 publishes no timeline, so v0.1
shows no progress decoration anywhere and does not need the number.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class PlaybackState(Enum):
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"

    @property
    def is_active(self) -> bool:
        """Whether the room should look like music is happening."""
        return self is PlaybackState.PLAYING


@dataclass(frozen=True)
class Controls:
    """Which transport buttons the player says it supports.

    These change per player *and* per moment, so the buttons are enabled from
    whatever arrived last rather than from a table of known applications.
    """

    play: bool = False
    pause: bool = False
    next: bool = False
    previous: bool = False


@dataclass(frozen=True)
class NowPlaying:
    app_id: str
    title: str = ""
    artist: str = ""
    album: str = ""
    state: PlaybackState = PlaybackState.STOPPED
    artwork: bytes | None = None
    controls: Controls = field(default_factory=Controls)

    @property
    def track_key(self) -> tuple[str, str, str, str]:
        """Identity of the track, for caching artwork and spotting changes.

        Keyed on the metadata rather than the artwork bytes so we do not have to
        decode an image to find out whether it is the one we already have.
        """
        return (self.app_id, self.title, self.artist, self.album)

    @property
    def display_title(self) -> str:
        return self.title or "(no title)"

    @property
    def display_artist(self) -> str:
        return self.artist or ""


@dataclass(frozen=True)
class SessionInfo:
    """One candidate source, for the override menu."""

    app_id: str
    title: str
    state: PlaybackState
    is_current: bool

    @property
    def label(self) -> str:
        name = self.app_id.removesuffix(".exe")
        return f"{name} — {self.title}" if self.title else name
