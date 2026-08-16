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


def band_colour(colour: QColor) -> QColor:
    """Darkened, so the artwork stays the brightest thing inside the sleeve."""
    return QColor(
        int(colour.red() * 0.55), int(colour.green() * 0.55), int(colour.blue() * 0.55)
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
    """Decoded, fitted artwork keyed on track identity.

    Windows re-publishes the same thumbnail on every poll, so without this the
    app would decode and rescale an image once a second forever.
    """

    def __init__(self, size: int, capacity: int = 8) -> None:
        self._size = size
        self._capacity = capacity
        self._entries: dict[tuple, tuple[QImage, QColor]] = {}
        self._order: list[tuple] = []

    def get(self, key: tuple, data: bytes | None) -> tuple[QImage, QColor] | None:
        if data is None:
            return None
        if key in self._entries:
            return self._entries[key]

        cover = decode(data)
        if cover is None:
            return None
        entry = (fit_to_sleeve(cover, self._size), dominant_colour(cover))

        self._entries[key] = entry
        self._order.append(key)
        while len(self._order) > self._capacity:
            self._entries.pop(self._order.pop(0), None)
        return entry

    def __len__(self) -> int:
        return len(self._entries)


@lru_cache(maxsize=8)
def fit_static(path: str, size: int) -> tuple[QImage, QColor]:
    """For artwork that ships with the app, such as demo covers."""
    cover = QImage(path).convertToFormat(QImage.Format.Format_ARGB32)
    return fit_to_sleeve(cover, size), dominant_colour(cover)
