"""Hand-authored pixel art for the bedroom, expressed as drawing code.

Every shape here is placed deliberately at logical-pixel coordinates taken from
`docs/art-brief.md` Part 2. Writing the art as code rather than as a painted file
keeps it reproducible and lets a later session nudge one object by one pixel
without repainting anything.

    uv run python tools/make_assets.py

Coordinate ranges are half-open throughout, matching the brief: `rect(24, 48,
80, 104)` is 56x56 pixels covering columns 24..79 and rows 48..103.
"""

from __future__ import annotations

import colorsys
import json
import math
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "proof"

WIDTH, HEIGHT = 320, 200

# The app's frame interval, restated here only so the proof GIFs play at the
# speed the reactions will really run. Keep it in step with __main__.TICK_MS.
TICK_MS = 120

# Where the app drops live album artwork. x, y, width, height — half-open, and
# exported to assets/layout.json so the app never restates these numbers.
SLEEVE_SLOT = (26, 50, 52, 52)
LABEL_SLOT = (117, 80, 12, 7)
# The amp's readout. Baked dark; the app fills it with a colour sampled from the
# artwork that is playing, and blinks it while the music runs.
AMP_SLOT = (31, 117, 14, 4)

# The record's groove highlight is a full diameter, so it draws the same pixels
# at an angle and at that angle plus half a turn: a spin only has 180 degrees of
# distinct frames. Twelve of them, advanced one per TICK_MS, sweeps the mark
# through that half turn in 1.44 seconds — the same "one authored frame is one
# drawn frame" rule the cat's reactions run on.
RECORD_FRAMES, RECORD_ARC = 12, 180.0

TIMES_OF_DAY = ("day", "evening", "night")

# ---------------------------------------------------------------- palette ---
# Sampled from the approved daytime reference.
WALL = (203, 208, 170)
WALL_SHADE = (188, 194, 156)
BEAM = (74, 56, 43)
FLOOR = (198, 154, 106)
FLOOR_PLANK = (178, 135, 88)
SKIRT = (150, 110, 72)

WOOD = (122, 74, 43)
WOOD_DARK = (92, 54, 31)
WOOD_LIGHT = (146, 93, 55)
OUTLINE = (58, 38, 26)

# The sideboard has its own wood, cooler and darker than the rest of the room's.
# It is the one large object directly behind the cat, and in the shared WOOD it
# sat at almost the same value as the cat's fur — the cat's back dissolved into
# it. Kept separate from WOOD so cooling it does not also cool the window frame,
# the bed and the curtain rod.
SIDEBOARD = (104, 66, 46)
SIDEBOARD_DARK = (78, 48, 34)
SIDEBOARD_LIGHT = (126, 84, 58)

SPEAKER = (44, 44, 48)
SPEAKER_DARK = (24, 24, 27)
SPEAKER_RIM = (66, 66, 71)

# The turning glint on the record, and the static grooves it has to be told apart
# from. The glint used to be 72 and never moved, so nobody had to see it; once it
# turns it has to clear the grooves in every band, and the night wash lifts the
# darks so far that at 72 it landed one value step above them and vanished.
RECORD_DISC = (18, 18, 21)
RECORD_GROOVE = (46, 46, 52)
RECORD_GLINT = (104, 104, 114)

CAT_CREAM = (240, 231, 214)
CAT_FUR = (146, 114, 84)
CAT_DARK = (108, 80, 57)
CAT_EAR = (198, 148, 146)
CAT_LINE = (70, 50, 36)
# A one-pixel rim along the top of the loaf, where it crosses the sideboard.
CAT_LIGHT = (178, 144, 110)
# A shade under the body fur, enough to tell the tail from the flank it crosses
# now that the two share one outline.
CAT_TAIL = (134, 103, 75)

RUG = (244, 236, 220)
RUG_EDGE = (224, 212, 188)

SKY = (146, 200, 233)
CLOUD = (243, 249, 253)
SEA = (108, 166, 200)
SEA_LINE = (140, 191, 219)
TREE = (112, 170, 92)
TREE_DARK = (76, 122, 62)

CURTAIN = (241, 231, 207)
CURTAIN_SHADE = (221, 209, 182)
ROD = (92, 62, 44)

PLANT = (78, 140, 62)
PLANT_DARK = (56, 106, 46)
POT = (192, 112, 63)
POT_DARK = (158, 88, 47)

# The bed is large, pale and right next to the window, so it wins any contrast
# fight it is allowed to enter. Linen pulled down off white and its outlines
# softened to BED_LINE: it stays perfectly readable and stops shouting.
BED_LINEN = (224, 218, 202)
BED_LINEN_TOP = (236, 231, 217)
BED_LINE = (128, 106, 88)
BED_BLANKET = (86, 106, 82)
BED_BLANKET_D = (68, 86, 66)

MUG = (108, 140, 150)

LAMP_METAL = (168, 132, 78)
LAMP_METAL_D = (118, 88, 48)
LAMP_SHADE = (238, 214, 158)

AMP_FACE = (52, 48, 46)
# The display is dark in the baked art. Its colour arrives at runtime, sampled
# from whatever is playing — see AMP_SLOT.
AMP_DEAD = (34, 38, 36)

# Contact shadows under the furniture. Warm and translucent rather than grey, so
# they darken the floor without turning it muddy. Retinted plum since the grade
# went in — a neutral brown shadow sat oddly against its warm/cool split.
SHADOW = (74, 40, 40, 64)
SHADOW_SOFT = (74, 40, 40, 38)


def tapered_stroke(points: list[tuple[float, float, float]]) -> list[tuple[float, float]]:
    """A smooth outline around a centre-line that changes width along its length.

    Used for the cat's tail. Built from a single polygon rather than a chain of
    overlapping circles: the circles left scalloped bumps along the silhouette,
    and a bumpy row along the bottom of a cat reads as toes.
    """
    left: list[tuple[float, float]] = []
    right: list[tuple[float, float]] = []
    for i, (x, y, half) in enumerate(points):
        if i == 0:
            dx, dy = points[1][0] - x, points[1][1] - y
        elif i == len(points) - 1:
            dx, dy = x - points[-2][0], y - points[-2][1]
        else:
            dx = points[i + 1][0] - points[i - 1][0]
            dy = points[i + 1][1] - points[i - 1][1]
        length = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / length * half, dx / length * half
        left.append((x + nx, y + ny))
        right.append((x - nx, y - ny))
    return left + right[::-1]


def grow(points: list[tuple[float, float]], amount: float = 1.4) -> list[tuple[float, float]]:
    """The same polygon, pushed outwards from its own centre.

    Used to stroke a shape from the outside rather than on its boundary, so the
    stroke can be hidden where the shape is buried inside another one — which is
    how the cat's ears get an outline without a line drawn across the top of its
    head.
    """
    cx = sum(x for x, _ in points) / len(points)
    cy = sum(y for _, y in points) / len(points)
    out: list[tuple[float, float]] = []
    for x, y in points:
        dx, dy = x - cx, y - cy
        length = math.hypot(dx, dy) or 1.0
        out.append((x + dx / length * amount, y + dy / length * amount))
    return out


class Art:
    """A logical-pixel canvas with half-open drawing primitives."""

    def __init__(self, width: int = WIDTH, height: int = HEIGHT) -> None:
        self.img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)

    def rect(self, x0: int, y0: int, x1: int, y1: int, colour) -> None:
        if x1 <= x0 or y1 <= y0:
            return
        self.d.rectangle([x0, y0, x1 - 1, y1 - 1], fill=colour)

    def outline_rect(self, x0: int, y0: int, x1: int, y1: int, colour) -> None:
        self.d.rectangle([x0, y0, x1 - 1, y1 - 1], outline=colour, width=1)

    def ellipse(self, x0: int, y0: int, x1: int, y1: int, colour, outline=None) -> None:
        self.d.ellipse([x0, y0, x1 - 1, y1 - 1], fill=colour, outline=outline, width=1)

    def arc(self, x0: int, y0: int, x1: int, y1: int, start, end, colour, width=1) -> None:
        self.d.arc([x0, y0, x1 - 1, y1 - 1], start, end, fill=colour, width=width)

    def poly(self, points, colour, outline=None) -> None:
        self.d.polygon(points, fill=colour, outline=outline)

    def paste(self, other: Image.Image, x: int, y: int) -> None:
        self.img.paste(other, (x, y), other if other.mode == "RGBA" else None)

    def shade(self, paint) -> None:
        """Composite a translucent pass over whatever is already drawn.

        ImageDraw writes RGBA values straight into the buffer instead of blending
        them, so a semi-transparent shape drawn directly would punch a hole in
        the room rather than darken it. Used for the contact shadows.
        """
        layer = Image.new("RGBA", self.img.size, (0, 0, 0, 0))
        paint(ImageDraw.Draw(layer))
        self.img.alpha_composite(layer)


# ------------------------------------------------------------------ room ---


def draw_shell(a: Art) -> None:
    a.rect(0, 0, WIDTH, 152, WALL)
    a.rect(0, 0, WIDTH, 7, BEAM)
    a.rect(0, 7, WIDTH, 10, WALL_SHADE)
    a.rect(0, 152, WIDTH, HEIGHT, FLOOR)
    for y in range(156, HEIGHT, 9):
        a.rect(0, y, WIDTH, y + 1, FLOOR_PLANK)
    a.rect(0, 148, WIDTH, 152, SKIRT)
    a.rect(0, 147, WIDTH, 148, OUTLINE)
    a.rect(0, HEIGHT - 6, WIDTH, HEIGHT, BEAM)


def draw_window(a: Art) -> None:
    # Rod and curtains sit outside the frame so the frame reads as the opening.
    a.rect(198, 16, 312, 19, ROD)
    a.ellipse(196, 14, 203, 21, ROD)
    a.ellipse(307, 14, 314, 21, ROD)

    # View: open sky over a treeline. No water — it is an inland view.
    a.rect(216, 28, 292, 88, SKY)
    for cx, cy, w in ((222, 38, 16), (256, 32, 20), (274, 44, 14)):
        a.ellipse(cx, cy, cx + w, cy + 7, CLOUD)
        a.ellipse(cx + 4, cy - 4, cx + w - 4, cy + 6, CLOUD)

    # Far treeline first, then a nearer, brighter one in front of it.
    for bx, lift in ((214, 4), (228, 10), (242, 2), (256, 8), (270, 0), (282, 6)):
        a.ellipse(bx, 60 - lift, bx + 22, 90, TREE_DARK)
    for bx, lift in ((216, 0), (234, 6), (250, 0), (266, 5), (280, 2)):
        a.ellipse(bx, 66 - lift, bx + 18, 90, TREE)
    a.rect(216, 84, 292, 88, TREE_DARK)

    # Frame, mullions, sill.
    a.outline_rect(212, 24, 296, 92, WOOD_DARK)
    a.rect(213, 25, 295, 28, WOOD)
    a.rect(213, 88, 295, 91, WOOD)
    a.rect(213, 25, 216, 91, WOOD)
    a.rect(292, 25, 295, 91, WOOD)
    a.rect(252, 28, 256, 88, WOOD)
    a.rect(216, 55, 292, 59, WOOD)
    a.outline_rect(212, 24, 296, 92, OUTLINE)
    a.rect(208, 92, 300, 96, WOOD_LIGHT)
    a.rect(208, 96, 300, 97, OUTLINE)

    for x0 in (202, 294):
        a.rect(x0, 18, x0 + 12, 98, CURTAIN)
        a.rect(x0 + 8, 18, x0 + 12, 98, CURTAIN_SHADE)
        a.rect(x0, 18, x0 + 1, 98, CURTAIN_SHADE)


def draw_bed(a: Art) -> None:
    # Headboard: a broad panel behind the pillows, tall enough to read as one.
    a.rect(198, 98, 220, 160, WOOD)
    a.rect(198, 98, 220, 104, WOOD_LIGHT)
    a.rect(203, 108, 215, 154, WOOD_DARK)
    a.rect(204, 109, 214, 153, WOOD)
    a.outline_rect(198, 98, 220, 160, OUTLINE)

    # Mattress, then two pillows resting on it against the headboard. Outlined in
    # BED_LINE rather than the room's universal OUTLINE: at full strength the bed
    # was the highest-contrast object in the room and pulled the eye off the cat.
    a.rect(218, 126, 318, 142, BED_LINEN)
    a.rect(218, 126, 318, 129, BED_LINEN_TOP)
    a.outline_rect(218, 126, 318, 142, BED_LINE)

    for px in (220, 258):
        a.rect(px + 5, 106, px + 37, 128, BED_LINEN)
        a.ellipse(px, 106, px + 14, 128, BED_LINEN)
        a.ellipse(px + 28, 106, px + 42, 128, BED_LINEN)
        a.arc(px, 106, px + 14, 128, 90, 270, BED_LINE, 1)
        a.arc(px + 28, 106, px + 42, 128, 270, 90, BED_LINE, 1)
        a.rect(px + 6, 106, px + 36, 107, BED_LINE)
        a.rect(px + 6, 127, px + 36, 128, BED_LINE)

    # Duvet, with a turned-back top edge so it reads as bedding, not a box.
    a.rect(218, 140, 318, 172, BED_BLANKET)
    a.rect(218, 140, 318, 149, BED_BLANKET_D)
    a.rect(218, 147, 318, 149, (110, 132, 104))
    for x in range(228, 318, 15):
        a.arc(x, 150, x + 14, 176, 180, 300, BED_BLANKET_D, 2)
    a.outline_rect(218, 140, 318, 172, OUTLINE)

    a.rect(212, 172, 318, 180, WOOD)
    a.outline_rect(212, 172, 318, 180, OUTLINE)
    a.rect(216, 180, 224, 188, WOOD_DARK)
    a.rect(302, 180, 310, 188, WOOD_DARK)

    # Mug on the sill.
    a.rect(284, 84, 294, 93, MUG)
    a.rect(284, 84, 294, 86, (132, 164, 174))
    a.outline_rect(284, 84, 294, 93, OUTLINE)
    a.arc(292, 85, 299, 92, 290, 70, OUTLINE, 1)


def draw_sideboard(a: Art) -> None:
    a.rect(16, 104, 172, 152, SIDEBOARD)
    a.rect(16, 104, 172, 109, SIDEBOARD_LIGHT)
    a.outline_rect(16, 104, 172, 152, OUTLINE)
    # Cupboards left, drawers centre, cupboard right — matches the reference.
    for x0, x1 in ((22, 74), (80, 122), (128, 166)):
        a.outline_rect(x0, 114, x1, 146, SIDEBOARD_DARK)
    a.rect(46, 128, 50, 132, SIDEBOARD_LIGHT)
    a.rect(52, 128, 56, 132, SIDEBOARD_LIGHT)
    a.rect(96, 122, 106, 125, SIDEBOARD_LIGHT)
    a.rect(96, 136, 106, 139, SIDEBOARD_LIGHT)
    a.rect(143, 128, 151, 132, SIDEBOARD_LIGHT)
    a.rect(20, 152, 26, 158, SIDEBOARD_DARK)
    a.rect(162, 152, 168, 158, SIDEBOARD_DARK)


def draw_amp(a: Art) -> None:
    """The amp on the sideboard front, clear of the cat.

    Its readout is baked dark and sits in a recessed well one pixel larger than
    AMP_SLOT, so whatever colour the app paints in still reads as a lit panel set
    into the case rather than as a sticker.
    """
    a.rect(28, 114, 60, 124, AMP_FACE)
    a.outline_rect(28, 114, 60, 124, OUTLINE)
    a.rect(30, 116, 46, 122, AMP_DEAD)
    a.rect(48, 118, 50, 120, (74, 80, 78))
    a.rect(52, 118, 54, 120, (60, 66, 64))


def draw_speaker(a: Art, x0: int, x1: int) -> None:
    """One cabinet and its three drivers.

    The cones do not move. They were built as a two-frame sprite alongside the
    record and taken out again: a dust cap is five pixels across, the movement
    available to it is one pixel, and at 2x the two positions are indis-
    tinguishable side by side. In motion that is not a cone pumping, it is eight
    edge pixels blinking. The cat's breathing is also one pixel and does work,
    because it runs along the length of the animal's back — a compact blob has no
    edge to carry the movement, and the answer to that is not a bigger movement.
    """
    a.rect(x0, 84, x1, 152, SPEAKER)
    a.rect(x0, 84, x1, 87, SPEAKER_RIM)
    a.outline_rect(x0, 84, x1, 152, OUTLINE)
    cx = (x0 + x1) // 2
    for cy, r in ((98, 5), (116, 6), (136, 8)):
        a.ellipse(cx - r, cy - r, cx + r, cy + r, SPEAKER_DARK, SPEAKER_RIM)
        a.ellipse(cx - 2, cy - 2, cx + 2, cy + 2, SPEAKER_RIM)
    a.rect(x0, 152, x1, 156, SPEAKER_DARK)


def draw_turntable(a: Art) -> None:
    """The deck the record sits on: plinth, top face, bare platter.

    The one deliberate exception to the flat camera — a shallow top surface, so
    the platter and tonearm stay readable. The record itself is *not* here: it
    turns at runtime, so it is a sprite, and there is deliberately no parked copy
    baked underneath for the sprite to disagree with. See `draw_record`.
    """

    # Plinth, then a shallow top face carrying the platter.
    a.rect(92, 88, 152, 104, (44, 44, 49))
    a.rect(92, 88, 152, 91, (64, 64, 70))
    a.outline_rect(92, 88, 152, 104, OUTLINE)
    a.poly([(94, 88), (150, 88), (146, 76), (98, 76)], (58, 58, 64), OUTLINE)

    a.ellipse(102, 76, 144, 90, (30, 30, 34), (86, 86, 92))


def draw_record(a: Art, angle: float, label_colour) -> None:
    """Everything from the record disc up, at one angle of rotation.

    Baked as its own sprite family and composited over the room at runtime. The
    tonearm is in here rather than in the deck because the groove highlight
    crosses it: leave it behind and a groove line paints straight over the
    stylus.
    """
    a.ellipse(105, 78, 141, 88, RECORD_DISC)
    for rr in (4, 7):
        a.ellipse(123 - rr * 2, 83 - rr // 2, 123 + rr * 2, 83 + rr // 2, None, RECORD_GROOVE)
    a.ellipse(117, 80, 129, 87, label_colour)

    # A groove highlight that rotates, so the record visibly spins. The vertical
    # radius is the disc's own half-height and not a round 5: at 5 the mark
    # overshot the bottom of the record by one pixel at the steepest angle, and a
    # bright pixel that appears on the platter once per turn reads as a fault.
    rad = math.radians(angle)
    a.d.line(
        [
            (123 + math.cos(rad) * 16, 83 + math.sin(rad) * 4.5),
            (123 - math.cos(rad) * 16, 83 - math.sin(rad) * 4.5),
        ],
        fill=RECORD_GLINT,
        width=1,
    )

    # Tonearm resting across the record.
    a.ellipse(142, 74, 150, 82, (150, 150, 158), OUTLINE)
    a.d.line([(146, 78), (132, 86)], fill=(190, 190, 198), width=2)
    a.rect(130, 85, 134, 89, (210, 210, 218))


def draw_plant(a: Art) -> None:
    a.poly([(158, 92), (172, 92), (169, 104), (161, 104)], POT, OUTLINE)
    a.rect(157, 88, 173, 93, POT_DARK)
    a.outline_rect(157, 88, 173, 93, OUTLINE)
    a.rect(164, 76, 166, 90, PLANT_DARK)
    for dx, dy, w, h in ((-12, -4, 12, 8), (2, -6, 12, 8), (-9, -12, 10, 7), (3, -13, 10, 7)):
        a.ellipse(165 + dx, 80 + dy, 165 + dx + w, 80 + dy + h, PLANT, PLANT_DARK)
    a.ellipse(160, 62, 172, 72, PLANT, PLANT_DARK)


def draw_lamp(a: Art) -> None:
    """A small wall sconce over the sideboard, where the empty picture frame was.

    Drawn unlit on purpose. The glow belongs to the lighting overlays, so one
    lamp object serves all three times of day and the daytime room does not have
    to explain why a lamp is on in the sunshine.
    """
    # Wall plate and stem.
    a.rect(129, 22, 137, 27, LAMP_METAL_D)
    a.outline_rect(129, 22, 137, 27, OUTLINE)
    a.rect(131, 27, 135, 34, LAMP_METAL)
    a.d.line([(131, 27), (131, 33)], fill=LAMP_METAL_D, width=1)

    # A cone opening downwards, which is what explains the pool of light below it.
    a.poly([(124, 34), (141, 34), (146, 45), (119, 45)], LAMP_SHADE, OUTLINE)
    a.poly([(137, 34), (141, 34), (146, 45), (140, 45)], (212, 184, 126))
    a.rect(120, 43, 145, 45, LAMP_METAL)
    a.d.line([(119, 45), (146, 45)], fill=OUTLINE, width=1)

    # The bulb, just showing under the lip.
    a.ellipse(129, 44, 137, 50, (246, 238, 214), OUTLINE)


def draw_rug(a: Art) -> None:
    # Grown a little with the cat. The loaf and its tail together are wider than
    # the old rug, and a cat half on the boards did not read as sitting on a rug.
    a.ellipse(94, 145, 202, 176, RUG_EDGE)
    a.ellipse(97, 147, 199, 174, RUG)
    for x in range(104, 196, 8):
        a.rect(x, 160, x + 3, 162, RUG_EDGE)


def draw_sleeve_frame(a: Art) -> None:
    """The 56x56 sleeve. Its 52x52 interior is filled at runtime with whatever
    artwork Windows is publishing, so only the frame is baked into the art."""
    a.rect(24, 48, 80, 104, (232, 226, 210))
    a.outline_rect(24, 48, 80, 104, OUTLINE)
    a.rect(26, 50, 78, 102, (58, 54, 48))
    a.rect(24, 102, 80, 104, (206, 198, 180))


# ------------------------------------------------------------------- cat ---


# Where the cat and its tail meet the rug. draw_shadows works from these, so the
# contact shadow cannot drift away from the cat: move the loaf and move these
# with it. Nothing else should restate the numbers.
CAT_FOOTPRINT = ((102, 158, 178, 176), (156, 162, 200, 176))


@dataclass(frozen=True)
class Pose:
    """One posture of the cat. Every reaction is a path through these numbers.

    Defaults are the resting loaf, so `Pose()` is the cat as it sits, and any
    field left alone stays exactly as authored. That matters more than it looks:
    it means a reaction can only ever change what it names, and a bad clip cannot
    quietly redesign the animal.
    """

    back: int = 0        # breath: the spine rises
    belly: int = 0       # breath: the underside spreads
    lift: int = 0        # the head comes up off the chest
    ears: int = 0        # ears prick further upright
    ear_flick: int = 0   # the near ear tilts on its own
    eyes: int = 0        # 0 closed, 1 half, 2 wide
    gaze: int = 0        # the eyes slide towards the speakers, on the left
    tail: int = 0        # the tail's outer half lifts off the rug
    stretch: int = 0     # the loaf lengthens and flattens
    yawn: int = 0        # the mouth opens


# The cat as it sits, and the default everywhere a pose is optional.
RESTING = Pose()


def draw_cat(a: Art, pose: Pose = RESTING) -> None:
    """One heavy loaf in three-quarter profile, head to the viewer's left.

    The cat is drawn as **one silhouette**, not as a head plus a body. Every
    shape is stroked first, a pixel oversized, in CAT_LINE, and only then filled.
    Outlining each shape on its own boundary left a hard line down the middle of
    the animal and it read as a snowman rather than as one heavy loaf.

    The head and everything on it are positioned from one origin, `hx, hy`, so
    the whole face moves as a unit when the cat looks up. Writing the features at
    absolute coordinates worked fine for a cat that never moved and became
    unmanageable the moment one did.

    Two rules survive from earlier rounds and still hold:

    - The cream face mask stays well clear of the cream chest. When the two pale
      areas met, the cat lost its face and read as one lump with ears stuck in
      the middle. There is now a deliberate band of fur between them.
    - The tail is one tapered polygon, never a chain of circles. Circles left
      scalloped bumps along the silhouette, and a row of same-sized bumps low on
      a cat reads unmistakably as feet. For the same reason it is kept off the
      cat's underside entirely and laid out along the rug to the viewer's right,
      where it has a silhouette of its own and nothing can take it for a leg.
    """
    top = 116 - pose.back + pose.stretch
    floor = 170 + pose.belly
    hx, hy = 94 - pose.stretch, 122 - pose.lift

    # The loaf, as three overlapping ellipses: the head, the domed back, and a
    # low wide base that joins them into one flat-bottomed mass. Without the base
    # the head and body met the rug at two separate points and the cat perched
    # rather than sat.
    loaf = (
        (hx, hy, hx + 46, hy + 47),
        (116, top, 172 + pose.stretch, 169),
        (110 - pose.stretch, 148 + pose.stretch, 170 + pose.stretch, floor),
    )
    ears = (
        [
            (hx + 4, hy + 12),
            (hx + 10 + pose.ear_flick, hy - 16 - pose.ears - pose.ear_flick),
            (hx + 24, hy + 5),
        ],
        [(hx + 28, hy + 3), (hx + 43, hy - 17 - pose.ears), (hx + 47, hy + 10)],
    )
    # Out of the rump and away to the right, lying along the rug with the tip
    # curling up. Kept *outside* the body for its whole visible length so it owns
    # a silhouette of its own: tucked against the cat it read as a shadow, and
    # run along the underside — where every earlier version put it — a tapered
    # lump low on a cat reads as feet no matter how smoothly it is drawn.
    #
    # `tail` lifts the outer half only. Lifting the root as well swung the whole
    # thing like a rudder instead of thumping it.
    spine = [
        (161, 155, 6.4), (171, 163 - pose.tail // 2, 5.2), (183, 167 - pose.tail, 3.8),
        (192, 163 - pose.tail, 2.4), (194, 157 - pose.tail, 0.9),
    ]

    # Pass one: the whole animal as a single dark silhouette.
    a.poly(tapered_stroke([(x, y, w + 1) for x, y, w in spine]), CAT_LINE)
    for pts in ears:
        a.poly(grow(pts), CAT_LINE)
    for x0, y0, x1, y1 in loaf:
        a.ellipse(x0 - 1, y0 - 1, x1 + 1, y1 + 1, CAT_LINE)

    # Pass two: fill inside it. The tail goes down first so the body covers where
    # it emerges; what is left is one continuous outline with no internal seam.
    a.poly(tapered_stroke(spine), CAT_TAIL)
    for x0, y0, x1, y1 in loaf:
        a.ellipse(x0, y0, x1, y1, CAT_FUR)
    # Three short bands down the near flank, before the ears so an ear always
    # wins, and well clear of them anyway.
    #
    # They used to be two matching arcs side by side. Adjacent humps of the same
    # size read unmistakably as a pair of arches rather than as fur, and the left
    # one began behind the far ear and cut straight across it. Uneven marks
    # running down the flank are what stripes on a loaf actually look like from
    # the side.
    # Each bends outward on the way down so it follows the roundness of the back.
    # Drawn as straight dashes they read as claw marks rather than as fur.
    for stripe in (
        ((147, 3), (149, 10), (153, 16)),
        ((157, 4), (159, 11), (163, 18)),
        ((166, 8), (168, 14), (171, 19)),
    ):
        a.d.line([(x, top + y) for x, y in stripe], fill=CAT_DARK, width=2)

    for pts in ears:
        a.poly(pts, CAT_FUR)
    a.poly(
        [
            (hx + 8, hy + 8),
            (hx + 11 + pose.ear_flick, hy - 8 - pose.ears),
            (hx + 21, hy + 5),
        ],
        CAT_EAR,
    )
    a.poly(
        [(hx + 32, hy + 4), (hx + 41, hy - 10 - pose.ears), (hx + 43, hy + 7)],
        CAT_EAR,
    )

    # The tail again, on top, because the body fill just buried the flank it
    # curls over. Edged in CAT_DARK rather than in CAT_LINE: it needs to read as
    # a separate limb lying against the side without becoming a second outline.
    a.poly(tapered_stroke(spine), CAT_TAIL, CAT_DARK)

    # A pixel of light along the spine and the crown. This is what holds the
    # brown cat apart from the brown sideboard behind it; without it the top edge
    # dissolves into the furniture.
    a.arc(117, top + 1, 171 + pose.stretch, 168, 205, 345, CAT_LIGHT, 1)
    a.arc(hx + 1, hy + 1, hx + 45, hy + 46, 158, 262, CAT_LIGHT, 1)

    # A hint of shoulder where the head meets the body. Shading only — an outline
    # here is exactly the seam this cat was redrawn to lose.
    a.arc(hx + 2, hy + 2, hx + 44, hy + 44, 330, 18, CAT_DARK, 1)

    # Chest and belly: the cream underside, low and to the right of the face.
    # Kept wider and shallower than the face mask — at similar sizes the two pale
    # ovals read as a pair rather than as a face and a chest.
    a.ellipse(134, 152, 168, floor, CAT_CREAM)
    # One tucked forepaw, suggested and no more. Drawn as a crease in the cream
    # rather than as a shape with its own outline, which is what made the last
    # set of paws read as beads.
    a.arc(139, 156, 157, 172, 202, 338, (216, 205, 186), 1)

    draw_cat_face(a, pose, hx, hy)


def draw_cat_face(a: Art, pose: Pose, hx: int, hy: int) -> None:
    """The face, positioned from the head's own origin."""
    a.ellipse(hx + 2, hy + 20, hx + 32, hy + 47, CAT_CREAM)

    # Two eyes, the far one smaller — this is a three-quarter view. Closed is the
    # resting state and by far the most common, so it stays the plain arc it
    # always was; opening them is what a reaction does.
    draw_cat_eye(a, pose, hx + 5, hy + 14, 14, 12)
    draw_cat_eye(a, pose, hx + 22, hy + 16, 12, 10)

    # Nose, then either the closed mouth or an open one.
    a.poly(
        [(hx + 12, hy + 28), (hx + 20, hy + 28), (hx + 16, hy + 33)], (198, 138, 134)
    )
    a.d.line([(hx + 16, hy + 33), (hx + 16, hy + 35)], fill=CAT_LINE, width=1)
    if pose.yawn:
        # Grows in both directions, and at full stretch reaches the chin. A
        # modest mouth read as a small "o" of surprise; the joke needs the whole
        # front of the cat to be hinge.
        width, depth = 10 + pose.yawn * 2, 3 + pose.yawn * 3
        mx, my = hx + 16, hy + 34
        a.ellipse(mx - width // 2, my, mx + width // 2, my + depth, CAT_LINE)
        a.ellipse(
            mx - width // 4, my + depth // 2, mx + width // 4, my + depth - 1,
            (176, 104, 104),
        )
    else:
        a.arc(hx + 9, hy + 32, hx + 23, hy + 40, 20, 160, CAT_LINE, 1)

    for wy, dy in ((28, -2), (32, 0), (36, 2)):
        a.d.line(
            [(hx + 4, hy + wy), (hx - 8, hy + wy + dy)], fill=(214, 200, 180), width=1
        )


# An open eye is the same size on both sides of the face, however the lids around
# it differ. Scaling the far eye down with its lid was correct perspective and
# looked simply wrong — one small eye and one large one reads as a squint, not as
# a three-quarter view.
EYE_WIDE = (10, 10)
EYE_HALF = (10, 5)


def draw_cat_eye(a: Art, pose: Pose, x: int, y: int, width: int, height: int) -> None:
    """One eye, closed, half or wide.

    The three states are drawn rather than tweened. At twelve pixels across there
    is nothing between a line and a circle to interpolate through, and trying to
    find one produced a smear that read as a wound.
    """
    if pose.eyes == 0:
        a.arc(x, y, x + width, y + height, 200, 340, CAT_LINE, 2)
        return

    ew, eh = EYE_WIDE if pose.eyes == 2 else EYE_HALF
    ex = x + (width - ew) // 2 - pose.gaze
    ey = y + (height - eh) // 2 + 1
    a.ellipse(ex, ey, ex + ew, ey + eh, CAT_LINE)
    if pose.eyes == 2:
        a.rect(ex + 2, ey + 2, ex + 4, ey + 4, (236, 232, 224))
    # The upper lid stays drawn over the top of the eye, so a wide-awake cat
    # still reads as the same cat rather than as a startled one. This is where
    # the three-quarter view survives: the lids differ, the eyes do not.
    a.arc(x, y, x + width, y + height, 210, 330, CAT_LINE, 2)


# ----------------------------------------------------------------- clips ---

# The cat's whole repertoire, one pose per frame, played at the tick rate.
#
# `breathe` loops forever; everything else plays once and hands back. Every clip
# starts and ends at rest so the handover is invisible — a clip that ended mid
# pose snapped when the breathing resumed.
#
# These are the personality. The room is played straight so that the cat does not
# have to be, and the reactions are where that pays off: they are the joke. They
# are also deliberately rare. A cat that performed on every track change would be
# a toy, and the point is an animal that mostly ignores you.

# One pixel of rise along the spine, one of spread underneath, and no more. At
# two pixels the whole cat visibly grew and shrank, which reads as bobbing. The
# belly lags the back on purpose: moving both together gave two states and looked
# like a blinking light, while offsetting them gives four and it reads as air
# going in and out.
_BREATH = (
    (0, 0), (0, 0), (0, 0),
    (1, 0), (1, 1), (1, 1), (1, 1), (1, 1),
    (0, 1), (0, 0), (0, 0), (0, 0),
)

CLIPS: dict[str, tuple[Pose, ...]] = {
    "breathe": tuple(Pose(back=b, belly=y) for b, y in _BREATH),

    # Music starts: the head comes up, the ears go hard forward, and the cat
    # looks at the speakers — then loses interest, which is the whole gag.
    "perk": (
        Pose(), Pose(lift=1, ears=1, eyes=1),
        Pose(lift=3, ears=3, eyes=2), Pose(lift=4, ears=4, eyes=2),
        Pose(lift=4, ears=4, eyes=2), Pose(lift=4, ears=4, eyes=2, gaze=1),
        Pose(lift=4, ears=4, eyes=2, gaze=1), Pose(lift=4, ears=3, eyes=2, gaze=1),
        Pose(lift=3, ears=2, eyes=2), Pose(lift=3, ears=1, eyes=1),
        Pose(lift=2, ears=1, eyes=1), Pose(lift=1, eyes=1),
        Pose(lift=1), Pose(), Pose(belly=1), Pose(),
    ),

    # Track change, most of the time: one ear, twice, and nothing else moves.
    "twitch": (
        Pose(), Pose(ear_flick=2), Pose(ear_flick=4), Pose(ear_flick=1),
        Pose(ear_flick=3), Pose(ear_flick=1), Pose(), Pose(),
    ),

    # Track change, occasionally: an eye opens and slides towards the stereo.
    "glance": (
        Pose(), Pose(eyes=1), Pose(eyes=2), Pose(eyes=2, gaze=1),
        Pose(eyes=2, gaze=2), Pose(eyes=2, gaze=2), Pose(eyes=2, gaze=2),
        Pose(eyes=2, gaze=2), Pose(eyes=2, gaze=1), Pose(eyes=2),
        Pose(eyes=1), Pose(eyes=1), Pose(), Pose(),
    ),

    # Too many skips in a row. Half an eye open and the tail slapped down twice,
    # which is the most a cat this shape is prepared to say about it.
    "thump": (
        Pose(), Pose(eyes=1, tail=3), Pose(eyes=1, tail=6), Pose(eyes=1, tail=7),
        Pose(eyes=1, tail=3), Pose(eyes=1), Pose(eyes=1),
        Pose(eyes=1, tail=5), Pose(eyes=1, tail=7), Pose(eyes=1, tail=3),
        Pose(eyes=1), Pose(eyes=1), Pose(), Pose(),
    ),

    # A long silence: one enormous yawn, the loaf pulled out long, and then it
    # settles and is gone. The eyes squeeze shut at the peak — a yawn with the
    # eyes open reads as a scream.
    "stretch": (
        Pose(), Pose(lift=1, eyes=1), Pose(lift=2, ears=1, eyes=2),
        Pose(lift=2, eyes=1, yawn=1, stretch=1),
        Pose(lift=3, yawn=2, stretch=3), Pose(lift=3, yawn=3, stretch=4),
        Pose(lift=3, yawn=3, stretch=5), Pose(lift=3, yawn=3, stretch=5),
        Pose(lift=2, yawn=3, stretch=5), Pose(lift=2, yawn=2, stretch=4),
        Pose(lift=1, yawn=1, stretch=3), Pose(lift=1, eyes=1, stretch=2),
        Pose(eyes=1, stretch=1), Pose(stretch=1), Pose(),
        Pose(belly=1), Pose(back=1, belly=1), Pose(belly=1), Pose(), Pose(),
    ),
}

RESTING_CLIP = "breathe"


# -------------------------------------------------------------- artwork ---


def dominant_colour(image: Image.Image) -> tuple[int, int, int]:
    small = image.convert("RGB").resize((32, 32), Image.LANCZOS)
    quantised = small.quantize(colors=8, method=Image.Quantize.MEDIANCUT).convert("RGB")
    counts = quantised.getcolors(1024) or [(1, (128, 128, 128))]
    return max(counts)[1]


def display_colour(rgb: tuple[int, int, int]) -> tuple[int, int, int]:
    """An album colour made fit for the amp's readout.

    Covers arrive at any brightness: a near-black sleeve left the display looking
    broken and a near-white one blew the whole panel out. The hue is kept exactly
    as sampled — that is the part that personalises the room — and only lightness
    and saturation are pulled into a band that reads as a lit display.
    """
    hue, light, sat = colorsys.rgb_to_hls(*(c / 255 for c in rgb))
    light = min(0.72, max(0.46, light))
    sat = min(1.0, max(0.45, sat))
    r, g, b = colorsys.hls_to_rgb(hue, light, sat)
    return round(r * 255), round(g * 255), round(b * 255)


def sleeve_grade(when: str) -> dict:
    """The numbers `artwork.py` needs to grade live album art the same way the
    room around it was graded.

    Exported into layout.json rather than restated in the app, like every other
    piece of geometry here. `dim` is the vignette averaged across the sleeve —
    the sleeve is small enough that one number for the whole square is
    indistinguishable from evaluating it per pixel.
    """
    field = grade_field(when)
    x0, y0, x1, y1 = SLEEVE_FRAME
    cells = [(x, y) for y in range(y0, y1) for x in range(x0, x1)]
    vignette = sum(field.vignette[y][x] for x, y in cells) / len(cells)
    return {
        "gain": SLEEVE_GAIN,
        "saturation": SLEEVE_SAT,
        "steps": STEPS,
        "dim": round(vignette, 4),
        "wash": list(LIGHT[when]["wash"]),
    }


def grade_sleeve(artwork: Image.Image, when: str = "day") -> Image.Image:
    """Lift the album art out of the room's value band.

    This is the review's sharpest point: the one element in the room that changes
    per track was the same brightness as the frame around it. Gain and saturation
    fix that, and quantizing to the room's own step count stops the cover reading
    as a photograph pasted onto pixel art.

    The band's wash is applied here too. It used to arrive from the light overlay
    that covered the whole canvas, artwork included; now that the overlay is
    baked into the background, the sleeve has to dim with the room on its own or
    it goes back to looking like a sticker at midnight.

    **No dithering.** The room dithers inside its lighting ramps, but ordered
    dither across a 52-pixel cover is noise laid over the only part of the frame
    carrying real information, and recognising the record matters more than
    matching the shader.
    """
    g = sleeve_grade(when)
    wr, wg, wb, wa = g["wash"]
    alpha, gain, sat, steps, dim = wa / 255, g["gain"], g["saturation"], g["steps"], g["dim"]

    out = artwork.convert("RGB")
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g_, b = (c / 255 for c in px[x, y])
            r = r * (1 - alpha) + wr / 255 * alpha
            g_ = g_ * (1 - alpha) + wg / 255 * alpha
            b = b * (1 - alpha) + wb / 255 * alpha

            lum = 0.299 * r + 0.587 * g_ + 0.114 * b
            r = (lum + (r - lum) * sat) * gain * dim
            g_ = (lum + (g_ - lum) * sat) * gain * dim
            b = (lum + (b - lum) * sat) * gain * dim

            px[x, y] = tuple(
                round(max(0.0, min(1.0, c)) * steps) * 255 // steps for c in (r, g_, b)
            )
    return out


def fit_artwork(cover: Image.Image, size: int = 52) -> Image.Image:
    """Fit artwork entirely inside a square slot. Never crops.

    Smooth downscaling on the way in — nearest-neighbour would make a 600x600
    photographic cover jagged. Nearest-neighbour belongs at the other end, when
    the finished room is enlarged to 2x or more.
    """
    cover = cover.convert("RGB")
    w, h = cover.size
    scale = min(size / w, size / h)
    nw, nh = max(1, round(w * scale)), max(1, round(h * scale))
    art = cover.resize((nw, nh), Image.LANCZOS)

    fill = tuple(int(c * 0.55) for c in dominant_colour(cover))
    slot = Image.new("RGB", (size, size), fill)
    ox, oy = (size - nw) // 2, (size - nh) // 2
    slot.paste(art, (ox, oy))

    if (nw, nh) != (size, size):
        # A deliberate mount, so letterboxing does not read as a broken render.
        border = tuple(min(255, int(c * 1.6) + 20) for c in fill)
        ImageDraw.Draw(slot).rectangle(
            [ox - 1, oy - 1, ox + nw, oy + nh], outline=border, width=1
        )
    return slot


# ------------------------------------------------------------- assembly ---


# One authored shape at every hour; only the colours change. Three separately
# drawn patches would read as three different rooms, and the whole point of the
# three is that the room is the same and the light is not.
#
# `wash` covers the entire canvas, artwork included — a sleeve left at full
# brightness while the room dimmed read as a sticker pasted on. `lamp` is None in
# the daytime, which is what keeps the sconce off in the sunshine.
LIGHT = {
    "day": {
        # Paler than the sunlight actually is. A saturated yellow beam vanished
        # against the warm orange floorboards: on this floor the light has to
        # arrive as *brightness*, not as more of the colour already there.
        "wash": (0, 0, 0, 0),
        "beam": (255, 246, 212, 96),
        "spill": (255, 248, 224, 46),
        "sky": None,
        "moon": False,
    },
    "evening": {
        # Warm *and* a shade darker. A purely additive warm wash made the evening
        # room brighter than the daytime one, which is the wrong way round.
        "wash": (198, 112, 52, 46),
        "beam": (255, 174, 88, 74),
        "spill": (255, 192, 124, 36),
        "sky": (200, 112, 60, 155),
        "moon": False,
    },
    "night": {
        # Darker and much less blue than it first was. A high blue channel over
        # the room's warm green wall came out lavender-grey, which read as a
        # washed-out photograph rather than as a room at night. What sells night
        # is the cold room against the warm lamp, so the wash goes deeper and the
        # grade's lamp comes up to meet it.
        "wash": (16, 28, 58, 154),
        "beam": (152, 188, 236, 44),
        "spill": (152, 188, 236, 22),
        "sky": (14, 22, 56, 206),
        "moon": True,
    },
}

# The window's four panes, inside the frame and between the mullions. The view is
# baked once and retinted here rather than painted three times, so all three
# hours share one background image and cannot drift out of register.
WINDOW_PANES = (
    (216, 28, 252, 55), (256, 28, 292, 55),
    (216, 59, 252, 88), (256, 59, 292, 88),
)

# One band of light on one angle, from the window to the cat. It replaces a patch
# that used to sit in the far left corner, pointing away from both the window and
# the cat, and read as a stain on the floorboards rather than as daylight.
#
# The upper half crosses the bed faintly — that is the only reason the light on
# the floor reads as coming from the window at all, since the bed stands between
# the two. It is kept weak on purpose: the bed is not allowed to brighten.
SUNBEAM_BED = [(236, 97), (292, 97), (245, 152), (189, 152)]
# Widening as it crosses the boards, which is what carries it far enough left to
# reach the cat. Its leading edge lands across the tail and stops: the cat is
# meant to be silhouetted against the bright floor, not bleached by it.
SUNBEAM = [(189, 152), (245, 152), (200, 194), (128, 194)]
SUNBEAM_SPILL = [(179, 152), (257, 152), (212, 194), (116, 194)]
# Gaps cast by the window's own mullions: one running the length of the band, one
# across it. Without them the shape is just a bright quadrilateral.
SUNBEAM_GAPS = (
    [(252, 97), (256, 97), (209, 152), (205, 152)],
    [(205, 152), (209, 152), (154, 194), (149, 194)],
    [(166, 168), (228, 168), (224, 172), (160, 172)],
)

def light_overlay(when: str = "day") -> Image.Image:
    """The window's contribution for one time of day: sky, beam and wash.

    The lamp is deliberately *not* here. It used to be, as a set of nested
    ellipses, and the grade in `grade()` now casts its own halo from the same
    sconce — two halos on one lamp, stacked. The grade owns the lamp; this owns
    the window.

    Built from several translucent passes composited together rather than drawn
    into one: ImageDraw replaces pixels instead of blending them, so a beam drawn
    straight onto the night wash would cut a hole in it.
    """
    tone = LIGHT[when]
    layer = Image.new("RGBA", (WIDTH, HEIGHT), tone["wash"])

    beam = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    d = ImageDraw.Draw(beam)
    d.polygon(SUNBEAM_BED, fill=tone["spill"])
    d.polygon(SUNBEAM_SPILL, fill=tone["spill"])
    d.polygon(SUNBEAM, fill=tone["beam"])
    for gap in SUNBEAM_GAPS:
        d.polygon(gap, fill=(0, 0, 0, 0))
    layer.alpha_composite(beam)

    if tone["sky"] is not None:
        glass = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        d = ImageDraw.Draw(glass)
        for x0, y0, x1, y1 in WINDOW_PANES:
            d.rectangle([x0, y0, x1 - 1, y1 - 1], fill=tone["sky"])
        if tone["moon"]:
            d.ellipse([276, 31, 288, 43], fill=(238, 242, 230, 236))
        layer.alpha_composite(glass)

    return layer


# ----------------------------------------------------------------- grade ---
#
# "Lamplight", ported from the shader in the design review that proposed it
# (`work/grade.js.txt` in the Claude Design project). Every number below came out
# of that file: this is a port, not an interpretation of the pictures.
#
# What it is for: the room was criticised, fairly, for sitting in one value band
# with nothing for the cat to separate from, and for a lamp that lit nothing. The
# grade is a single per-pixel pass over the finished art that gives the room a
# key light, a warm/cool split between highlight and shadow, a vignette and a
# quantized palette.
#
# Two deliberate departures from the shader, both decided on the renders:
#
#   - its `cone` term is dropped. A beam thrown from the lamp across the room was
#     rejected twice during the polish pass, and the answer did not change when
#     the beam acquired soft edges.
#   - it dithers every pixel. That speckles flat wall and flat wood, which is the
#     opposite of this art style, so here the dither is driven by how fast the
#     lighting is actually changing — see `ramp_field`.

BAYER = tuple(
    tuple(v / 16 - 0.47 for v in row)
    for row in ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))
)

CONTRAST, LIFT = 1.18, -0.02
HIGHLIGHT_TINT, HIGHLIGHT_TONE = 0.22, (255, 196, 120)

# Warm highlights against cool shadows is the whole trick, and what counts as
# "cool" has to follow the hour. The shader used one plum-brown shadow at every
# hour; pushed into an already-blue night room it raised the blacks to mauve and
# took the blue out entirely — the room came out lighter at midnight than at
# noon. Night keeps a slate shadow so the lamp still reads as the warm thing.
# The strength has to follow the hour as well as the colour. Blending a shadow
# toward a tone *lifts* anything darker than that tone, which is invisible on a
# daylit room and disastrous on a night one — at full strength the night room's
# blacks all rose to slate and the lamp had nothing left to glow against.
SHADOW_TINT = {"day": 0.34, "evening": 0.34, "night": 0.16}
SHADOW_TONE = {
    "day": (92, 54, 58),
    "evening": (92, 54, 58),
    "night": (24, 32, 60),
}
VIGNETTE = 0.26
STEPS = 16
# The shader dithered at 1.1 — half a quantization step — over every pixel in the
# frame. At that strength an ordered dither stops reading as smoothing and starts
# reading as television static, so it is both weaker here and confined to the
# ramps. DITHER_REACH turns "how fast the light is changing at this pixel" into
# "how much dither it earns"; the room's light ramps run at a few thousandths per
# pixel, and a flat wall runs at zero.
DITHER, DITHER_REACH = 0.7, 90.0

# The cat: a warm rim over the top half, a darkening under the bottom half, and
# the whole animal taken down a little so it sits *in* the room rather than on it.
CAT_FORM, CAT_FORM_TONE = 0.30, (255, 206, 140)
CAT_DARK_MUL = 0.94

# The contact shadow, which is the grade's answer to "the cat floats". Far
# stronger than the flat one it replaces in draw_shadows.
CAT_SHADOW = 0.32
CAT_SHADOW_ELLIPSE = (146.0, 175.0, 66.0, 10.0)

# The sleeve is the one thing in the room that changes per track, and it was the
# same brightness as its own frame. Lifted, and allowed to throw light.
SLEEVE_FRAME = (24, 48, 80, 104)
SLEEVE_GAIN, SLEEVE_SAT = 1.14, 1.25
SLEEVE_SPILL, SLEEVE_SPILL_RANGE = 0.26, 36.0
SLEEVE_SPILL_TONE = (255, 206, 150)

# The sconce, as two radial adds: the halo on the wall and a wide, weak pool of
# warmth on the floor.
#
# The shader had both burning at every hour, so its daytime still has a lamp lit
# in the sunshine. The halo here is switched off during the day; the floor warmth
# is not, because it is doing the work of general warm bounce rather than of a
# lamp, and the daytime room needs it as much as any other.
LAMP_HALO = (132.0, 50.0, 88.0, 86.0, 0.34, (255, 196, 110))
FLOOR_WARMTH = (146.0, 158.0, 110.0, 56.0, 0.14, (255, 186, 120))
LAMP_BY_BAND = {"day": 0.0, "evening": 1.0, "night": 1.3}


def smoothstep(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def _radial(light, x: int, y: int) -> float:
    lx, ly, rx, ry, _, _ = light
    dx, dy = (x - lx) / rx, (y - ly) / ry
    return smoothstep(1.0 - math.hypot(dx, dy))


def _sleeve_distance(x: int, y: int) -> float:
    x0, y0, x1, y1 = SLEEVE_FRAME
    dx = max(x0 - x, 0, x - (x1 - 1))
    dy = max(y0 - y, 0, y - (y1 - 1))
    return math.hypot(dx, dy)


class GradeField:
    """The parts of the grade that depend only on where a pixel is.

    Built once per time of day and reused for the background and every cat frame.
    Recomputing this per frame would multiply a couple of hundred images by a
    couple of hundred thousand square roots each, for an answer that never
    changes.
    """

    def __init__(self, when: str) -> None:
        self.shadow_tone = SHADOW_TONE[when]
        self.shadow_tint = SHADOW_TINT[when]
        lamp = LAMP_BY_BAND[when]
        lights = [(FLOOR_WARMTH, 1.0)]
        if lamp > 0:
            lights.append((LAMP_HALO, lamp))

        self.add = [[(0.0, 0.0, 0.0)] * WIDTH for _ in range(HEIGHT)]
        self.vignette = [[1.0] * WIDTH for _ in range(HEIGHT)]
        # Kept apart from the vignette because the contact shadow has to be
        # skipped where the cat itself is, or the animal darkens its own shadow.
        self.shadow = [[0.0] * WIDTH for _ in range(HEIGHT)]
        ramp = [[0.0] * WIDTH for _ in range(HEIGHT)]

        for y in range(HEIGHT):
            add_row, vig_row, shadow_row, ramp_row = (
                self.add[y], self.vignette[y], self.shadow[y], ramp[y],
            )
            for x in range(WIDTH):
                ar = ag = ab = 0.0
                energy = 0.0

                for light, scale in lights:
                    f = _radial(light, x, y) * light[4] * scale
                    if f > 0:
                        r, g, b = light[5]
                        ar += f * r / 255
                        ag += f * g / 255
                        ab += f * b / 255
                        energy += f

                spill = smoothstep(1.0 - _sleeve_distance(x, y) / SLEEVE_SPILL_RANGE)
                if spill > 0 and not _in_sleeve(x, y):
                    f = spill * SLEEVE_SPILL
                    r, g, b = SLEEVE_SPILL_TONE
                    ar += f * r / 255
                    ag += f * g / 255
                    ab += f * b / 255
                    energy += f

                vx, vy = (x - 160) / 195, (y - 100) / 140
                vig = VIGNETTE * min(1.0, math.hypot(vx, vy)) ** 2.4

                cx, cy, crx, cry = CAT_SHADOW_ELLIPSE
                e = 1.0 - min(1.0, math.hypot((x - cx) / crx, (y - cy) / cry))
                shadow = smoothstep(e) * CAT_SHADOW if e > 0 else 0.0

                add_row[x] = (ar, ag, ab)
                vig_row[x] = 1.0 - vig
                shadow_row[x] = shadow
                # The vignette is deliberately left out of the dither ramp. It
                # varies by about one quantization step across the whole canvas,
                # so it bands once, softly, at an edge nobody will find — and
                # including it put dither on every flat surface in the room,
                # which is the one thing this style cannot have.
                ramp_row[x] = energy + shadow

        self.dither = _dither_field(ramp)


def _dither_field(ramp: list[list[float]]) -> list[list[float]]:
    """How hard to dither each pixel: proportional to how fast the *lighting* is
    changing there, and zero where nothing is changing at all.

    This is the whole reason flat surfaces stay flat. Quantizing a flat colour is
    harmless — it lands on one level and stays there — but dithering it adds
    noise to a wall that has nothing happening on it. The review asked for dither
    "only where the lamp gradient falls", and this is that, measured rather than
    masked by hand: the lamp halo, the floor warmth, the sleeve spill and the
    cat's contact shadow all earn it, and the flat wall between them does not.
    """
    field = [[0.0] * WIDTH for _ in range(HEIGHT)]
    for y in range(HEIGHT):
        for x in range(WIDTH):
            here = ramp[y][x]
            dx = abs(ramp[y][min(WIDTH - 1, x + 1)] - here)
            dy = abs(ramp[min(HEIGHT - 1, y + 1)][x] - here)
            field[y][x] = min(1.0, (dx + dy) * DITHER_REACH)
    return field


def _in_sleeve(x: int, y: int) -> bool:
    x0, y0, x1, y1 = SLEEVE_FRAME
    return x0 <= x < x1 and y0 <= y < y1


def feathered_mask(image: Image.Image) -> list[list[float]]:
    """A soft 0..1 mask of where the cat is, taken from its own alpha.

    The shader hardcoded an eighteen-point outline of the cat. Reading the alpha
    instead means the mask follows the animal automatically — including when it
    stretches, yawns or lifts its head, which that polygon could not.
    """
    alpha = image.getchannel("A")
    small = alpha.resize((80, 50), Image.LANCZOS)
    soft = small.resize((WIDTH, HEIGHT), Image.BILINEAR)
    data = soft.tobytes()
    return [
        [data[y * WIDTH + x] / 255 for x in range(WIDTH)] for y in range(HEIGHT)
    ]


def cat_form(
    r: float, g: float, b: float, y: int, cm: float
) -> tuple[float, float, float]:
    """The part of the grade that belongs to the cat and to nothing else.

    A warm rim over the top half of the animal, a darkening under the bottom
    half, and the whole of it taken down a little so it sits *in* the room rather
    than on it.

    Split out of `grade` so the room's treatment can be applied on its own. The
    record and the speakers are furniture: they are lit by the room, and a sprite
    that had to be handed a cat mask before it could be graded was carrying a
    dependency it has no business having.

    It stays inside `grade`'s pixel loop rather than becoming a second pass over
    the finished image, because a second pass would shade values that have
    already been quantized and put the cat off the room's sixteen-step ladder.
    """
    # Top half of the animal catches the lamp, bottom half falls away.
    t = max(0.0, min(1.0, (y - 104) / 70))
    f = (0.5 - t) * 2
    amount = cm * CAT_FORM
    if f > 0:
        r += (1 - r) * f * amount * CAT_FORM_TONE[0] / 255
        g += (1 - g) * f * amount * CAT_FORM_TONE[1] / 255
        b += (1 - b) * f * amount * CAT_FORM_TONE[2] / 255
    else:
        dark = 1 + f * amount * 1.5
        r, g, b = r * dark, g * dark, b * dark
    fade = 1 - (1 - CAT_DARK_MUL) * cm
    return r * fade, g * fade, b * fade


def grade(
    image: Image.Image, field: GradeField, cat_mask: list[list[float]] | None = None
) -> Image.Image:
    """Apply the Lamplight grade to one layer.

    Everything here depends only on where a pixel is and what colour it is, which
    is what makes it safe to run over a sprite in isolation: the same source
    colour at the same coordinate comes out the same whether it arrived in the
    background or in a layer composited on top of it.

    `cat_mask` is the one exception, and it is optional. Pass the cat's feathered
    silhouette to shade the animal, and the *resting* cat's silhouette when
    grading the background so the room darkens under it in the same place. Leave
    it out for anything that is not a cat.

    Grading each layer on its own is an approximation — quantizing the cat and
    the floor separately is not the same arithmetic as quantizing the finished
    frame once. It is the usual production compromise, and the rendered result is
    what decides whether it holds up, not this reasoning.
    """
    out = image.convert("RGBA")
    px = out.load()

    for y in range(HEIGHT):
        add_row, vig_row, shadow_row, dither_row = (
            field.add[y], field.vignette[y], field.shadow[y], field.dither[y],
        )
        mask_row = cat_mask[y] if cat_mask is not None else None
        for x in range(WIDTH):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            r, g, b = r / 255, g / 255, b / 255
            sleeve = _in_sleeve(x, y)

            # Contrast about mid grey, applied to luminance and carried back into
            # the channels as a ratio so the hue survives.
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            lifted = max(0.0, min(1.0, (lum - 0.5) * CONTRAST + 0.5 + LIFT))
            k = lifted / lum if lum > 0 else 1.0
            r, g, b = r * k, g * k, b * k

            if sleeve:
                lum = 0.299 * r + 0.587 * g + 0.114 * b
                r = lum + (r - lum) * SLEEVE_SAT
                g = lum + (g - lum) * SLEEVE_SAT
                b = lum + (b - lum) * SLEEVE_SAT
                r, g, b = r * SLEEVE_GAIN, g * SLEEVE_GAIN, b * SLEEVE_GAIN
            else:
                # Warm the highlights, cool-and-purple the shadows. This split is
                # what stops the room reading as one flat value band.
                ws, wh = (1 - lifted) * field.shadow_tint, lifted * HIGHLIGHT_TINT
                shade = field.shadow_tone
                r = r * (1 - ws) + shade[0] / 255 * ws
                g = g * (1 - ws) + shade[1] / 255 * ws
                b = b * (1 - ws) + shade[2] / 255 * ws
                r += (1 - r) * wh * HIGHLIGHT_TONE[0] / 255
                g += (1 - g) * wh * HIGHLIGHT_TONE[1] / 255
                b += (1 - b) * wh * HIGHLIGHT_TONE[2] / 255

            ar, ag, ab = add_row[x]
            r += (1 - r) * ar
            g += (1 - g) * ag
            b += (1 - b) * ab

            cm = mask_row[x] if mask_row is not None else 0.0
            if cm > 0.02:
                r, g, b = cat_form(r, g, b, y, cm)

            # Vignette everywhere; the contact shadow only on the floor beside
            # the cat, never on the cat, which would darken its own shadow.
            m = vig_row[x]
            if cm < 0.5:
                m *= 1.0 - shadow_row[x] * (1.0 - cm)
            r, g, b = r * m, g * m, b * m

            step = dither_row[x] * DITHER * BAYER[y & 3][x & 3] / STEPS
            px[x, y] = (
                round(max(0.0, min(1.0, r + step)) * STEPS) * 255 // STEPS,
                round(max(0.0, min(1.0, g + step)) * STEPS) * 255 // STEPS,
                round(max(0.0, min(1.0, b + step)) * STEPS) * 255 // STEPS,
                a,
            )
    return out


def draw_shadows(a: Art) -> None:
    """Contact shadows for the furniture. Everything floated before these.

    The cat's own shadow is *not* here any more — the grade casts a far stronger
    one, in a better place, and two stacked would be a smear. Nothing in the
    grade touches the sideboard, the speakers or the bed, though, so those stay:
    delete them and the furniture floats again, which is the criticism this whole
    exercise is answering.

    Offset down and to the viewer's left, away from the window, so they agree
    with the beam.
    """

    def shapes(d: ImageDraw.ImageDraw) -> None:
        d.rectangle([8, 152, 170, 157], fill=SHADOW_SOFT)
        d.ellipse([14, 154, 32, 162], fill=SHADOW)
        for x0, x1 in ((0, 18), (172, 196)):
            d.ellipse([x0, 152, x1, 161], fill=SHADOW)

        # The bed stands further back, so its shadow is longer and softer.
        d.rectangle([204, 180, 316, 187], fill=SHADOW_SOFT)
        for x0, x1 in ((208, 230), (294, 316)):
            d.ellipse([x0, 183, x1, 192], fill=SHADOW)

    a.shade(shapes)


def record_angle(index: int) -> float:
    return index * RECORD_ARC / RECORD_FRAMES


def build_background() -> Image.Image:
    """Everything static: no cat, no record, no album artwork, no lighting."""
    a = Art()
    draw_shell(a)
    draw_lamp(a)
    draw_window(a)
    draw_bed(a)
    draw_sideboard(a)
    draw_amp(a)
    draw_speaker(a, 0, 14)
    draw_speaker(a, 176, 192)
    draw_sleeve_frame(a)
    draw_turntable(a)
    draw_plant(a)
    draw_rug(a)
    draw_shadows(a)
    return a.img


def build_cat_frame(pose: Pose = RESTING) -> Image.Image:
    """The cat alone, on transparency, at full canvas size.

    Full-canvas frames rather than a cropped sprite plus an offset: the frames
    are a couple of kilobytes each and it removes a whole class of
    off-by-one placement bugs. It matters more now than it did — the cat changes
    size and position across the reactions, and a cropped sprite would need an
    offset per frame.
    """
    a = Art()
    draw_cat(a, pose)
    return a.img


def build_record_frame(index: int) -> Image.Image:
    """The record alone, on transparency, at full canvas size.

    Full canvas for the same reason the cat is: the frames are a kilobyte or two
    each and it removes a whole class of off-by-one placement bugs.
    """
    a = Art()
    draw_record(a, record_angle(index), (40, 40, 44))
    return a.img


def lit_sprite(sprite: Image.Image, when: str) -> Image.Image:
    """The window's light on a sprite, without lighting the canvas around it.

    The background is graded *after* `light_overlay`, so anything composited on
    top of it has to carry the same wash or it will not belong to the room. At
    night that wash is alpha 154 over everything, and a sprite that skipped it
    would read as a lit hole cut in the furniture.

    Restoring the sprite's own alpha afterwards is the whole trick: compositing
    the overlay fills the empty canvas with wash too, and putting the original
    alpha back is what confines the light to the pixels the sprite actually has.
    """
    lit = sprite.copy()
    lit.alpha_composite(light_overlay(when))
    lit.putalpha(sprite.getchannel("A"))
    return lit


@lru_cache(maxsize=4)
def grade_field(when: str) -> GradeField:
    return GradeField(when)


@lru_cache(maxsize=4)
def graded_background(when: str) -> Image.Image:
    """The room for one time of day, lit and graded. Callers must copy it."""
    lit = build_background()
    lit.alpha_composite(light_overlay(when))
    return grade(lit, grade_field(when), feathered_mask(build_cat_frame()))


@lru_cache(maxsize=256)
def graded_cat(when: str, pose: Pose) -> Image.Image:
    frame = build_cat_frame(pose)
    return grade(frame, grade_field(when), feathered_mask(frame))


@lru_cache(maxsize=64)
def graded_record(when: str, index: int) -> Image.Image:
    return grade(lit_sprite(build_record_frame(index), when), grade_field(when))


def build_room(
    artwork: Image.Image,
    *,
    when: str = "day",
    pose: Pose = RESTING,
    lit: bool = True,
    record: int = 0,
) -> Image.Image:
    """Compose the way the app does, so proofs and runtime cannot drift apart.

    Layer by layer, exactly as `scene.compose` does it: a graded background, the
    record, artwork graded on its own, then a graded cat. Grading the finished
    frame in one pass — which is what the design review's shader did — would look
    slightly better and would not be what ships.
    """
    room = graded_background(when).copy()
    room.paste(grade_sleeve(artwork, when), (SLEEVE_SLOT[0], SLEEVE_SLOT[1]))
    room.alpha_composite(graded_record(when, record))
    colour = dominant_colour(artwork)
    label = Image.new("RGB", (LABEL_SLOT[2], LABEL_SLOT[3]), colour)
    room.paste(label, (LABEL_SLOT[0], LABEL_SLOT[1]))
    if lit:
        panel = Image.new("RGB", (AMP_SLOT[2], AMP_SLOT[3]), display_colour(colour))
        room.paste(panel, (AMP_SLOT[0], AMP_SLOT[1]))
    room.alpha_composite(graded_cat(when, pose))
    return room


def scale(image: Image.Image, factor: int) -> Image.Image:
    return image.resize(
        (image.width * factor, image.height * factor), Image.Resampling.NEAREST
    )


DEMO_COVERS = (
    ((214, 92, 76), (38, 54, 84), (238, 214, 168)),
    ((64, 124, 132), (232, 236, 226), (196, 118, 62)),
    ((122, 84, 148), (240, 200, 96), (34, 38, 54)),
)


def build_demo_cover(index: int) -> Image.Image:
    """An invented sleeve for demo mode.

    Drawn rather than borrowed: demo mode must not ship anyone else's artwork.
    """
    base, accent, light = DEMO_COVERS[index]
    cover = Image.new("RGB", (96, 96), base)
    d = ImageDraw.Draw(cover)
    if index == 0:
        d.polygon([(0, 96), (96, 0), (96, 40), (36, 96)], fill=accent)
        d.ellipse([20, 16, 60, 56], fill=light)
    elif index == 1:
        d.rectangle([0, 52, 96, 96], fill=accent)
        for i, x in enumerate(range(8, 92, 14)):
            d.rectangle([x, 52 - (i % 4) * 11 - 8, x + 9, 52], fill=light)
    else:
        for r in (44, 32, 20, 10):
            d.ellipse([48 - r, 48 - r, 48 + r, 48 + r], outline=accent, width=3)
        d.rectangle([0, 78, 96, 96], fill=light)
    return cover


def export_assets() -> None:
    """Write the PNGs the app loads at runtime."""
    assets = ROOT / "src" / "bedroom" / "assets"
    assets.mkdir(parents=True, exist_ok=True)

    demo = assets / "demo"
    demo.mkdir(exist_ok=True)
    for i in range(len(DEMO_COVERS)):
        build_demo_cover(i).save(demo / f"cover-{i:02d}.png")

    # The grade runs over a finished frame, and the app composites at runtime, so
    # the window's light is folded into the background here rather than shipped
    # as a separate overlay. That is what costs a full set of art per time of
    # day — and it is the only way a per-pixel grade and a live composite can
    # both exist.
    room = build_background()
    resting = build_cat_frame()
    resting_mask = feathered_mask(resting)

    cats = assets / "cat"
    records = assets / "record"
    for old in assets.glob("light-*.png"):
        old.unlink()
    if (assets / "background.png").exists():
        (assets / "background.png").unlink()
    # Stale frames from a clip that has since been shortened would still load, so
    # the trees are cleared rather than written over.
    for tree in (cats, records):
        for old in tree.rglob("*.png"):
            old.unlink()

    for when in TIMES_OF_DAY:
        field = GradeField(when)
        lit = room.copy()
        lit.alpha_composite(light_overlay(when))
        grade(lit, field, resting_mask).save(assets / f"background-{when}.png")

        band = cats / when
        band.mkdir(parents=True, exist_ok=True)
        for clip, poses in CLIPS.items():
            for i, pose in enumerate(poses):
                frame = build_cat_frame(pose)
                graded = grade(frame, field, feathered_mask(frame))
                graded.save(band / f"{clip}-{i:02d}.png")

        # No cat mask here: the record is furniture, lit by the room and by
        # nothing else.
        band = records / when
        band.mkdir(parents=True, exist_ok=True)
        for i in range(RECORD_FRAMES):
            frame = lit_sprite(build_record_frame(i), when)
            grade(frame, field).save(band / f"{i:02d}.png")

    (assets / "layout.json").write_text(
        json.dumps(
            {
                "canvas": {"width": WIDTH, "height": HEIGHT},
                "sleeve_slot": dict(
                    zip(("x", "y", "width", "height"), SLEEVE_SLOT, strict=True)
                ),
                "label_slot": dict(
                    zip(("x", "y", "width", "height"), LABEL_SLOT, strict=True)
                ),
                "amp_slot": dict(
                    zip(("x", "y", "width", "height"), AMP_SLOT, strict=True)
                ),
                "cat_clips": {clip: len(poses) for clip, poses in CLIPS.items()},
                "resting_clip": RESTING_CLIP,
                "record_frames": RECORD_FRAMES,
                "times_of_day": list(TIMES_OF_DAY),
                "sleeve_grade": {w: sleeve_grade(w) for w in TIMES_OF_DAY},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    bands = len(TIMES_OF_DAY)
    total = sum(len(poses) for poses in CLIPS.values()) * bands
    print(f"assets      {len(CLIPS)} clips x {bands} bands, "
          f"{total} cat frames -> src/bedroom/assets/")
    print(f"            {RECORD_FRAMES * bands} record frames")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    export_assets()
    refs = ROOT / "docs" / "reference"

    covers = {
        "spotify": refs / "cover-spotify.png",
        "foobar2000": refs / "cover-foobar2000.png",
        "brave": refs / "cover-brave.png",
    }
    available = {k: v for k, v in covers.items() if v.exists()}
    if not available:
        print("No covers in docs/reference — run tools/dump_artwork.py first.")
        return 1

    for name, path in available.items():
        cover = Image.open(path)
        art = fit_artwork(cover)
        room = build_room(art)
        out = OUT / f"room-day-{name}-2x.png"
        scale(room, 2).convert("RGB").save(out)
        print(f"{name:11s} {cover.size[0]}x{cover.size[1]:<4d} -> {out.name}")

    # The same room at all three hours, so the three can be compared as one set
    # rather than one at a time.
    hero = Image.open(next(iter(available.values())))
    art = fit_artwork(hero)
    for when in TIMES_OF_DAY:
        out = OUT / f"room-{when}-2x.png"
        scale(build_room(art, when=when), 2).convert("RGB").save(out)
        print(f"{when:11s} {'':9s} -> {out.name}")

    def animate(name: str, frames: list[Image.Image]) -> None:
        out = OUT / f"{name}.gif"
        frames[0].save(
            out, save_all=True, append_images=frames[1:], duration=TICK_MS, loop=0
        )
        print(f"{name:11s} {len(frames):2d} frames    -> {out.name}")

    # One tick is one authored record frame, which is what the app does, so the
    # record turns at its real rate in every proof it appears in.
    for clip, poses in CLIPS.items():
        animate(
            f"cat-{clip}",
            [
                scale(build_room(art, pose=p, record=i).convert("RGB"), 2)
                for i, p in enumerate(poses)
            ],
        )

    # The turntable on its own loop: the cat is at rest here on purpose, so the
    # question "is the record competing with the animal" can actually be looked at.
    animate(
        "record-spin",
        [
            scale(build_room(art, record=i).convert("RGB"), 2)
            for i in range(RECORD_FRAMES)
        ],
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
