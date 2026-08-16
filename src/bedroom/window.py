"""The window the room lives in."""

from __future__ import annotations

from PySide6.QtCore import (
    Property,
    QEasingCurve,
    QPoint,
    QPropertyAnimation,
    Qt,
    Signal,
)
from PySide6.QtGui import QAction, QActionGroup, QColor, QGuiApplication, QImage, QPainter
from PySide6.QtWidgets import QMenu, QWidget

from . import assets_loader as assets
from .model import Controls, SessionInfo
from .scene import Frame, compose

ZOOM_LEVELS = (2, 3, 4)

FOLLOW_WINDOWS = ""  # the "no override" sentinel, stored in settings

_BUTTON_RADIUS = 15
_BUTTON_GAP = 46
_BAR_BOTTOM_MARGIN = 30


def largest_zoom_that_fits(canvas: tuple[int, int], available: tuple[int, int]) -> int:
    """The biggest whole-number scale that still fits on screen.

    Whole numbers only. A fractional scale would blur every edge in the art,
    which is the one thing pixel art cannot survive.
    """
    width, height = canvas
    room_w, room_h = available
    fitting = [z for z in ZOOM_LEVELS if width * z <= room_w and height * z <= room_h]
    return max(fitting) if fitting else min(ZOOM_LEVELS)


class RoomWidget(QWidget):
    """Draws the room, enlarged by a whole number, with controls on hover."""

    playpause = Signal()
    skip = Signal(int)

    def __init__(self, zoom: int = 2) -> None:
        super().__init__()
        self._layout = assets.layout()
        self._frame = Frame()
        self._controls = Controls()
        self._zoom = zoom
        self._overlay = 0.0
        self.setMouseTracking(True)
        self._apply_zoom()

        self._fade = QPropertyAnimation(self, b"overlay", self)
        self._fade.setDuration(160)
        self._fade.setEasingCurve(QEasingCurve.Type.InOutQuad)

    # -- overlay opacity, animated ---------------------------------------

    def get_overlay(self) -> float:
        return self._overlay

    def set_overlay(self, value: float) -> None:
        self._overlay = value
        self.update()

    overlay = Property(float, get_overlay, set_overlay)

    def _fade_to(self, target: float) -> None:
        self._fade.stop()
        self._fade.setStartValue(self._overlay)
        self._fade.setEndValue(target)
        self._fade.start()

    def enterEvent(self, event) -> None:  # noqa: N802 (Qt override)
        self._fade_to(1.0)

    def leaveEvent(self, event) -> None:  # noqa: N802 (Qt override)
        self._fade_to(0.0)

    # -- state -----------------------------------------------------------

    @property
    def zoom(self) -> int:
        return self._zoom

    def set_zoom(self, zoom: int) -> None:
        self._zoom = zoom
        self._apply_zoom()

    def _apply_zoom(self) -> None:
        self.setFixedSize(self._layout.width * self._zoom, self._layout.height * self._zoom)

    def set_frame(self, frame: Frame) -> None:
        self._frame = frame
        self.update()

    def set_controls(self, controls: Controls) -> None:
        self._controls = controls
        self.update()

    def render_room(self) -> QImage:
        return compose(self._frame)

    # -- controls --------------------------------------------------------

    def _button_centres(self) -> list[tuple[str, QPoint, bool]]:
        y = self.height() - _BAR_BOTTOM_MARGIN
        cx = self.width() // 2
        can_toggle = self._controls.play or self._controls.pause
        return [
            ("previous", QPoint(cx - _BUTTON_GAP, y), self._controls.previous),
            ("playpause", QPoint(cx, y), can_toggle),
            ("next", QPoint(cx + _BUTTON_GAP, y), self._controls.next),
        ]

    def mousePressEvent(self, event) -> None:  # noqa: N802 (Qt override)
        if event.button() != Qt.MouseButton.LeftButton or self._overlay < 0.5:
            return
        for name, centre, enabled in self._button_centres():
            if not enabled:
                continue
            delta = event.position().toPoint() - centre
            if delta.x() ** 2 + delta.y() ** 2 <= _BUTTON_RADIUS**2:
                if name == "playpause":
                    self.playpause.emit()
                else:
                    self.skip.emit(1 if name == "next" else -1)
                return

    def _paint_controls(self, painter: QPainter) -> None:
        alpha = self._overlay
        if alpha <= 0.01:
            return
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(Qt.PenStyle.NoPen)

        for name, centre, enabled in self._button_centres():
            painter.setBrush(QColor(16, 14, 20, int(150 * alpha)))
            painter.drawEllipse(centre, _BUTTON_RADIUS, _BUTTON_RADIUS)

            shade = 235 if enabled else 110
            painter.setBrush(QColor(shade, shade, shade, int((255 if enabled else 130) * alpha)))
            self._paint_glyph(painter, name, centre)

    def _paint_glyph(self, painter: QPainter, name: str, c: QPoint) -> None:
        s = 6
        if name == "playpause":
            if not self._frame.playing:
                painter.drawPolygon(
                    [
                        QPoint(c.x() - 4, c.y() - s),
                        QPoint(c.x() - 4, c.y() + s),
                        QPoint(c.x() + 7, c.y()),
                    ]
                )
            else:
                painter.drawRect(c.x() - 5, c.y() - s, 4, s * 2)
                painter.drawRect(c.x() + 1, c.y() - s, 4, s * 2)
            return

        direction = 1 if name == "next" else -1
        for offset in (-4, 2):
            tip = c.x() + direction * (offset + 5)
            back = c.x() + direction * offset
            painter.drawPolygon(
                [QPoint(back, c.y() - s), QPoint(back, c.y() + s), QPoint(tip, c.y())]
            )

    def paintEvent(self, event) -> None:  # noqa: N802 (Qt override)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)
        painter.drawImage(self.rect(), self.render_room())
        self._paint_controls(painter)
        painter.end()


class BedroomWindow(QWidget):
    playpause = Signal()
    skip = Signal(int)
    source_chosen = Signal(str)
    zoom_chosen = Signal(int)

    def __init__(self, zoom: int = 2) -> None:
        super().__init__()
        self.setWindowTitle("The Bedroom")
        self.room = RoomWidget(zoom)
        self.room.setParent(self)
        self.setFixedSize(self.room.size())
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.DefaultContextMenu)

        self._sessions: list[SessionInfo] = []
        self._override = FOLLOW_WINDOWS
        self._demo = False

        self.room.playpause.connect(self.playpause)
        self.room.skip.connect(self.skip)

    def set_frame(self, frame: Frame) -> None:
        self.room.set_frame(frame)

    def set_controls(self, controls: Controls) -> None:
        self.room.set_controls(controls)

    def set_sessions(self, sessions: list[SessionInfo]) -> None:
        self._sessions = sessions

    def set_override(self, app_id: str) -> None:
        self._override = app_id

    def set_demo(self, demo: bool) -> None:
        self._demo = demo

    def set_zoom(self, zoom: int) -> None:
        self.room.set_zoom(zoom)
        self.setFixedSize(self.room.size())

    def contextMenuEvent(self, event) -> None:  # noqa: N802 (Qt override)
        menu = QMenu(self)

        # Listed only when there is genuinely a choice to make. Several sessions
        # linger routinely, but usually only one is playing, so this is an
        # escape hatch rather than something on the face of the room.
        if not self._demo and len(self._sessions) > 1:
            source_menu = menu.addMenu("Follow")
            group = QActionGroup(source_menu)
            group.setExclusive(True)
            for app_id, label in [(FOLLOW_WINDOWS, "Whatever Windows says")] + [
                (s.app_id, s.label) for s in self._sessions
            ]:
                action = QAction(label, source_menu, checkable=True)
                action.setChecked(app_id == self._override)
                action.triggered.connect(lambda _=False, a=app_id: self.source_chosen.emit(a))
                group.addAction(action)
                source_menu.addAction(action)
            menu.addSeparator()

        canvas_width = assets.layout().width
        zoom_menu = menu.addMenu("Size")
        zoom_group = QActionGroup(zoom_menu)
        zoom_group.setExclusive(True)
        for level in ZOOM_LEVELS:
            label = f"{level}x  ({canvas_width * level} px)"
            action = QAction(label, zoom_menu, checkable=True)
            action.setChecked(level == self.room.zoom)
            action.triggered.connect(lambda _=False, z=level: self.zoom_chosen.emit(z))
            zoom_group.addAction(action)
            zoom_menu.addAction(action)

        menu.addSeparator()
        quit_action = QAction("Close", menu)
        quit_action.triggered.connect(self.close)
        menu.addAction(quit_action)
        menu.exec(event.globalPos())

    def keyPressEvent(self, event) -> None:  # noqa: N802 (Qt override)
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        elif event.key() == Qt.Key.Key_Space:
            self.playpause.emit()

    def centre_on_screen(self) -> None:
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            return
        area = screen.availableGeometry()
        self.move(
            area.x() + (area.width() - self.width()) // 2,
            area.y() + (area.height() - self.height()) // 2,
        )
