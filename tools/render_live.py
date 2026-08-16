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
from bedroom.artwork import ArtworkCache  # noqa: E402
from bedroom.scene import Frame, compose  # noqa: E402
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
        entry = cache.get(now.track_key, now.artwork)
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

        room = compose(
            Frame(
                artwork=artwork,
                label_colour=colour,
                dim=not now.state.is_active,
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
