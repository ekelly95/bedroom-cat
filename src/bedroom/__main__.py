"""Entry point."""

from __future__ import annotations

import argparse
import sys
import time

from PySide6.QtCore import QSettings, QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication

from . import assets_loader as assets
from .artwork import fit_static
from .cat import CatMind
from .model import Controls, NowPlaying, PlaybackState
from .scene import Frame
from .source_demo import DemoSource
from .window import FOLLOW_WINDOWS, ZOOM_LEVELS, BedroomWindow, largest_zoom_that_fits

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
        default=None,
        choices=ZOOM_LEVELS,
        help="whole-number scale for the room (default: remembered, or 2)",
    )
    return parser.parse_args(argv)


def describe(now: NowPlaying | None, *, demo: bool = False) -> str:
    if now is None:
        return "The Bedroom — nothing playing"
    who = "Demo" if demo else now.app_id.removesuffix(".exe")
    mark = "▶" if now.state is PlaybackState.PLAYING else "❚❚"
    artist = f" — {now.display_artist}" if now.display_artist else ""
    return f"{mark} {now.display_title}{artist}  ·  {who}"


def resolve_zoom(settings: QSettings, requested: int | None) -> int:
    canvas = (assets.layout().width, assets.layout().height)
    screen = QGuiApplication.primaryScreen()
    area = screen.availableGeometry() if screen else None
    ceiling = (
        largest_zoom_that_fits(canvas, (area.width() - 80, area.height() - 120))
        if area
        else max(ZOOM_LEVELS)
    )
    if requested is not None:
        return min(requested, ceiling)
    remembered = int(settings.value("zoom", 2))
    if remembered not in ZOOM_LEVELS:
        remembered = 2
    return min(remembered, ceiling)


def run_demo(window: BedroomWindow, settings: QSettings) -> object:
    layout = assets.layout()
    demo = DemoSource()
    covers = [str(p) for p in sorted((assets.ASSETS / "demo").glob("cover-*.png"))]
    cat = CatMind(frames=layout.cat_breathe_frames)
    clock = {"last": time.monotonic()}

    window.set_demo(True)
    window.playpause.connect(demo.toggle)
    window.skip.connect(demo.skip)

    def tick() -> None:
        demo.advance(TICK_MS / 1000)
        now = demo.now_playing()
        artwork, colour = fit_static(covers[demo.cover_index], layout.sleeve.width)
        playing = now.state is PlaybackState.PLAYING

        elapsed = time.monotonic() - clock["last"]
        clock["last"] += elapsed
        cat.observe(playing, now.track_key)
        cat.advance(elapsed)

        window.set_frame(
            Frame(
                artwork=artwork,
                label_colour=colour,
                cat_frame=cat.frame,
                dim=not playing,
                playing=playing,
            )
        )
        window.set_controls(now.controls)
        window.setWindowTitle(describe(now, demo=True) + "  ·  demo")

    timer = QTimer(window)
    timer.timeout.connect(tick)
    timer.start(TICK_MS)
    tick()
    return timer


def run_windows(window: BedroomWindow, settings: QSettings) -> object:
    from .artwork import ArtworkCache
    from .source_windows import WindowsSource

    layout = assets.layout()
    cache = ArtworkCache(layout.sleeve.width)
    source = WindowsSource()
    latest: dict[str, NowPlaying | None] = {"now": None}
    cat = CatMind(frames=layout.cat_breathe_frames)
    clock = {"last": time.monotonic()}

    remembered = str(settings.value("follow", FOLLOW_WINDOWS))
    source.set_override(remembered or None)
    window.set_override(remembered)

    source.updated.connect(lambda now: latest.__setitem__("now", now))
    source.sessions_changed.connect(window.set_sessions)
    source.failed.connect(lambda m: print(f"[bedroom] {m}", file=sys.stderr))

    def choose_source(app_id: str) -> None:
        source.set_override(app_id or None)
        window.set_override(app_id)
        settings.setValue("follow", app_id)

    window.source_chosen.connect(choose_source)
    window.playpause.connect(lambda: source.send("playpause"))
    window.skip.connect(lambda step: source.send("next" if step > 0 else "previous"))

    def tick() -> None:
        now = latest["now"]

        artwork = colour = None
        if now is not None:
            entry = cache.get(now.track_key, now.artwork)
            if entry is not None:
                artwork, colour = entry

        playing = now is not None and now.state is PlaybackState.PLAYING

        # The cat runs on wall-clock time, not on the tick counter, so its pace
        # is its own and survives a slow or uneven frame.
        elapsed = time.monotonic() - clock["last"]
        clock["last"] += elapsed
        cat.observe(playing, now.track_key if now is not None else None)
        cat.advance(elapsed)

        window.set_frame(
            Frame(
                artwork=artwork,
                label_colour=colour,
                cat_frame=cat.frame,
                # Dim means paused. With no session at all the room is quiet but
                # bright: an empty daytime bedroom, not a paused one.
                dim=now is not None and not playing,
                playing=playing,
            )
        )
        window.set_controls(now.controls if now is not None else Controls())
        window.setWindowTitle(describe(now))

    timer = QTimer(window)
    timer.timeout.connect(tick)
    timer.start(TICK_MS)
    tick()
    source.start()
    return source


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    app = QApplication(sys.argv[:1])
    app.setOrganizationName("Bedroom")
    app.setApplicationName("Bedroom")
    settings = QSettings()

    zoom = resolve_zoom(settings, args.zoom)
    window = BedroomWindow(zoom=zoom)
    window.zoom_chosen.connect(
        lambda z: (window.set_zoom(z), settings.setValue("zoom", z))
    )

    source = run_demo(window, settings) if args.demo else run_windows(window, settings)
    window.centre_on_screen()
    window.show()
    try:
        return app.exec()
    finally:
        if hasattr(source, "stop"):
            source.stop()


if __name__ == "__main__":
    sys.exit(main())
