"""Load the authored art and its layout.

The layout numbers live in `assets/layout.json`, written by
`tools/make_assets.py` from the same constants that positioned the art. The app
never restates them: if the sleeve moves, it moves in one place.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from PySide6.QtGui import QImage

ASSETS = Path(__file__).parent / "assets"


@dataclass(frozen=True)
class Slot:
    x: int
    y: int
    width: int
    height: int


@dataclass(frozen=True)
class Layout:
    width: int
    height: int
    sleeve: Slot
    label: Slot
    cat_breathe_frames: int


@lru_cache(maxsize=1)
def layout() -> Layout:
    data = json.loads((ASSETS / "layout.json").read_text(encoding="utf-8"))
    return Layout(
        width=data["canvas"]["width"],
        height=data["canvas"]["height"],
        sleeve=Slot(**data["sleeve_slot"]),
        label=Slot(**data["label_slot"]),
        cat_breathe_frames=data["cat_breathe_frames"],
    )


@lru_cache(maxsize=32)
def load(relative: str) -> QImage:
    path = ASSETS / relative
    image = QImage(str(path))
    if image.isNull():
        raise FileNotFoundError(
            f"Missing or unreadable asset: {path}. Run `uv run python tools/make_assets.py`."
        )
    return image.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)


@lru_cache(maxsize=1)
def cat_breathe_frames() -> tuple[QImage, ...]:
    return tuple(load(f"cat/breathe-{i:02d}.png") for i in range(layout().cat_breathe_frames))


@lru_cache(maxsize=1)
def demo_covers() -> tuple[QImage, ...]:
    covers = sorted((ASSETS / "demo").glob("cover-*.png"))
    return tuple(load(f"demo/{p.name}") for p in covers)
