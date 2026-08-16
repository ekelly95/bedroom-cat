"""Compose one frame from whatever Windows is publishing right now, and save it.

An end-to-end check of the whole chain — worker thread, artwork bytes, fitting,
cache, composition — without needing to look at a live window.

    uv run python tools/render_live.py docs/proof/live.png
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QCoreApplication, QTimer  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402

from bedroom import assets_loader as assets  # noqa: E402
from bedroom.artwork import ArtworkCache, display_colour  # noqa: E402
from bedroom.scene import Frame, amp_colour, compose, time_of_day  # noqa: E402
from bedroom.source_windows import WindowsSource  # noqa: E402


def main() -> int:
    destination = Path(sys.argv[1] if len(sys.argv) > 1 else "docs/proof/live.png")
    app = QGuiApplication.instance() or QGuiApplication([])

    layout = assets.layout()
    cache = ArtworkCache(layout.sleeve.width)
    source = WindowsSource(poll_seconds=0.4)
    seen: dict[str, object] = {}

    def on_update(now) -> None:
        if now is None or seen.get("done"):
            return
        seen["done"] = True
        # One band for the whole frame: the sleeve is graded to match the room it
        # is dropped into, so the cache is keyed on the hour as well as the track.
        # Nothing in the suite can reach this file — it needs a live Windows
        # session — so this call going stale is only ever caught by running it.
        when = time_of_day()
        entry = cache.get(now.track_key, now.artwork, when)
        artwork = colour = None
        if entry is not None:
            artwork, colour = entry
        print(f"app       {now.app_id}")
        print(f"track     {now.title} / {now.artist}")
        print(f"state     {now.state.value}")
        print(f"artwork   {'none' if now.artwork is None else f'{len(now.artwork):,} bytes'}")
        print(f"fitted    {'no' if artwork is None else artwork.size().toTuple()}")
        if colour is not None:
            print(f"label     {colour.name()}")

        # The same frame the app builds, field for field. A proof rendered from a
        # near-copy of the pipeline is not proof of what the app draws.
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
        destination.parent.mkdir(parents=True, exist_ok=True)
        room.scaled(room.width() * 2, room.height() * 2).save(str(destination))
        print(f"saved     {destination}")
        QCoreApplication.quit()

    source.updated.connect(on_update)
    source.failed.connect(lambda m: print(f"[failed] {m}", file=sys.stderr))
    source.start()

    QTimer.singleShot(8000, QCoreApplication.quit)
    app.exec()
    source.stop()
    return 0 if seen.get("done") else 1


if __name__ == "__main__":
    sys.exit(main())
