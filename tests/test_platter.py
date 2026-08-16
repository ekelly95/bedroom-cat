"""The record follows playback and nothing else, but it does it with mass."""

from __future__ import annotations

from bedroom.platter import FRAME_SECONDS, Platter

FRAMES = 12
# One drawn frame of the app, so a tick here is a tick there.
TICK = FRAME_SECONDS


def platter() -> Platter:
    return Platter(frames=FRAMES)


def run(deck: Platter, seconds: float, *, playing: bool) -> list[int]:
    """Advance in real ticks and report the frame drawn at each one."""
    drawn = []
    for _ in range(round(seconds / TICK)):
        deck.advance(TICK, playing=playing)
        drawn.append(deck.frame)
    return drawn


def travel(deck: Platter, ticks: int, *, playing: bool) -> int:
    """How many frames the record moves through over `ticks` ticks."""
    moved = 0
    for _ in range(ticks):
        before = deck.frame
        deck.advance(TICK, playing=playing)
        moved += (deck.frame - before) % FRAMES
    return moved


def up_to_speed() -> Platter:
    deck = platter()
    run(deck, 2.0, playing=True)
    return deck


def test_a_record_that_has_never_played_does_not_move() -> None:
    deck = platter()
    assert set(run(deck, 5.0, playing=False)) == {0}
    assert not deck.spinning


def test_playing_turns_the_record() -> None:
    seen = set(run(platter(), 3.0, playing=True))
    assert len(seen) == FRAMES, (
        f"a couple of turns should visit every authored frame, saw {sorted(seen)}"
    )


def test_it_settles_at_one_authored_frame_per_tick() -> None:
    """The pace the art was drawn for: one baked frame per drawn frame, the same
    rule the cat's reaction clips run on. Off that pace the glint either stutters
    (a frame drawn twice) or skips (a frame never drawn at all). Twenty-three
    rather than a flat twenty-four because the record parks mid-frame as often as
    not, and the last fraction of the last one falls outside the window.
    """
    deck = up_to_speed()
    assert travel(deck, 24, playing=True) in (23, 24)


def test_playing_does_not_snap_straight_to_speed() -> None:
    """A platter takes a moment. Coming up to speed instantly is the one thing
    here that would make the room look like software rather than furniture."""
    assert travel(platter(), 3, playing=True) < 2, "three ticks is no run-up at all"


def test_it_is_at_speed_within_a_second() -> None:
    deck = platter()
    run(deck, 1.0, playing=True)
    assert travel(deck, 24, playing=True) >= 22


def test_pausing_coasts_rather_than_stopping_dead() -> None:
    deck = up_to_speed()
    assert len(set(run(deck, 0.5, playing=False))) > 1, (
        "the record should still be turning half a second after the music stopped"
    )


def test_the_coast_ends_in_a_full_stop() -> None:
    """Not merely slow: stopped. An exponential decay never actually arrives, so
    the model takes the last of the speed away rather than creeping forever."""
    deck = up_to_speed()
    run(deck, 4.0, playing=False)
    assert not deck.spinning
    assert len(set(run(deck, 30.0, playing=False))) == 1


def test_it_stops_wherever_it_happened_to_be() -> None:
    """No home position. Where it parks depends only on how long it ran, which is
    what stops the record looking like it is being reset between tracks."""
    stops = set()
    for seconds in (1.0, 1.3, 1.6, 2.1):
        deck = platter()
        run(deck, seconds, playing=True)
        run(deck, 4.0, playing=False)
        stops.add(deck.frame)
    assert len(stops) > 1, f"the record always parks at {stops}"


def test_it_picks_up_from_where_it_stopped() -> None:
    deck = up_to_speed()
    run(deck, 4.0, playing=False)
    stopped = deck.frame
    resumed = run(deck, 0.6, playing=True)
    assert (resumed[0] - stopped) % FRAMES <= 1, "the record jumped when the music came back"
    assert resumed[-1] != stopped


def test_the_frame_is_always_a_frame_that_exists() -> None:
    deck = platter()
    for i in range(4000):
        deck.advance(0.07, playing=i % 500 < 300)
        assert 0 <= deck.frame < FRAMES
