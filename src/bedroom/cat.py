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

On top of that pace there are **reactions**: short authored clips that play once
over the breathing loop and hand straight back to it. They are where the comedy
lives, so they are kept rare on purpose — a cat that performed on every track
change would be a toy, and the point is an animal that mostly ignores you.
"""

from __future__ import annotations

import random
from collections.abc import Mapping
from dataclasses import dataclass, field

# Seconds for one unhurried breath.
#
# Kept near a second on purpose. The visible movement is a single logical pixel
# along the back and another under the belly, and stretched over several seconds
# that reads as slow drift rather than as breathing — the cat looks broken
# rather than calm. A short cycle with a tiny amplitude is what reads as alive.
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

# Reaction clips play at a fixed pace of their own, not at the breathing pace: a
# yawn that sped up because the cat was excited looked like a fault. Kept in step
# with __main__.TICK_MS so one authored frame is one drawn frame.
REACTION_FRAME_SECONDS = 0.12

# How often a track change is worth reacting to at all, and how many of those
# reactions are a proper look rather than an ear.
TRACK_CHANGE_CHANCE = 0.22
GLANCE_SHARE = 0.35

# No two reactions closer together than this, however much happens. Without it a
# burst of activity turned the cat into a puppet.
REACTION_COOLDOWN = 7.0

# What counts as being skipped through: this many track changes inside this many
# seconds earns the tail.
SKIP_RUN = 3
SKIP_WINDOW = 8.0

# How drowsy the cat gets before it stretches and gives up on the evening. Well
# short of `asleep`, because the stretch is what comes *before* sleep.
STRETCH_AT = 0.55
# Below this it counts as properly awake again and can earn another stretch.
RESET_STRETCH_BELOW = 0.2

# Which reaction wins when two want the floor at once. A clip is never
# interrupted by something equal or lower — the cat finishes what it started.
PRIORITY = {"twitch": 1, "glance": 1, "thump": 2, "stretch": 2, "perk": 3}


@dataclass
class CatMind:
    """Tracks the cat's rhythm and turns elapsed time into a clip and a frame."""

    clips: Mapping[str, int]
    resting: str = "breathe"
    rng: random.Random = field(default_factory=random.Random)

    excitement: float = 0.0
    drowsiness: float = 0.0

    _phase: float = 0.0
    _period: float = CALM_PERIOD
    _was_playing: bool = False
    _last_track: tuple | None = None

    _clock: float = 0.0
    _clip: str = ""
    _clip_frame: float = 0.0
    _last_reaction_at: float = -REACTION_COOLDOWN
    _skips: list[float] = field(default_factory=list)
    _stretched: bool = False

    def __post_init__(self) -> None:
        self._period = self._fresh_period()

    # -- what the world does to the cat ----------------------------------

    def observe(self, playing: bool, track_key: tuple | None) -> None:
        """Feed in the current playback state. Safe to call every frame."""
        if playing and not self._was_playing:
            self.nudge(STARTED_NUDGE)
            self.react("perk")
        elif playing and track_key is not None and track_key != self._last_track:
            self.nudge(TRACK_CHANGE_NUDGE)
            self._note_skip()

        if track_key is not None:
            self._last_track = track_key
        self._was_playing = playing

    def react(self, clip: str) -> bool:
        """Ask for a reaction. It may well be refused, and that is the point.

        Refused if the clip does not exist, if something at least as important is
        already playing, or if the cat has reacted too recently. Only the caller
        that earned it — a run of skips, the music starting — should be calling
        this directly.
        """
        if clip not in self.clips or clip not in PRIORITY:
            return False
        if self._clip and PRIORITY[clip] <= PRIORITY[self._clip]:
            return False
        # The cooldown holds back the incidental reactions and nothing else. A
        # run of skips, or the music starting, has been earned by something the
        # listener actually did, and must not be swallowed because an ear
        # happened to twitch a moment earlier.
        cooling = self._clock - self._last_reaction_at < REACTION_COOLDOWN
        if cooling and PRIORITY[clip] == 1:
            return False

        self._clip = clip
        self._clip_frame = 0.0
        self._last_reaction_at = self._clock
        return True

    def _note_skip(self) -> None:
        """A track change: usually nothing, sometimes an ear, and if they keep
        coming, the tail."""
        self._skips.append(self._clock)
        self._skips = [t for t in self._skips if self._clock - t <= SKIP_WINDOW]

        if len(self._skips) >= SKIP_RUN:
            if self.react("thump"):
                self._skips.clear()
            return
        if self.rng.random() >= TRACK_CHANGE_CHANCE:
            return
        self.react("glance" if self.rng.random() < GLANCE_SHARE else "twitch")

    def nudge(self, strength: float) -> None:
        """A reaction, not a mode. It decays back to the cat's own pace."""
        self.excitement = min(1.0, self.excitement + strength)
        self.drowsiness = max(0.0, self.drowsiness - strength * 0.8)

    # -- the cat's own clock ---------------------------------------------

    def advance(self, delta: float) -> None:
        if delta <= 0:
            return
        self._clock += delta

        # Excitement decays on a half-life so the return to calm is gradual
        # rather than a cliff.
        self.excitement *= 0.5 ** (delta / EXCITEMENT_HALF_LIFE)
        if self.excitement < 0.001:
            self.excitement = 0.0

        if self._was_playing:
            self.drowsiness = max(0.0, self.drowsiness - delta / SECONDS_TO_WAKE)
        else:
            self.drowsiness = min(1.0, self.drowsiness + delta / SECONDS_TO_SLEEP)

        # One stretch per quiet spell, on the way down into sleep, and only once
        # the cat has properly woken can it earn another.
        if self.drowsiness < RESET_STRETCH_BELOW:
            self._stretched = False
        elif self.drowsiness >= STRETCH_AT and not self._stretched:
            self._stretched = True
            self.react("stretch")

        # A reaction runs on its own clock and always finishes, then hands the
        # cat straight back to its breathing.
        if self._clip:
            self._clip_frame += delta / REACTION_FRAME_SECONDS
            if self._clip_frame >= self.clips[self._clip]:
                self._clip = ""
                self._clip_frame = 0.0
            return

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
    def reacting(self) -> bool:
        return bool(self._clip)

    @property
    def clip(self) -> str:
        """Which authored clip is on screen — the resting loop unless something
        has earned an interruption."""
        return self._clip or self.resting

    @property
    def frame(self) -> int:
        if self._clip:
            return min(self.clips[self._clip] - 1, int(self._clip_frame))
        count = self.clips[self.resting]
        return min(count - 1, int(self._phase * count))
