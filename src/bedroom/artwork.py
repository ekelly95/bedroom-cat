"""Fit whatever artwork Windows hands over into the record sleeve.

Windows publishes wildly different images — a 600x600 square cover from
foobar2000, a 150x83 widescreen video still from a browser. Nothing is ever
cropped: artwork is scaled to fit entirely inside the slot and the leftover
bands take a colour derived from the artwork itself.
"""

from __future__ import annotations

from collections import Counter
from functools import lru_cache

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QImage, QPainter

from .assets_loader import layout


def decode(data: bytes) -> QImage | None:
    image = QImage()
    if not image.loadFromData(data):
        return None
    return image.convertToFormat(QImage.Format.Format_ARGB32)


def dominant_colour(image: QImage) -> QColor:
    """The most common colour, found on a heavily reduced copy.

    Colours are bucketed before counting: a photograph has thousands of nearly
    identical shades, and counting them exactly would return a colour that
    happens to appear twice rather than the one the cover actually reads as.
    """
    small = image.scaled(
        24, 24, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation
    ).convertToFormat(QImage.Format.Format_RGB32)

    buckets: Counter[tuple[int, int, int]] = Counter()
    totals: dict[tuple[int, int, int], list[int]] = {}
    for y in range(small.height()):
        for x in range(small.width()):
            c = small.pixelColor(x, y)
            key = (c.red() >> 4, c.green() >> 4, c.blue() >> 4)
            buckets[key] += 1
            acc = totals.setdefault(key, [0, 0, 0])
            acc[0] += c.red()
            acc[1] += c.green()
            acc[2] += c.blue()

    if not buckets:
        return QColor(90, 90, 96)
    key, count = buckets.most_common(1)[0]
    r, g, b = (v // count for v in totals[key])
    return QColor(r, g, b)


# How bright and how saturated a colour has to be before it can pass for a lit
# panel. Hue is never touched: the hue is the part that says which record is on.
DISPLAY_LIGHTNESS = (0.46, 0.72)
DISPLAY_SATURATION = 0.45


def display_colour(colour: QColor) -> QColor:
    """An album colour made fit for the amp's readout.

    Covers arrive at any brightness. A near-black sleeve left the display looking
    like a dead panel and a near-white one blew it out, so lightness and
    saturation are pulled into a band that reads as lit whatever is playing.
    """
    hue, sat, light, _ = colour.getHslF()
    low, high = DISPLAY_LIGHTNESS
    return QColor.fromHslF(
        max(0.0, hue),
        min(1.0, max(DISPLAY_SATURATION, sat)),
        min(high, max(low, light)),
    )


def backdrop(cover: QImage, size: int) -> QImage:
    """A soft wash of the artwork's own colours, filling the whole slot.

    Replaces a flat band colour, which failed badly on dark artwork: a music
    video thumbnail is mostly near-black, so near-black bands around a small
    dark picture made the sleeve read as one blank square.

    Reduced to a handful of blocks and blown back up, so it stays chunky enough
    to belong in pixel art rather than looking like a photographic blur, then
    darkened so the crisp artwork on top is clearly the subject.
    """
    tiny = cover.scaled(
        5, 5, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation
    )
    wash = tiny.scaled(
        size,
        size,
        Qt.AspectRatioMode.IgnoreAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    ).convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)

    painter = QPainter(wash)
    painter.fillRect(wash.rect(), QColor(10, 8, 14, 110))
    painter.end()
    return wash


def grade_sleeve(slot: QImage, when: str) -> QImage:
    """Make live album art belong to the room it is dropped into.

    The design review's sharpest criticism was that the one element changing per
    track sat at the same brightness as its own frame. Gain and saturation fix
    that; quantizing to the room's step count stops a photograph reading as a
    photograph pasted onto pixel art; and the band's wash dims the sleeve with
    the room, which used to happen because a full-canvas light overlay covered
    the artwork too.

    The numbers come from `layout.json`, authored beside the art.

    **Deliberately not dithered**, unlike the room. Ordered dither across a
    52-pixel cover is noise over the only part of the frame carrying real
    information; recognising the record beats matching the shader.
    """
    g = layout().sleeve_grade[when]
    gain, sat, steps, dim = g["gain"], g["saturation"], g["steps"], g["dim"]
    wr, wg, wb, wa = g["wash"]
    alpha = wa / 255

    out = slot.convertToFormat(QImage.Format.Format_ARGB32)
    for y in range(out.height()):
        for x in range(out.width()):
            c = out.pixelColor(x, y)
            r, g_, b = c.redF(), c.greenF(), c.blueF()
            r = r * (1 - alpha) + wr / 255 * alpha
            g_ = g_ * (1 - alpha) + wg / 255 * alpha
            b = b * (1 - alpha) + wb / 255 * alpha

            lum = 0.299 * r + 0.587 * g_ + 0.114 * b
            channels = [
                round(min(1.0, max(0.0, (lum + (v - lum) * sat) * gain * dim)) * steps)
                * 255
                // steps
                for v in (r, g_, b)
            ]
            out.setPixelColor(x, y, QColor(*channels))
    return out


def fit_to_sleeve(cover: QImage, size: int) -> QImage:
    """Scale to fit entirely inside a square slot, never cropping.

    Smooth scaling on the way down — nearest-neighbour would make a 600x600
    photographic cover jagged and noisy. Nearest-neighbour belongs at the other
    end of the pipeline, when the finished room is enlarged to 2x or more.
    """
    fitted = cover.scaled(
        size,
        size,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )

    slot = backdrop(cover, size)
    ox = (size - fitted.width()) // 2
    oy = (size - fitted.height()) // 2

    painter = QPainter(slot)
    painter.drawImage(ox, oy, fitted)
    if fitted.width() != size or fitted.height() != size:
        # A hairline between artwork and wash, so the edge of the picture is
        # always findable even when both are dark.
        painter.setPen(QColor(235, 230, 220, 150))
        painter.drawRect(ox - 1, oy - 1, fitted.width() + 1, fitted.height() + 1)
    painter.end()
    return slot


class ArtworkCache:
    """Decoded, fitted, graded artwork keyed on track identity and time of day.

    Windows re-publishes the same thumbnail on every poll, so without this the
    app would decode, rescale and grade an image once a second forever. The band
    is part of the key because the sleeve is graded to match the room: there are
    only three of them, so a cover is reworked when the room moves from day to
    evening to night and at no other time.
    """

    def __init__(self, size: int, capacity: int = 8) -> None:
        self._size = size
        self._capacity = capacity
        # `None` is a remembered failure, not an absence. Artwork that will not
        # decode is still republished on every poll, and without this the app
        # tried to decode the same broken thumbnail eight times a second for as
        # long as the track was playing.
        self._entries: dict[tuple, tuple[QImage, QColor] | None] = {}
        self._order: list[tuple] = []

    def get(self, key: tuple, data: bytes | None, when: str) -> tuple[QImage, QColor] | None:
        if data is None:
            return None
        entry_key = (when, key)
        if entry_key in self._entries:
            return self._entries[entry_key]

        cover = decode(data)
        entry = None
        if cover is not None:
            # The dominant colour is sampled from the *original* cover, not the
            # graded one: it drives the record label and the amp, and those
            # should follow the record rather than the hour.
            entry = (
                grade_sleeve(fit_to_sleeve(cover, self._size), when),
                dominant_colour(cover),
            )

        self._entries[entry_key] = entry
        self._order.append(entry_key)
        while len(self._order) > self._capacity:
            self._entries.pop(self._order.pop(0), None)
        return entry

    def __len__(self) -> int:
        return len(self._entries)


@lru_cache(maxsize=16)
def fit_static(path: str, size: int, when: str) -> tuple[QImage, QColor]:
    """For artwork that ships with the app, such as demo covers."""
    cover = QImage(path).convertToFormat(QImage.Format.Format_ARGB32)
    return grade_sleeve(fit_to_sleeve(cover, size), when), dominant_colour(cover)
