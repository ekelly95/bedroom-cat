"""The cat's clock is its own. Playback nudges it; it never drives it."""

from __future__ import annotations

import random

from bedroom.cat import (
    CALM_PERIOD,
    REACTION_COOLDOWN,
    REACTION_FRAME_SECONDS,
    SKIP_RUN,
    CatMind,
)

FRAMES = 8
CLIPS = {
    "breathe": FRAMES,
    "perk": 16,
    "twitch": 8,
    "glance": 14,
    "thump": 14,
    "stretch": 20,
}


def mind(seed: int = 7) -> CatMind:
    return CatMind(clips=CLIPS, rng=random.Random(seed))


def run(cat: CatMind, seconds: float, *, playing: bool, track=("a",), step: float = 0.1) -> None:
    for _ in range(int(seconds / step)):
        cat.observe(playing, track)
        cat.advance(step)


def settle(cat: CatMind) -> None:
    """Let any reaction finish and the cooldown expire."""
    run(cat, seconds=REACTION_COOLDOWN + 1, playing=True)


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
        assert 0 <= cat.frame < CLIPS[cat.clip]


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
    here maps a playback event onto a specific breathing frame."""
    quiet, excited = mind(3), mind(3)
    excited.nudge(1.0)
    assert quiet.frame == excited.frame


# -- reactions -----------------------------------------------------------


def test_the_cat_rests_until_something_happens() -> None:
    cat = mind()
    for _ in range(200):
        cat.advance(0.1)
        assert cat.clip == "breathe"
        assert not cat.reacting


def test_starting_the_music_perks_the_cat_up() -> None:
    cat = mind()
    cat.observe(playing=True, track_key=("a",))
    assert cat.clip == "perk"


def test_a_reaction_always_finishes_and_hands_back() -> None:
    cat = mind()
    cat.observe(playing=True, track_key=("a",))
    seen = set()
    for _ in range(CLIPS["perk"] + 4):
        seen.add(cat.frame)
        cat.advance(REACTION_FRAME_SECONDS)
    assert seen == set(range(CLIPS["perk"])), "every authored frame should be shown"
    assert cat.clip == "breathe"


def test_frames_stay_in_range_for_every_clip() -> None:
    cat = mind()
    for clip in CLIPS:
        cat._clip = clip if clip != "breathe" else ""
        cat._clip_frame = 0.0
        for _ in range(CLIPS[clip] * 3):
            assert 0 <= cat.frame < CLIPS[cat.clip]
            cat.advance(REACTION_FRAME_SECONDS)


def test_skipping_repeatedly_earns_the_tail() -> None:
    cat = mind()
    settle(cat)
    for i in range(SKIP_RUN):
        cat.observe(playing=True, track_key=(f"t{i}",))
        cat.advance(0.2)
    assert cat.clip == "thump"


def test_one_track_change_never_earns_the_tail() -> None:
    cat = mind()
    settle(cat)
    cat.observe(playing=True, track_key=("b",))
    assert cat.clip != "thump"


def test_reactions_are_rare_rather_than_constant() -> None:
    """A cat that performed on every track change would be a toy."""
    cat = mind()
    settle(cat)
    changes = 200
    reactions = 0
    for i in range(changes):
        cat.observe(playing=True, track_key=(f"t{i}",))
        if cat.reacting:
            reactions += 1
        run(cat, seconds=30, playing=True, track=(f"t{i}",))
    assert 0 < reactions < changes * 0.45, (
        f"{reactions} reactions in {changes} track changes — the cat should "
        "ignore most of them"
    )


def test_nothing_interrupts_a_reaction_except_something_bigger() -> None:
    cat = mind()
    settle(cat)
    assert cat.react("twitch")
    assert not cat.react("twitch"), "equal priority must not restart it"
    assert cat.react("perk"), "the music starting outranks an ear"
    assert cat.clip == "perk"


def test_the_cat_stretches_once_on_its_way_to_sleep() -> None:
    cat = mind()
    stretches = 0
    for _ in range(1200):
        cat.observe(playing=False, track_key=None)
        cat.advance(0.1)
        if cat.clip == "stretch" and cat.frame == 0:
            stretches += 1
    assert stretches == 1
    assert cat.asleep


def test_waking_up_earns_another_stretch_later() -> None:
    def stretched(cat: CatMind, seconds: float, *, playing: bool) -> bool:
        seen = False
        for _ in range(int(seconds / 0.1)):
            cat.observe(playing, ("a",) if playing else None)
            cat.advance(0.1)
            seen = seen or cat.clip == "stretch"
        return seen

    cat = mind()
    assert stretched(cat, 60, playing=False)
    assert stretched(cat, 20, playing=True) is False
    assert stretched(cat, 60, playing=False)


def test_an_unknown_reaction_is_simply_refused() -> None:
    cat = mind()
    assert not cat.react("backflip")
    assert cat.clip == "breathe"
