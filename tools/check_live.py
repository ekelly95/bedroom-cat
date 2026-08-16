"""Check the whole app against whatever is playing right now.

Reads one live update, renders the frame the room would draw, and then exercises
the transport by toggling play/pause and putting it straight back. Run it once
per player.

    uv run python tools/check_live.py

The transport check really does pause and resume your music, and restores the
state it found. Pass --no-transport to skip it.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QCoreApplication, QEventLoop, QTimer  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402

from bedroom import assets_loader as assets  # noqa: E402
from bedroom.artwork import ArtworkCache, display_colour  # noqa: E402
from bedroom.model import NowPlaying, PlaybackState  # noqa: E402
from bedroom.scene import Frame, amp_colour, compose, time_of_day  # noqa: E402
from bedroom.source_windows import WindowsSource  # noqa: E402

PROOF = Path("docs/proof")


class Checker:
    def __init__(self, do_transport: bool, follow: str | None = None) -> None:
        self.source = WindowsSource(poll_seconds=0.4)
        self.source.set_override(follow)
        self.cache = ArtworkCache(assets.layout().sleeve.width)
        self.latest: NowPlaying | None = None
        self.do_transport = do_transport
        self.results: list[tuple[bool, str]] = []
        self.source.updated.connect(self._on_update)
        self.source.failed.connect(lambda m: print(f"  [worker] {m}", file=sys.stderr))

    def _on_update(self, now: NowPlaying | None) -> None:
        self.latest = now

    def check(self, ok: bool, label: str) -> None:
        self.results.append((ok, label))
        print(f"  {'PASS' if ok else 'FAIL'}  {label}")

    def wait(self, ms: int) -> None:
        loop = QEventLoop()
        QTimer.singleShot(ms, loop.quit)
        loop.exec()

    def wait_for_update(self, timeout_ms: int = 8000) -> bool:
        waited = 0
        while self.latest is None and waited < timeout_ms:
            self.wait(200)
            waited += 200
        return self.latest is not None

    def run(self) -> int:
        self.source.start()
        if not self.wait_for_update():
            print("No media session appeared. Start playback somewhere first.")
            self.source.stop()
            return 1

        now = self.latest
        assert now is not None
        app = now.app_id.removesuffix(".exe")
        print(f"\n{app}\n{'-' * len(app)}")
        print(f"  title      {now.title or '(empty)'}")
        print(f"  artist     {now.artist or '(empty)'}")
        print(f"  album      {now.album or '(empty)'}")
        print(f"  state      {now.state.value}")
        c = now.controls
        print(
            f"  controls   play={c.play} pause={c.pause} next={c.next} prev={c.previous}"
        )
        print()

        self.check(bool(now.title), "reports a title")
        self.check(now.state is not PlaybackState.STOPPED, "reports an active playback state")

        # One band for the whole frame: the sleeve is graded to match the room it
        # is dropped into, so the cache is keyed on the hour as well as the track.
        # Nothing in the suite can reach this file — it needs a live Windows
        # session — so this call going stale is only ever caught by running it.
        when = time_of_day()
        entry = self.cache.get(now.track_key, now.artwork, when)
        if now.artwork is None:
            self.check(False, "publishes artwork")
        else:
            self.check(True, f"publishes artwork ({len(now.artwork):,} bytes)")
            self.check(entry is not None, "artwork decodes and fits the sleeve")
            if entry is not None:
                fitted, colour = entry
                size = assets.layout().sleeve.width
                self.check(
                    fitted.size().toTuple() == (size, size),
                    f"fitted artwork fills the {size}x{size} slot exactly",
                )
                print(f"         label colour {colour.name()}")

        artwork = colour = None
        if entry is not None:
            artwork, colour = entry
        # The same frame the app builds, field for field, so this proof cannot
        # drift away from what the window actually draws.
        playing = now.state.is_active
        room = compose(
            Frame(
                artwork=artwork,
                label_colour=colour,
                amp_colour=amp_colour(
                    display_colour(colour) if colour is not None else None,
                    playing=playing,
                    at=0.0,
                ),
                # A still, so the record is parked at frame 0 rather than caught
                # mid-turn. It is still the sprite that draws it.
                record_frame=0,
                light=when,
                dim=not playing,
                playing=playing,
            )
        )
        PROOF.mkdir(parents=True, exist_ok=True)
        out = PROOF / f"live-{app.lower()}.png"
        room.scaled(room.width() * 2, room.height() * 2).save(str(out))
        print(f"         rendered -> {out}")

        if self.do_transport and (c.play or c.pause):
            self._check_transport(now.state)
        elif self.do_transport:
            self.check(False, "player accepts play/pause (it reports neither as available)")

        self.source.stop()
        failures = [label for ok, label in self.results if not ok]
        print(f"\n{len(self.results) - len(failures)}/{len(self.results)} checks passed")
        return 1 if failures else 0

    def _check_transport(self, original: PlaybackState) -> None:
        print("\n  toggling playback (and putting it back)")
        self.source.send("playpause")
        self.wait(1800)
        flipped = self.latest.state if self.latest else None
        moved = flipped.value if flipped else "?"
        self.check(
            flipped is not original,
            f"play/pause changed the state ({original.value} -> {moved})",
        )

        self.source.send("playpause")
        self.wait(1800)
        restored = self.latest.state if self.latest else None
        self.check(restored is original, f"playback restored to {original.value}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--no-transport",
        action="store_true",
        help="skip the play/pause round trip",
    )
    args = parser.parse_args()

    QGuiApplication.instance() or QGuiApplication([])
    result = Checker(do_transport=not args.no_transport).run()
    QCoreApplication.processEvents()
    return result


if __name__ == "__main__":
    sys.exit(main())
