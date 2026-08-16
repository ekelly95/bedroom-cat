"""Facts this codebase states in more than one place.

Several numbers and one formula are deliberately restated across files, each
time with a comment saying to keep it in step with the others. Comments do not
fail a test run, and both of these have already come apart once: the sleeve's
mounting drifted between the app and the bake and was only caught by an outside
reader.

These are the two places this codebase can rot while continuing to work.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from PIL import Image
from PySide6.QtGui import QColor, QImage

from bedroom import __main__ as app
from bedroom import artwork, cat, platter

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import make_assets


def test_one_authored_frame_is_one_drawn_frame() -> None:
    """The cat, the record and the proof GIFs all run at the app's tick.

    Four files hold this number. Change one and its own tests still pass, while
    the cat quietly falls out of step with the record and the proof GIFs play at
    a speed the room never runs at.
    """
    tick = app.TICK_MS / 1000
    assert tick == cat.REACTION_FRAME_SECONDS, "cat.py has drifted from TICK_MS"
    assert tick == platter.FRAME_SECONDS, "platter.py has drifted from TICK_MS"
    assert make_assets.TICK_MS == app.TICK_MS, "the proof GIFs would play at the wrong speed"


def test_the_record_completes_its_cycle_in_whole_ticks() -> None:
    """The authored frame count and the app's idea of a cycle are the same thing."""
    from bedroom import assets_loader

    assert assets_loader.layout().record_frames == make_assets.RECORD_FRAMES


def _solid_qt(rgb: tuple[int, int, int], size: int = 8) -> QImage:
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(QColor(*rgb))
    return image


def _solid_pil(rgb: tuple[int, int, int], size: int = 8) -> Image.Image:
    return Image.new("RGB", (size, size), rgb)


@pytest.mark.parametrize("when", ["day", "evening", "night"])
@pytest.mark.parametrize(
    "rgb",
    [
        (200, 40, 40),  # a saturated cover
        (18, 20, 26),  # a near-black one, where the wash matters most
        (240, 235, 225),  # a near-white one, where the gain can clip
        (60, 120, 180),
    ],
)
def test_both_sleeve_grades_agree(when: str, rgb: tuple[int, int, int]) -> None:
    """The app grades live artwork in Qt; the bake grades it again in Pillow.

    The same formula, written twice, because one side composites through Qt at
    runtime and the other draws through Pillow at bake time. That duplication is
    unavoidable and it is exactly how the sleeve's mounting drifted before.
    Colour is the half that *can* be compared, so it is.
    """
    graded_qt = artwork.grade_sleeve(_solid_qt(rgb), when)
    graded_pil = make_assets.grade_sleeve(_solid_pil(rgb), when)

    from_qt = graded_qt.pixelColor(4, 4).getRgb()[:3]
    from_pil = graded_pil.getpixel((4, 4))
    assert from_qt == from_pil, (
        f"{when} {rgb}: app says {from_qt}, bake says {from_pil} — "
        "the two copies of grade_sleeve have parted"
    )


def test_the_baked_sleeve_numbers_are_what_the_app_reads() -> None:
    """`layout.json` is the handover between the two, so pin it as well."""
    from bedroom import assets_loader

    for when in assets_loader.layout().times_of_day:
        exported = dict(assets_loader.layout().sleeve_grade[when])
        exported["wash"] = list(exported["wash"])
        assert exported == make_assets.sleeve_grade(when)
