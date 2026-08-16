"""The session-selection policy, tested without touching Windows.

The behaviours pinned here were measured from real players — see the table in
README.md. They are the reason the policy is what it is.
"""

from __future__ import annotations

from bedroom.model import PlaybackState, SessionInfo
from bedroom.source_windows import choose_session


def session(app_id: str, state=PlaybackState.PLAYING, current=False, title="") -> SessionInfo:
    return SessionInfo(app_id=app_id, title=title, state=state, is_current=current)


def test_no_sessions_means_no_choice() -> None:
    assert choose_session([], None) is None


def test_the_only_session_wins_even_if_windows_marks_none_current() -> None:
    only = session("Spotify.exe", current=False)
    assert choose_session([only], None) is only


def test_windows_current_marker_wins_over_enumeration_order() -> None:
    """The case that rules out 'first session reporting PLAYING'.

    Brave started while Spotify was already playing; Windows moved the marker
    and enumeration order would have kept Spotify.
    """
    sessions = [
        session("foobar2000.exe", PlaybackState.STOPPED),
        session("Spotify.exe", PlaybackState.PLAYING),
        session("Brave", PlaybackState.PLAYING, current=True),
    ]
    assert choose_session(sessions, None).app_id == "Brave"


def test_current_marker_is_followed_even_when_it_is_paused() -> None:
    """With nothing playing the marker stays put, and so does the room —
    it must not flicker to a different player or to empty."""
    sessions = [
        session("Spotify.exe", PlaybackState.PAUSED, current=True),
        session("Brave", PlaybackState.PAUSED),
    ]
    assert choose_session(sessions, None).app_id == "Spotify.exe"


def test_override_beats_the_current_marker() -> None:
    """The stale case: foobar2000 kept the marker while a resumed Brave tab
    played. This is the escape hatch for exactly that."""
    sessions = [
        session("foobar2000.exe", PlaybackState.PLAYING, current=True),
        session("Brave", PlaybackState.PLAYING),
    ]
    assert choose_session(sessions, "Brave").app_id == "Brave"


def test_override_is_ignored_once_that_player_is_gone() -> None:
    sessions = [session("Spotify.exe", PlaybackState.PLAYING, current=True)]
    assert choose_session(sessions, "Brave").app_id == "Spotify.exe"


def test_override_for_a_missing_player_does_not_blank_the_room() -> None:
    assert choose_session([], "Brave") is None


def test_falls_back_to_the_first_session_when_windows_names_none() -> None:
    sessions = [
        session("Spotify.exe", PlaybackState.PAUSED),
        session("Brave", PlaybackState.PAUSED),
    ]
    assert choose_session(sessions, None).app_id == "Spotify.exe"


def test_session_label_drops_the_exe_suffix() -> None:
    assert session("Spotify.exe", title="Shut It Down").label == "Spotify — Shut It Down"
    assert session("Brave").label == "Brave"
