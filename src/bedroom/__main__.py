"""Entry point."""

from __future__ import annotations

import argparse
import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from . import assets_loader as assets
from .artwork import fit_static
from .scene import Frame
from .source_demo import DemoSource
from .window import ZOOM_LEVELS, BedroomWindow

TICK_MS = 120


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="bedroom", description=__doc__)
    parser.add_argument(
        "--demo",
        action="store_true",
        help="run the invented player instead of reading Windows",
    )
    parser.add_argument(
        "--zoom",
        type=int,
        default=2,
        choices=ZOOM_LEVELS,
        help="whole-number scale for the room (default: 2)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    app = QApplication(sys.argv[:1])
    window = BedroomWindow(zoom=args.zoom)

    layout = assets.layout()
    demo = DemoSource()
    covers = [str(p) for p in sorted((assets.ASSETS / "demo").glob("cover-*.png"))]
    state = {"cat": 0}

    def tick() -> None:
        demo.advance(TICK_MS / 1000)
        artwork, colour = fit_static(covers[demo.cover_index], layout.sleeve.width)
        state["cat"] = (state["cat"] + 1) % layout.cat_breathe_frames
        window.set_frame(
            Frame(artwork=artwork, label_colour=colour, cat_frame=state["cat"])
        )

    timer = QTimer()
    timer.timeout.connect(tick)
    timer.start(TICK_MS)
    tick()

    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
