"""Composite one frame of the room."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from PySide6.QtGui import QColor, QImage, QPainter

from . import assets_loader as assets

# When the window changes. Local hours, and deliberately blunt: the room is a
# companion, not a clock, and nothing here is worth a crossfade.
EVENING_FROM = 18
NIGHT_FROM = 22
DAY_FROM = 7

# How long the amp's readout holds each half of its pulse. Slow on purpose — on a
# panel this small anything quicker reads as a fault rather than as activity.
AMP_BLINK_SECONDS = 0.9


def time_of_day(now: datetime | None = None) -> str:
    """Which light the room is in.

    Follows the real clock and nothing else. The window is the one thing in the
    room that ignores playback entirely — the cat is what reacts to music.
    """
    hour = (now or datetime.now()).hour
    if DAY_FROM <= hour < EVENING_FROM:
        return "day"
    if EVENING_FROM <= hour < NIGHT_FROM:
        return "evening"
    return "night"


def quantized(colour: QColor, steps: int) -> QColor:
    """Snap a colour onto the room's value ladder.

    The rest of the room was quantized at bake time. The amp's readout is the one
    colour painted live, and left alone it was the only thing in the frame off
    the palette — small, but exactly the sort of pixel that reads as a mistake.
    """
    return QColor(
        *(round(c / 255 * steps) * 255 // steps
          for c in (colour.red(), colour.green(), colour.blue()))
    )


def amp_colour(colour: QColor | None, *, playing: bool, at: float) -> QColor | None:
    """What the amp's readout shows this frame.

    The album's own colour while something is playing, pulsing gently between two
    brightnesses, and nothing at all when it is not.
    """
    if colour is None or not playing:
        return None
    bright = int(at / AMP_BLINK_SECONDS) % 2 == 0
    return colour if bright else colour.darker(150)


@dataclass
class Frame:
    """Everything needed to draw one frame, and nothing about where it came
    from — the demo source and the Windows source produce the same thing."""

    artwork: QImage | None = None
    label_colour: QColor | None = None
    amp_colour: QColor | None = None
    cat_clip: str = "breathe"
    cat_frame: int = 0
    # Where the record has turned to. It is not in the background at all, so
    # frame 0 is a stopped record rather than no record.
    record_frame: int = 0
    light: str = "day"
    dim: bool = False
    # Distinct from `not dim`: with nothing playing at all the room is quiet but
    # bright — an empty daytime bedroom, not a paused one.
    playing: bool = False


def compose(frame: Frame) -> QImage:
    layout = assets.layout()
    when = frame.light if frame.light in layout.times_of_day else layout.times_of_day[0]
    room = assets.background(when).copy()

    painter = QPainter(room)
    if frame.artwork is not None:
        painter.drawImage(layout.sleeve.x, layout.sleeve.y, frame.artwork)

    # The record, always — the background has a bare platter, and this is what
    # puts a record on the deck. Before the label, so the album's colour stays on
    # top and the grooves stop where they stop on a real record.
    records = assets.record_frames(when)
    painter.drawImage(0, 0, records[frame.record_frame % len(records)])

    if frame.label_colour is not None:
        painter.fillRect(
            layout.label.x,
            layout.label.y,
            layout.label.width,
            layout.label.height,
            frame.label_colour,
        )
    if frame.amp_colour is not None:
        painter.fillRect(
            layout.amp.x,
            layout.amp.y,
            layout.amp.width,
            layout.amp.height,
            quantized(frame.amp_colour, layout.sleeve_grade[when]["steps"]),
        )

    # An unknown clip falls back to the resting loop rather than raising. A
    # missing reaction should cost the cat a gesture, not the whole room.
    clip = frame.cat_clip if frame.cat_clip in layout.cat_clips else layout.resting_clip
    cats = assets.cat_frames(when, clip)
    painter.drawImage(0, 0, cats[frame.cat_frame % len(cats)])

    if frame.dim:
        # Paused: the room quietens rather than switching to another palette.
        painter.fillRect(room.rect(), QColor(18, 20, 38, 90))
    painter.end()
    return room
