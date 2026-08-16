"""Composition: the room, the artwork slot, and the cat frames."""

from __future__ import annotations

from datetime import datetime

import pytest
from PySide6.QtGui import QColor, QImage

from bedroom import assets_loader as assets
from bedroom.scene import Frame, amp_colour, compose, time_of_day


def solid(size: int, colour: QColor) -> QImage:
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(colour)
    return image


def test_layout_matches_the_authored_canvas() -> None:
    layout = assets.layout()
    assert (layout.width, layout.height) == (320, 200)
    assert (layout.sleeve.width, layout.sleeve.height) == (52, 52)
    assert layout.resting_clip in layout.cat_clips
    assert all(count > 1 for count in layout.cat_clips.values())
    assert layout.record_frames > 1


def test_background_is_the_canvas_size() -> None:
    background = assets.background("day")
    layout = assets.layout()
    assert background.size().toTuple() == (layout.width, layout.height)


def test_every_cat_frame_of_every_clip_is_the_canvas_size() -> None:
    layout = assets.layout()
    for clip, count in layout.cat_clips.items():
        frames = assets.cat_frames("day", clip)
        assert len(frames) == count, clip
        for frame in frames:
            assert frame.size().toTuple() == (layout.width, layout.height), clip


@pytest.mark.parametrize("when", ["day", "evening", "night"])
def test_every_record_frame_of_every_band_is_the_canvas_size(when: str) -> None:
    layout = assets.layout()
    frames = assets.record_frames(when)
    assert len(frames) == layout.record_frames
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
    room = compose(Frame(cat_frame=layout.cat_clips[layout.resting_clip] * 3 + 1))
    assert not room.isNull()


def test_an_unknown_clip_falls_back_to_resting() -> None:
    """A missing reaction should cost the cat a gesture, not the whole room."""
    assert compose(Frame(cat_clip="backflip")) == compose(Frame())


def test_breathing_frames_actually_differ() -> None:
    frames = assets.cat_frames("day", "breathe")
    rendered = [compose(Frame(cat_frame=i)) for i in range(len(frames))]
    assert any(rendered[0] != other for other in rendered[1:]), (
        "if every breath frame renders identically the animation is not running"
    )


def test_every_reaction_actually_moves_the_cat() -> None:
    layout = assets.layout()
    rest = compose(Frame())
    for clip in layout.cat_clips:
        if clip == layout.resting_clip:
            continue
        rendered = [
            compose(Frame(cat_clip=clip, cat_frame=i))
            for i in range(layout.cat_clips[clip])
        ]
        assert any(r != rest for r in rendered), f"{clip} never leaves the resting pose"


# -- the record -------------------------------------------------------------
#
# The disc as `make_assets.draw_record` authors it, half-open, and a few patches
# inside it. Written out here rather than derived: a test that says where it is
# looking is easier to check than one that computes it, and these are the same
# numbers the art is drawn to.
DISC = (105, 78, 141, 88)
# Plain record, clear of the grooves, the label, the glint at frame 0 and the arm.
BARE_DISC = [(x, y) for y in (79, 86) for x in range(108, 118)]
# The platter rim, which is background and never part of the sprite.
PLATTER = [(x, y) for x in (103, 104, 142) for y in (82, 83, 84)]
# The tonearm's headshell: the brightest flat block the sprite has.
HEADSHELL = [(x, y) for y in range(85, 89) for x in range(130, 134)]


def mean_lightness(room: QImage, cells: list[tuple[int, int]]) -> int:
    return sum(room.pixelColor(x, y).lightness() for x, y in cells) // len(cells)


def test_the_record_actually_turns() -> None:
    layout = assets.layout()
    rendered = [compose(Frame(record_frame=i)) for i in range(layout.record_frames)]
    assert all(rendered[0] != other for other in rendered[1:]), (
        "every record frame should put the glint somewhere new"
    )


def test_record_frame_index_wraps_rather_than_raising() -> None:
    layout = assets.layout()
    assert compose(Frame(record_frame=layout.record_frames * 3 + 2)) == compose(
        Frame(record_frame=2)
    )


def test_the_record_only_ever_turns_on_the_platter() -> None:
    """Nothing outside the disc may move. The glint sweeps a radius that once
    overshot the bottom of the record by a pixel, which put a bright dot on the
    platter one frame in twelve and read as a stuck pixel rather than as a
    record."""
    layout = assets.layout()
    x0, y0, x1, y1 = DISC
    still = compose(Frame())
    for i in range(1, layout.record_frames):
        room = compose(Frame(record_frame=i))
        strays = [
            (x, y)
            for y in range(layout.height)
            for x in range(layout.width)
            if not (x0 <= x < x1 and y0 <= y < y1)
            and room.pixelColor(x, y) != still.pixelColor(x, y)
        ]
        assert not strays, f"frame {i} changes pixels off the record: {strays[:6]}"


def test_the_label_stays_on_top_of_the_turning_record() -> None:
    """The glint runs the full width of the disc and the label sits over its
    middle, so the album's colour has to be painted after the record or the
    grooves cross it."""
    layout = assets.layout()
    for i in range(layout.record_frames):
        room = compose(Frame(label_colour=QColor(0, 255, 0), record_frame=i))
        pixel = room.pixelColor(layout.label.x + 5, layout.label.y + 3)
        assert (pixel.red(), pixel.green(), pixel.blue()) == (0, 255, 0), i


def test_the_record_is_lit_by_the_room_it_sits_in() -> None:
    """The record is composited over a background that was graded *after* the
    band's light was folded into it, so the sprite has to carry that same light
    or it will not belong to the room. Drop `make_assets.lit_sprite` and this is
    what catches it.

    Two bands, because they fail differently. At night the wash is a heavy blue
    darkening and the tell is the tonearm: unwashed it stays near-white while the
    room goes dark, which is the lit hole the wash exists to prevent. In the
    evening the wash is a warm lift the platter receives and an unwashed disc
    would not, so the record falls away from the deck it is lying on.
    """
    day, evening, night = (compose(Frame(light=w)) for w in ("day", "evening", "night"))

    bright = mean_lightness(day, HEADSHELL)
    assert mean_lightness(night, HEADSHELL) < bright * 0.75, (
        "the stylus is as bright at midnight as at noon, so the record is not"
        " taking the night wash"
    )

    def gap(room: QImage) -> int:
        return mean_lightness(room, PLATTER) - mean_lightness(room, BARE_DISC)

    assert gap(evening) < gap(day), (
        "the evening wash lifts the platter; the record on it should be lifted too"
    )


def test_dimming_darkens_the_room() -> None:
    def brightness(image: QImage) -> int:
        c = image.pixelColor(160, 30)
        return c.red() + c.green() + c.blue()

    assert brightness(compose(Frame(dim=True))) < brightness(compose(Frame()))


def test_amp_colour_lands_on_the_display() -> None:
    layout = assets.layout()
    room = compose(Frame(amp_colour=QColor(0, 0, 255)))
    pixel = room.pixelColor(layout.amp.x + 1, layout.amp.y + 1)
    assert (pixel.red(), pixel.green(), pixel.blue()) == (0, 0, 255)


def test_the_display_is_dark_with_no_colour() -> None:
    layout = assets.layout()
    room = compose(Frame())
    pixel = room.pixelColor(layout.amp.x + 1, layout.amp.y + 1)
    assert pixel.red() + pixel.green() + pixel.blue() < 180


def test_every_graded_background_loads_at_canvas_size() -> None:
    layout = assets.layout()
    assert set(layout.times_of_day) == {"day", "evening", "night"}
    for when in layout.times_of_day:
        room = assets.background(when)
        assert room.size().toTuple() == (layout.width, layout.height)


@pytest.mark.parametrize("when", ["day", "evening", "night"])
def test_a_flat_wall_is_not_dithered(when: str) -> None:
    """Dithering a flat surface is the one thing this art style cannot survive.

    What is being caught is *speckle*, not colour count. The vignette crosses a
    quantization step somewhere on that wall and leaves a soft band, which is
    correct and invisible; ordered dither leaves pixels that disagree with both
    of their horizontal neighbours, which is not. So this counts those, on a
    patch of far-right wall clear of the lamp, the sleeve's halo and the window.
    """
    room = compose(Frame(light=when))

    def isolated(x: int, y: int) -> bool:
        here = room.pixelColor(x, y)
        return all(
            here != room.pixelColor(x + dx, y + dy)
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1))
        )

    cells = [(x, y) for y in range(105, 123) for x in range(301, 317)]
    speckle = sum(1 for x, y in cells if isolated(x, y))
    # Not zero: where the vignette's band boundary runs diagonally it leaves the
    # odd isolated pixel at a corner, and that is quantization doing its job. An
    # ordered dither puts roughly half the patch in this state, so the two cases
    # are nowhere near each other and the threshold does not need to be delicate.
    assert speckle <= len(cells) * 0.02, (
        f"{when}: {speckle}/{len(cells)} speckled pixels on a flat wall"
    )


def test_the_three_times_of_day_actually_differ() -> None:
    rooms = {when: compose(Frame(light=when)) for when in assets.layout().times_of_day}
    for a, b in (("day", "evening"), ("evening", "night"), ("day", "night")):
        assert rooms[a] != rooms[b], f"{a} and {b} render identically"


@pytest.mark.parametrize(
    ("hour", "expected"),
    [(0, "night"), (6, "night"), (7, "day"), (17, "day"), (18, "evening"),
     (21, "evening"), (22, "night"), (23, "night")],
)
def test_the_clock_picks_the_intended_light(hour: int, expected: str) -> None:
    assert time_of_day(datetime(2026, 8, 16, hour, 30)) == expected


def test_the_amp_pulses_while_playing_and_is_dark_otherwise() -> None:
    green = QColor(0, 200, 0)
    assert amp_colour(green, playing=False, at=0.0) is None
    assert amp_colour(None, playing=True, at=0.0) is None

    lit = amp_colour(green, playing=True, at=0.0)
    dimmed = amp_colour(green, playing=True, at=1.0)
    assert lit is not None and dimmed is not None
    assert dimmed.lightness() < lit.lightness()
