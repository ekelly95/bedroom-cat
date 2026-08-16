"""The window the room lives in."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPainter, QPaintEvent
from PySide6.QtWidgets import QWidget

from . import assets_loader as assets
from .scene import Frame, compose

ZOOM_LEVELS = (2, 3, 4)


class RoomWidget(QWidget):
    """Draws the composed room, enlarged by a whole number only.

    Nearest-neighbour on the way up, so pixels stay square and hard. Fractional
    scaling is never used: it would blur every edge in the art.
    """

    def __init__(self, zoom: int = 2) -> None:
        super().__init__()
        self._layout = assets.layout()
        self._frame = Frame()
        self._zoom = zoom
        self.setMinimumSize(self._layout.width, self._layout.height)
        self._apply_zoom()

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

    def render_room(self) -> QImage:
        return compose(self._frame)

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802 (Qt override)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)
        painter.drawImage(self.rect(), self.render_room())
        painter.end()


class BedroomWindow(QWidget):
    def __init__(self, zoom: int = 2) -> None:
        super().__init__()
        self.setWindowTitle("The Bedroom")
        self.room = RoomWidget(zoom)
        self.room.setParent(self)
        self.setFixedSize(self.room.size())

    def set_frame(self, frame: Frame) -> None:
        self.room.set_frame(frame)

    def set_zoom(self, zoom: int) -> None:
        self.room.set_zoom(zoom)
        self.setFixedSize(self.room.size())

    def keyPressEvent(self, event) -> None:  # noqa: N802 (Qt override)
        if event.key() == Qt.Key.Key_Escape:
            self.close()
