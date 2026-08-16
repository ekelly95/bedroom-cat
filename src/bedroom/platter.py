"""The record's own clock.

A platter has mass. It takes a moment to come up to speed when the music starts,
and when the music stops it coasts: the groove highlight keeps sweeping, slower
and slower, and then the record is simply still. Where it stops is wherever it
happened to be — there is no home position, and snapping back to one would be the
single clearest way to make the room look like software.

This follows the play/pause state and nothing else. There is no beat detection
here and there is not going to be: it would need system audio capture, and it
would make the room look mechanically wired to the track instead of lived in.

The record is the only thing in the room that moves like this. The speakers were
going to have a two-frame sprite of their own, driven straight off playback with
no coasting; it came out as flicker rather than movement and was taken out. See
`make_assets.draw_speaker`.
"""

from __future__ import annotations

from dataclasses import dataclass

# One authored frame per drawn frame, matching `cat.REACTION_FRAME_SECONDS` and
# `__main__.TICK_MS`. At twelve frames to the half turn that sweeps the highlight
# through 180 degrees in 1.44 seconds: clearly turning, and still slow enough
# that the cat and not the turntable is what the eye goes to.
FRAME_SECONDS = 0.12
FULL_SPEED = 1 / FRAME_SECONDS

# Up quickly, down slowly. The asymmetry is the whole character of the thing —
# pressing play should feel answered, and pressing pause should not feel like a
# switch being thrown.
SPIN_UP_HALF_LIFE = 0.25
SPIN_DOWN_HALF_LIFE = 0.6

# An exponential decay never actually arrives, and "slows to a stop" has to mean
# stopped: below this the next frame is more than two seconds away, which already
# reads as still, so it is snapped to zero and the record is done. From full
# speed that puts the whole coast-down at about two and a half seconds.
STOP_BELOW = 0.4


@dataclass
class Platter:
    """Turns elapsed time and a play/pause state into a record frame."""

    frames: int

    _position: float = 0.0
    _speed: float = 0.0  # frames per second

    def advance(self, delta: float, *, playing: bool) -> None:
        """Move the record on by `delta` seconds. Safe to call every frame."""
        target = FULL_SPEED if playing else 0.0
        half_life = SPIN_UP_HALF_LIFE if self._speed < target else SPIN_DOWN_HALF_LIFE
        self._speed += (target - self._speed) * (1 - 0.5 ** (delta / half_life))
        if not playing and self._speed < STOP_BELOW:
            self._speed = 0.0
        self._position = (self._position + self._speed * delta) % self.frames

    @property
    def frame(self) -> int:
        return int(self._position) % self.frames

    @property
    def spinning(self) -> bool:
        return self._speed > 0.0
