"""Load the authored art and its layout.

The layout numbers live in `assets/layout.json`, written by
`tools/make_assets.py` from the same constants that positioned the art. The app
never restates them: if the sleeve moves, it moves in one place.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType

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
    amp: Slot
    # Every animation the cat has, and how many frames each runs for. The app
    # never names a clip it has not been told about here.
    cat_clips: Mapping[str, int]
    resting_clip: str
    # How many frames one turn of the record takes.
    record_frames: int
    times_of_day: tuple[str, ...]
    # How to grade live album art so it belongs to the room it is dropped into.
    # Authored with the art, exported here, never restated in the app.
    sleeve_grade: Mapping[str, Mapping[str, object]]


@lru_cache(maxsize=1)
def layout() -> Layout:
    data = json.loads((ASSETS / "layout.json").read_text(encoding="utf-8"))
    return Layout(
        width=data["canvas"]["width"],
        height=data["canvas"]["height"],
        sleeve=Slot(**data["sleeve_slot"]),
        label=Slot(**data["label_slot"]),
        amp=Slot(**data["amp_slot"]),
        cat_clips=MappingProxyType(dict(data["cat_clips"])),
        resting_clip=data["resting_clip"],
        record_frames=data["record_frames"],
        times_of_day=tuple(data["times_of_day"]),
        sleeve_grade=MappingProxyType(
            {k: MappingProxyType(dict(v)) for k, v in data["sleeve_grade"].items()}
        ),
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


@lru_cache(maxsize=8)
def background(when: str) -> QImage:
    """The room for one time of day, already lit and graded.

    There is a full set of art per band because the grade is a per-pixel pass
    over a finished frame, and the app composites live. Baking is the only place
    the two can meet.
    """
    return load(f"background-{when}.png")


@lru_cache(maxsize=32)
def cat_frames(when: str, clip: str) -> tuple[QImage, ...]:
    """Every frame of one of the cat's clips, in order, graded for this band."""
    count = layout().cat_clips[clip]
    return tuple(load(f"cat/{when}/{clip}-{i:02d}.png") for i in range(count))


@lru_cache(maxsize=8)
def record_frames(when: str) -> tuple[QImage, ...]:
    """One turn of the record, graded for this band.

    The record is not in the background at all — there is no parked copy baked
    underneath. These frames are the record, stopped as well as spinning.
    """
    return tuple(
        load(f"record/{when}/{i:02d}.png") for i in range(layout().record_frames)
    )
