"""Composite one frame of the room."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtGui import QColor, QImage, QPainter

from . import assets_loader as assets


@dataclass
class Frame:
    """Everything needed to draw one frame, and nothing about where it came
    from — the demo source and the Windows source produce the same thing."""

    artwork: QImage | None = None
    label_colour: QColor | None = None
    cat_frame: int = 0
    dim: bool = False
    # Distinct from `not dim`: with nothing playing at all the room is quiet but
    # bright — an empty daytime bedroom, not a paused one.
    playing: bool = False


def compose(frame: Frame) -> QImage:
    room = assets.load("background.png").copy()
    layout = assets.layout()

    painter = QPainter(room)
    if frame.artwork is not None:
        painter.drawImage(layout.sleeve.x, layout.sleeve.y, frame.artwork)
    if frame.label_colour is not None:
        painter.fillRect(
            layout.label.x,
            layout.label.y,
            layout.label.width,
            layout.label.height,
            frame.label_colour,
        )

    cats = assets.cat_breathe_frames()
    painter.drawImage(0, 0, cats[frame.cat_frame % len(cats)])
    painter.drawImage(0, 0, assets.load("light-day.png"))

    if frame.dim:
        # Paused: the room quietens rather than switching to another palette.
        painter.fillRect(room.rect(), QColor(18, 20, 38, 90))
    painter.end()
    return room
