"""The artwork rule: fit entirely inside the sleeve, never crop."""

from __future__ import annotations

import pytest
from PySide6.QtGui import QColor, QImage, QPainter

from bedroom.artwork import (
    DISPLAY_LIGHTNESS,
    ArtworkCache,
    display_colour,
    dominant_colour,
    fit_to_sleeve,
    grade_sleeve,
)

SIZE = 52


def solid(width: int, height: int, colour: QColor) -> QImage:
    image = QImage(width, height, QImage.Format.Format_ARGB32)
    image.fill(colour)
    return image


def halves(width: int, height: int, left: QColor, right: QColor) -> QImage:
    image = solid(width, height, left)
    painter = QPainter(image)
    painter.fillRect(width // 2, 0, width - width // 2, height, right)
    painter.end()
    return image


def test_dominant_colour_of_a_solid_cover_is_that_colour() -> None:
    found = dominant_colour(solid(64, 64, QColor(200, 40, 60)))
    assert abs(found.red() - 200) <= 6
    assert abs(found.green() - 40) <= 6
    assert abs(found.blue() - 60) <= 6


def test_dominant_colour_picks_the_majority_not_an_outlier() -> None:
    cover = solid(64, 64, QColor(30, 120, 200))
    painter = QPainter(cover)
    painter.fillRect(0, 0, 8, 8, QColor(255, 255, 0))
    painter.end()
    found = dominant_colour(cover)
    assert found.blue() > found.red()


@pytest.mark.parametrize(("w", "h"), [(300, 300), (600, 600), (150, 83), (83, 150), (1, 1)])
def test_fitted_artwork_always_fills_the_slot_exactly(w: int, h: int) -> None:
    fitted = fit_to_sleeve(solid(w, h, QColor(120, 90, 60)), SIZE)
    assert fitted.size().toTuple() == (SIZE, SIZE)


def test_a_square_cover_leaves_no_bands() -> None:
    fitted = fit_to_sleeve(solid(300, 300, QColor(200, 40, 60)), SIZE)
    corner = fitted.pixelColor(1, 1)
    assert abs(corner.red() - 200) <= 8, "a square cover should reach the slot corners"


def test_a_widescreen_cover_is_letterboxed_not_cropped() -> None:
    # Distinct halves, so a centre-crop would be visible as a lost edge.
    cover = halves(150, 83, QColor(220, 30, 30), QColor(30, 30, 220))
    fitted = fit_to_sleeve(cover, SIZE)

    middle = SIZE // 2
    assert fitted.pixelColor(6, middle).red() > fitted.pixelColor(6, middle).blue()
    assert fitted.pixelColor(SIZE - 7, middle).blue() > fitted.pixelColor(SIZE - 7, middle).red()


def test_the_wash_behind_a_widescreen_cover_carries_its_colours() -> None:
    """A flat band failed on dark artwork — near-black bands round a small dark
    picture read as one blank square. The wash must come from the artwork."""
    cover = halves(150, 83, QColor(220, 30, 30), QColor(30, 30, 220))
    fitted = fit_to_sleeve(cover, SIZE)

    left_band = fitted.pixelColor(6, 1)
    right_band = fitted.pixelColor(SIZE - 7, 1)
    assert left_band.red() > left_band.blue(), "the wash should be red above the red half"
    assert right_band.blue() > right_band.red(), "and blue above the blue half"


def test_a_dark_cover_still_leaves_a_findable_picture_edge() -> None:
    """The failure that prompted the wash: a dark music-video thumbnail."""
    cover = solid(150, 83, QColor(8, 8, 12))
    fitted = fit_to_sleeve(cover, SIZE)

    # Scan for the hairline rather than deriving its row: Qt's rounding decides
    # whether the picture is 28 or 29 rows tall, and the test should not care.
    column = SIZE // 2
    brightest = max(fitted.pixelColor(column, y).lightness() for y in range(SIZE // 2))
    inside = fitted.pixelColor(column, SIZE // 2).lightness()
    assert brightest > inside + 30, (
        "a dark cover needs a visible hairline or the sleeve reads as blank"
    )


def test_a_tall_cover_is_pillarboxed() -> None:
    fitted = fit_to_sleeve(solid(83, 150, QColor(40, 200, 90)), SIZE)
    side = fitted.pixelColor(1, SIZE // 2)
    centre = fitted.pixelColor(SIZE // 2, SIZE // 2)
    assert centre.green() > side.green(), "the artwork should be brighter than its bands"


def _png(colour: QColor, size: int = 64) -> bytes:
    from PySide6.QtCore import QBuffer

    buffer = QBuffer()
    buffer.open(QBuffer.OpenModeFlag.WriteOnly)
    solid(size, size, colour).save(buffer, "PNG")
    return bytes(buffer.data())


def test_cache_returns_the_same_object_for_the_same_track() -> None:
    cache = ArtworkCache(SIZE)
    data = _png(QColor(90, 140, 200))
    first = cache.get(("app", "t", "a", "al"), data, "day")
    second = cache.get(("app", "t", "a", "al"), data, "day")
    assert first is second, "re-decoding every poll is the thing this exists to avoid"


def test_cache_separates_different_tracks() -> None:
    cache = ArtworkCache(SIZE)
    one = cache.get(("app", "one", "a", "al"), _png(QColor(200, 40, 40)), "day")
    two = cache.get(("app", "two", "a", "al"), _png(QColor(40, 40, 200)), "day")
    assert one is not two
    assert len(cache) == 2


def test_cache_evicts_the_oldest_entry_past_capacity() -> None:
    cache = ArtworkCache(SIZE, capacity=2)
    for i in range(3):
        cache.get(("app", f"t{i}", "", ""), _png(QColor(10 * i + 20, 100, 100)), "day")
    assert len(cache) == 2


def test_cache_ignores_a_track_with_no_artwork() -> None:
    cache = ArtworkCache(SIZE)
    assert cache.get(("app", "t", "a", "al"), None, "day") is None
    assert len(cache) == 0


def test_cache_survives_bytes_that_are_not_an_image() -> None:
    cache = ArtworkCache(SIZE)
    assert cache.get(("app", "t", "a", "al"), b"this is not a picture", "day") is None


def test_a_thumbnail_that_will_not_decode_is_only_decoded_once(monkeypatch) -> None:
    """A failure has to be remembered, not just survived.

    Windows republishes the same thumbnail on every poll and the room redraws
    eight times a second, so artwork that cannot be decoded was being decoded
    again on every tick for as long as the track played. The cost of the
    successful path is exactly why this cache exists; the failing path was
    getting none of the benefit.
    """
    from bedroom import artwork

    calls = []
    real = artwork.decode

    def counted(data: bytes):
        calls.append(data)
        return real(data)

    monkeypatch.setattr(artwork, "decode", counted)

    cache = ArtworkCache(SIZE)
    for _ in range(5):
        assert cache.get(("app", "t", "a", "al"), b"not a picture", "day") is None
    assert len(calls) == 1, f"decoded {len(calls)} times, should have been remembered"


def test_a_remembered_failure_still_counts_against_capacity() -> None:
    """Otherwise a run of broken covers grows the cache without bound."""
    cache = ArtworkCache(SIZE, capacity=2)
    for i in range(3):
        cache.get(("app", f"t{i}", "", ""), b"not a picture", "day")
    assert len(cache) == 2


@pytest.mark.parametrize(
    "colour",
    [QColor(0, 0, 0), QColor(255, 255, 255), QColor(4, 6, 30), QColor(250, 248, 240)],
)
def test_any_cover_colour_can_light_the_display(colour: QColor) -> None:
    low, high = DISPLAY_LIGHTNESS
    assert low - 0.01 <= display_colour(colour).lightnessF() <= high + 0.01


def test_the_sleeve_grade_saturates_the_artwork() -> None:
    """The review's sharpest point: the one thing that changes per track sat at
    the same brightness as its own frame.

    Saturation is what is asserted rather than brightness. The gain is 14% and
    the vignette across the sleeve takes back 8% of it, which nets out to less
    than one of the room's sixteen value steps — so a flat colour genuinely
    cannot move, and a brightness assertion here would be testing the rounding.
    The lift that matters is relative: the room around the sleeve is pushed down
    by a shadow tint the sleeve is exempt from.
    """
    middle = SIZE // 2
    cover = fit_to_sleeve(solid(120, 120, QColor(180, 90, 70)), SIZE)
    before = cover.pixelColor(middle, middle)
    after = grade_sleeve(cover, "day").pixelColor(middle, middle)
    assert after.saturation() > before.saturation()


def test_the_sleeve_dims_with_the_room() -> None:
    """It used to be dimmed by a light overlay drawn across the whole canvas. Now
    that the overlay is baked into the background, the sleeve has to do it itself
    or it goes back to reading as a sticker at midnight."""
    cover = fit_to_sleeve(solid(120, 120, QColor(160, 150, 140)), SIZE)
    middle = SIZE // 2
    lightness = {
        when: grade_sleeve(cover, when).pixelColor(middle, middle).lightness()
        for when in ("day", "evening", "night")
    }
    assert lightness["night"] < lightness["evening"] < lightness["day"]


def test_the_sleeve_grade_keeps_covers_apart() -> None:
    """Quantizing to the room's palette must not flatten two records into one."""
    one = grade_sleeve(fit_to_sleeve(solid(120, 120, QColor(200, 60, 40)), SIZE), "day")
    two = grade_sleeve(fit_to_sleeve(solid(120, 120, QColor(40, 90, 200)), SIZE), "day")
    assert one != two
