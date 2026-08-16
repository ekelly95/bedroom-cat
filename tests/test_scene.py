"""Composition: the room, the artwork slot, and the cat frames."""

from __future__ import annotations

from PySide6.QtGui import QColor, QImage

from bedroom import assets_loader as assets
from bedroom.scene import Frame, compose


def solid(size: int, colour: QColor) -> QImage:
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(colour)
    return image


def test_layout_matches_the_authored_canvas() -> None:
    layout = assets.layout()
    assert (layout.width, layout.height) == (320, 200)
    assert (layout.sleeve.width, layout.sleeve.height) == (52, 52)
    assert layout.cat_breathe_frames > 1


def test_background_is_the_canvas_size() -> None:
    background = assets.load("background.png")
    layout = assets.layout()
    assert background.size().toTuple() == (layout.width, layout.height)


def test_every_cat_frame_is_the_canvas_size() -> None:
    layout = assets.layout()
    frames = assets.cat_breathe_frames()
    assert len(frames) == layout.cat_breathe_frames
    for frame in frames:
        assert frame.size().toTuple() == (layout.width, layout.height)


def test_composed_room_is_the_canvas_size() -> None:
    room = compose(Frame())
    layout = assets.layout()
    assert room.size().toTuple() == (layout.width, layout.height)


def test_artwork_lands_in_the_sleeve_slot() -> None:
    layout = assets.layout()
    magenta = QColor(255, 0, 255)
    room = compose(Frame(artwork=solid(layout.sleeve.width, magenta)))

    inside = room.pixelColor(layout.sleeve.x + 2, layout.sleeve.y + 2)
    assert (inside.red(), inside.green(), inside.blue()) == (255, 0, 255)

    outside = room.pixelColor(layout.sleeve.x - 3, layout.sleeve.y + 2)
    assert (outside.red(), outside.green(), outside.blue()) != (255, 0, 255)


def test_label_colour_lands_on_the_record() -> None:
    layout = assets.layout()
    room = compose(Frame(label_colour=QColor(0, 255, 0)))
    pixel = room.pixelColor(layout.label.x + 1, layout.label.y + 1)
    assert (pixel.red(), pixel.green(), pixel.blue()) == (0, 255, 0)


def test_a_frame_with_no_artwork_still_composes() -> None:
    room = compose(Frame(artwork=None, label_colour=None))
    assert not room.isNull()


def test_cat_frame_index_wraps_rather_than_raising() -> None:
    layout = assets.layout()
    room = compose(Frame(cat_frame=layout.cat_breathe_frames * 3 + 1))
    assert not room.isNull()


def test_breathing_frames_actually_differ() -> None:
    frames = assets.cat_breathe_frames()
    rendered = [compose(Frame(cat_frame=i)) for i in range(len(frames))]
    assert any(rendered[0] != other for other in rendered[1:]), (
        "if every breath frame renders identically the animation is not running"
    )


def test_dimming_darkens_the_room() -> None:
    def brightness(image: QImage) -> int:
        c = image.pixelColor(160, 30)
        return c.red() + c.green() + c.blue()

    assert brightness(compose(Frame(dim=True))) < brightness(compose(Frame()))
