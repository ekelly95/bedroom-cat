"""The cat's clock is its own. Playback nudges it; it never drives it."""

from __future__ import annotations

import random

from bedroom.cat import CALM_PERIOD, CatMind

FRAMES = 8


def mind(seed: int = 7) -> CatMind:
    return CatMind(frames=FRAMES, rng=random.Random(seed))


def run(cat: CatMind, seconds: float, *, playing: bool, track=("a",), step: float = 0.1) -> None:
    for _ in range(int(seconds / step)):
        cat.observe(playing, track)
        cat.advance(step)


def test_the_cat_breathes_with_no_music_at_all() -> None:
    """The quiet room is still alive. This is the whole point of the cat having
    its own clock rather than the music's."""
    cat = mind()
    seen = set()
    for _ in range(120):
        cat.advance(0.1)
        seen.add(cat.frame)
    assert len(seen) > 1


def test_frames_stay_in_range() -> None:
    cat = mind()
    for _ in range(2000):
        cat.advance(0.07)
        assert 0 <= cat.frame < FRAMES


def test_starting_music_quickens_the_breathing() -> None:
    cat = mind()
    calm = cat.period
    cat.observe(playing=True, track_key=("a",))
    cat.advance(0.01)
    assert cat.excitement > 0.5
    # The shorter period only takes effect on the next breath.
    while cat.period == calm:
        cat.advance(0.1)
    assert cat.period < CALM_PERIOD


def test_excitement_decays_back_to_the_cats_own_pace() -> None:
    cat = mind()
    cat.observe(playing=True, track_key=("a",))
    assert cat.excitement > 0.9
    run(cat, seconds=20, playing=True)
    assert cat.excitement < 0.05, "a reaction must resolve, not become a mode"


def test_a_track_change_nudges_but_less_than_starting_does() -> None:
    starting = mind()
    starting.observe(playing=True, track_key=("a",))

    changing = mind()
    changing.observe(playing=True, track_key=("a",))
    run(changing, seconds=30, playing=True, track=("a",))
    changing.observe(playing=True, track_key=("b",))

    assert 0 < changing.excitement < starting.excitement


def test_the_same_track_reported_repeatedly_does_not_re_excite() -> None:
    cat = mind()
    run(cat, seconds=30, playing=True, track=("a",))
    settled = cat.excitement
    cat.observe(playing=True, track_key=("a",))
    assert cat.excitement == settled


def test_pausing_makes_the_cat_drowsy_and_then_asleep() -> None:
    cat = mind()
    run(cat, seconds=5, playing=True)
    assert not cat.asleep
    run(cat, seconds=60, playing=False)
    assert cat.asleep
    assert cat.period > CALM_PERIOD


def test_the_cat_wakes_faster_than_it_falls_asleep() -> None:
    cat = mind()
    run(cat, seconds=60, playing=False)
    assert cat.asleep
    run(cat, seconds=6, playing=True)
    assert not cat.asleep


def test_breaths_are_never_identical() -> None:
    """Jittered per cycle, so the rhythm cannot read as metronomic."""
    cat = mind()
    periods = []
    for _ in range(4000):
        before = cat.period
        cat.advance(0.05)
        if cat.period != before:
            periods.append(cat.period)
    assert len(periods) >= 5
    assert len(set(periods)) == len(periods)


def test_the_period_never_collapses_to_nothing() -> None:
    cat = mind()
    for _ in range(50):
        cat.nudge(1.0)
        cat.advance(0.1)
    assert cat.period >= 0.6


def test_the_clock_is_deterministic_for_a_given_seed() -> None:
    a, b = mind(11), mind(11)
    for _ in range(500):
        a.advance(0.09)
        b.advance(0.09)
    assert a.frame == b.frame
    assert a.period == b.period


def test_advancing_by_nothing_changes_nothing() -> None:
    cat = mind()
    cat.advance(0.5)
    frame, period = cat.frame, cat.period
    cat.advance(0)
    cat.advance(-1)
    assert (cat.frame, cat.period) == (frame, period)


def test_playback_never_sets_the_frame_directly() -> None:
    """A quiet cat and an excited cat differ in pace, not in position — nothing
    here maps a playback event onto a specific frame."""
    quiet, excited = mind(3), mind(3)
    excited.nudge(1.0)
    assert quiet.frame == excited.frame
