"""The cat's own clock.

The cat is never synchronised to the music. It breathes on its own rhythm
whether or not anything is playing, and playback only *nudges* that rhythm —
each nudge decaying back into the cat's own pace rather than becoming a mode it
stays locked in.

Beat synchronisation would need system audio capture and analysis, and would
make the cat look mechanically tied to the track instead of alive. None of that
is here on purpose.

What playback does:

- **music starts** — the cat perks up: quicker, shallower breathing that eases
  off over the next few seconds
- **track changes** — a smaller nudge of the same kind
- **paused or quiet** — drowsiness builds and the breathing slows right down,
  until the cat is effectively asleep

Only the breathing frames are authored so far, so those reactions currently show
as changes of pace. The ear flick, the glance towards the speakers and the
stretch-and-settle are separate sprite work; they hook onto the same events.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

# Seconds for one unhurried breath.
#
# Kept near a second on purpose. The visible movement is only about two logical
# pixels, and stretched over several seconds that reads as slow drift rather
# than as breathing — the cat looks broken rather than calm. A short cycle with
# a small amplitude is what reads as alive.
CALM_PERIOD = 1.5
# How much a fully-excited cat shortens that by.
EXCITEMENT_SPEEDUP = 0.35
# How much a fully-asleep cat lengthens it by.
DROWSY_SLOWDOWN = 1.4

# Excitement falls to half in this many seconds — long enough to notice, short
# enough that the cat is back to itself well before the track ends.
EXCITEMENT_HALF_LIFE = 3.5

# Drowsiness takes about this long to set in fully once the music stops, and
# clears far faster than it arrives.
SECONDS_TO_SLEEP = 40.0
SECONDS_TO_WAKE = 4.0

STARTED_NUDGE = 1.0
TRACK_CHANGE_NUDGE = 0.55


@dataclass
class CatMind:
    """Tracks the cat's rhythm and turns elapsed time into a frame number."""

    frames: int
    rng: random.Random = field(default_factory=random.Random)

    excitement: float = 0.0
    drowsiness: float = 0.0

    _phase: float = 0.0
    _period: float = CALM_PERIOD
    _was_playing: bool = False
    _last_track: tuple | None = None

    def __post_init__(self) -> None:
        self._period = self._fresh_period()

    # -- what the world does to the cat ----------------------------------

    def observe(self, playing: bool, track_key: tuple | None) -> None:
        """Feed in the current playback state. Safe to call every frame."""
        if playing and not self._was_playing:
            self.nudge(STARTED_NUDGE)
        elif playing and track_key is not None and track_key != self._last_track:
            self.nudge(TRACK_CHANGE_NUDGE)

        if track_key is not None:
            self._last_track = track_key
        self._was_playing = playing

    def nudge(self, strength: float) -> None:
        """A reaction, not a mode. It decays back to the cat's own pace."""
        self.excitement = min(1.0, self.excitement + strength)
        self.drowsiness = max(0.0, self.drowsiness - strength * 0.8)

    # -- the cat's own clock ---------------------------------------------

    def advance(self, delta: float) -> None:
        if delta <= 0:
            return

        # Excitement decays on a half-life so the return to calm is gradual
        # rather than a cliff.
        self.excitement *= 0.5 ** (delta / EXCITEMENT_HALF_LIFE)
        if self.excitement < 0.001:
            self.excitement = 0.0

        if self._was_playing:
            self.drowsiness = max(0.0, self.drowsiness - delta / SECONDS_TO_WAKE)
        else:
            self.drowsiness = min(1.0, self.drowsiness + delta / SECONDS_TO_SLEEP)

        self._phase += delta / self._period
        while self._phase >= 1.0:
            self._phase -= 1.0
            self._period = self._fresh_period()

    def _fresh_period(self) -> float:
        """Length of the next breath.

        Jittered every cycle so the rhythm is never metronomic — the same event
        should not look identical twice.
        """
        period = (
            CALM_PERIOD
            - EXCITEMENT_SPEEDUP * self.excitement
            + DROWSY_SLOWDOWN * self.drowsiness
        )
        return max(0.6, period * self.rng.uniform(0.92, 1.08))

    @property
    def period(self) -> float:
        return self._period

    @property
    def asleep(self) -> bool:
        return self.drowsiness > 0.8

    @property
    def frame(self) -> int:
        return min(self.frames - 1, int(self._phase * self.frames))
