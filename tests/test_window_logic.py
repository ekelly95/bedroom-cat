"""Zoom fitting and the window's title text."""

from __future__ import annotations

import pytest

from bedroom.__main__ import describe
from bedroom.model import NowPlaying, PlaybackState
from bedroom.window import ZOOM_LEVELS, largest_zoom_that_fits, screen_scale

CANVAS = (320, 200)


@pytest.mark.parametrize(
    ("available", "expected"),
    [
        ((3840, 2160), 4),
        ((1920, 1080), 4),
        ((1280, 800), 4),
        ((1100, 700), 3),
        ((800, 500), 2),
    ],
)
def test_zoom_picks_the_largest_whole_number_that_fits(available, expected) -> None:
    assert largest_zoom_that_fits(CANVAS, available) == expected


def test_zoom_never_goes_fractional_on_a_tiny_screen() -> None:
    """Better to overflow slightly than to blur every edge in the art."""
    assert largest_zoom_that_fits(CANVAS, (100, 100)) == min(ZOOM_LEVELS)


def test_zoom_result_is_always_an_offered_level() -> None:
    for width in range(320, 2000, 137):
        assert largest_zoom_that_fits(CANVAS, (width, width)) in ZOOM_LEVELS


def test_an_unscaled_display_gets_exactly_the_zoom_it_asked_for() -> None:
    for level in ZOOM_LEVELS:
        assert screen_scale(level, 1.0) == level


@pytest.mark.parametrize(
    ("zoom", "dpr", "expected"),
    [
        (2, 1.5, 3),  # 150%: the even multipliers land exactly
        (3, 1.5, 4),  # 4.5 is not a number of pixels; 4 is
        (4, 1.5, 6),
        (2, 1.25, 2),  # 125%: 2.5 rounds down rather than overhanging
        (4, 1.25, 5),
        (3, 2.0, 6),
    ],
)
def test_the_screen_scale_is_always_a_whole_number(zoom, dpr, expected) -> None:
    """The bug this exists to stop.

    A logical pixel is not a screen pixel. At 150% a 3x room was being drawn at
    4.5 screen pixels per art pixel, which comes out as some columns four wide
    and some five — hard-edged, so not blurry, but visibly irregular anywhere
    the art has a repeating pattern.
    """
    assert screen_scale(zoom, dpr) == expected


def test_the_scale_never_collapses_to_nothing() -> None:
    """A display scaled below 100% must still draw the room at least life size."""
    assert screen_scale(2, 0.4) == 1


def test_title_says_nothing_playing_when_quiet() -> None:
    assert describe(None) == "The Bedroom — nothing playing"


def test_title_shows_track_artist_and_source() -> None:
    now = NowPlaying(
        app_id="Spotify.exe",
        title="Shut It Down",
        artist="Drake",
        state=PlaybackState.PLAYING,
    )
    assert describe(now) == "▶ Shut It Down — Drake  ·  Spotify"


def test_title_marks_a_paused_track() -> None:
    now = NowPlaying(app_id="Brave", title="Money Trees", state=PlaybackState.PAUSED)
    assert describe(now).startswith("❚❚ Money Trees")


def test_title_copes_with_a_player_reporting_no_artist() -> None:
    now = NowPlaying(app_id="foobar2000.exe", title="1/1", state=PlaybackState.PLAYING)
    assert describe(now) == "▶ 1/1  ·  foobar2000"


def test_title_copes_with_a_player_reporting_nothing_at_all() -> None:
    now = NowPlaying(app_id="Brave", state=PlaybackState.PLAYING)
    assert "(no title)" in describe(now)
