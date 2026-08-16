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

import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "proof"

WIDTH, HEIGHT = 320, 200

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

SPEAKER = (44, 44, 48)
SPEAKER_DARK = (24, 24, 27)
SPEAKER_RIM = (66, 66, 71)

CAT_CREAM = (240, 231, 214)
CAT_FUR = (146, 114, 84)
CAT_DARK = (108, 80, 57)
CAT_EAR = (198, 148, 146)
CAT_LINE = (70, 50, 36)

RUG = (238, 228, 208)
RUG_EDGE = (214, 200, 173)

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

BED_LINEN = (238, 233, 219)
BED_BLANKET = (86, 106, 82)
BED_BLANKET_D = (68, 86, 66)

MUG = (108, 140, 150)
FRAME_MAT = (232, 224, 205)

AMP_FACE = (52, 48, 46)
AMP_GLOW = (126, 214, 176)

SUNPATCH = (255, 226, 150, 64)


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

    # Mattress, then two pillows resting on it against the headboard.
    a.rect(218, 126, 318, 142, BED_LINEN)
    a.rect(218, 126, 318, 129, (250, 247, 238))
    a.outline_rect(218, 126, 318, 142, OUTLINE)

    for px in (220, 258):
        a.rect(px + 5, 106, px + 37, 128, BED_LINEN)
        a.ellipse(px, 106, px + 14, 128, BED_LINEN)
        a.ellipse(px + 28, 106, px + 42, 128, BED_LINEN)
        a.arc(px, 106, px + 14, 128, 90, 270, OUTLINE, 1)
        a.arc(px + 28, 106, px + 42, 128, 270, 90, OUTLINE, 1)
        a.rect(px + 6, 106, px + 36, 107, OUTLINE)
        a.rect(px + 6, 127, px + 36, 128, OUTLINE)
        a.arc(px + 8, 111, px + 34, 125, 200, 340, (219, 212, 196), 1)

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
    a.rect(16, 104, 172, 152, WOOD)
    a.rect(16, 104, 172, 109, WOOD_LIGHT)
    a.outline_rect(16, 104, 172, 152, OUTLINE)
    # Cupboards left, drawers centre, cupboard right — matches the reference.
    for x0, x1 in ((22, 74), (80, 122), (128, 166)):
        a.outline_rect(x0, 114, x1, 146, WOOD_DARK)
    a.rect(46, 128, 50, 132, WOOD_LIGHT)
    a.rect(52, 128, 56, 132, WOOD_LIGHT)
    a.rect(96, 122, 106, 125, WOOD_LIGHT)
    a.rect(96, 136, 106, 139, WOOD_LIGHT)
    a.rect(143, 128, 151, 132, WOOD_LIGHT)
    a.rect(20, 152, 26, 158, WOOD_DARK)
    a.rect(162, 152, 168, 158, WOOD_DARK)


def draw_amp(a: Art, lit: bool = True) -> None:
    """The blinking display. Sits on the sideboard front, clear of the cat."""
    a.rect(28, 114, 60, 124, AMP_FACE)
    a.outline_rect(28, 114, 60, 124, OUTLINE)
    if lit:
        a.rect(31, 117, 45, 121, AMP_GLOW)
        a.rect(48, 118, 50, 120, AMP_GLOW)
        a.rect(52, 118, 54, 120, (90, 160, 130))


def draw_speaker(a: Art, x0: int, x1: int, cone_offset: int = 0) -> None:
    a.rect(x0, 84, x1, 152, SPEAKER)
    a.rect(x0, 84, x1, 87, SPEAKER_RIM)
    a.outline_rect(x0, 84, x1, 152, OUTLINE)
    cx = (x0 + x1) // 2
    for cy, r in ((98, 5), (116, 6), (136, 8)):
        a.ellipse(cx - r, cy - r, cx + r, cy + r, SPEAKER_DARK, SPEAKER_RIM)
        a.ellipse(cx - 2, cy - 2 + cone_offset, cx + 2, cy + 2 + cone_offset, SPEAKER_RIM)
    a.rect(x0, 152, x1, 156, SPEAKER_DARK)


def draw_turntable(a: Art, record_angle: float, label_colour) -> None:
    """The one deliberate exception to the flat camera: a shallow top surface so
    the platter and tonearm stay readable."""
    import math

    # Plinth, then a shallow top face carrying the platter.
    a.rect(92, 88, 152, 104, (44, 44, 49))
    a.rect(92, 88, 152, 91, (64, 64, 70))
    a.outline_rect(92, 88, 152, 104, OUTLINE)
    a.poly([(94, 88), (150, 88), (146, 76), (98, 76)], (58, 58, 64), OUTLINE)

    # Platter and record.
    a.ellipse(102, 76, 144, 90, (30, 30, 34), (86, 86, 92))
    a.ellipse(105, 78, 141, 88, (18, 18, 21))
    for rr in (4, 7):
        a.ellipse(123 - rr * 2, 83 - rr // 2, 123 + rr * 2, 83 + rr // 2, None, (46, 46, 52))
    a.ellipse(117, 80, 129, 87, label_colour)

    # A groove highlight that rotates, so the record visibly spins.
    rad = math.radians(record_angle)
    a.d.line(
        [
            (123 + math.cos(rad) * 16, 83 + math.sin(rad) * 5),
            (123 - math.cos(rad) * 16, 83 - math.sin(rad) * 5),
        ],
        fill=(72, 72, 80),
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


def draw_picture(a: Art) -> None:
    a.rect(118, 22, 148, 50, WOOD)
    a.outline_rect(118, 22, 148, 50, OUTLINE)
    a.rect(122, 26, 144, 46, FRAME_MAT)
    a.outline_rect(122, 26, 144, 46, WOOD_DARK)


def draw_rug(a: Art) -> None:
    a.ellipse(96, 146, 200, 172, RUG_EDGE)
    a.ellipse(99, 148, 197, 170, RUG)
    for x in range(104, 194, 8):
        a.rect(x, 158, x + 3, 160, RUG_EDGE)


def draw_sleeve(a: Art, artwork: Image.Image) -> None:
    """56x56 sleeve with a 52x52 artwork slot inset 2px."""
    a.rect(24, 48, 80, 104, (232, 226, 210))
    a.outline_rect(24, 48, 80, 104, OUTLINE)
    a.paste(artwork, 26, 50)
    a.rect(24, 102, 80, 104, (206, 198, 180))


# ------------------------------------------------------------------- cat ---


def draw_cat(a: Art, breath: int = 0, ear_flick: int = 0, tail: int = 0) -> None:
    """A fat cat in three-quarter profile, head to the viewer's left.

    `breath` lifts the body by a pixel or two; `ear_flick` tilts the near ear;
    `tail` shifts the tail tip. All three run on the cat's own clock, never the
    music's.

    The head is kept deliberately clear of the body's cream chest. An earlier
    version let the two pale areas meet and the cat lost its face entirely,
    reading as one lump with ears stuck in the middle.
    """
    top = 116 - breath

    # Body: a heavy dome, wider than it is tall.
    a.ellipse(126, top, 174, 164, CAT_FUR, CAT_LINE)
    for sx in (140, 152, 164):
        a.arc(sx - 11, top + 3, sx + 11, top + 26, 195, 345, CAT_DARK, 3)
    # Chest sits low and to the right of the head, never touching the face.
    a.ellipse(134, 142, 162, 164, CAT_CREAM)

    # Tail in front of the body, curling round the base. Drawn after the body
    # on purpose: behind it, the body swallowed it completely.
    #
    # Outlined as one silhouette rather than per-segment. Outlining each segment
    # made it read as a row of separate balls instead of a tail.
    beads = (
        (172, 153, 7), (173, 160, 6), (167, 166, 6),
        (157, 169, 5), (147, 169, 5), (138, 166, 4),
    )
    shifted = [(tx, ty + (tail if i >= 2 else 0), r) for i, (tx, ty, r) in enumerate(beads)]
    for tx, ty, r in shifted:
        a.ellipse(tx - r - 1, ty - r - 1, tx + r + 1, ty + r + 1, CAT_LINE)
    for tx, ty, r in shifted:
        a.ellipse(tx - r, ty - r, tx + r, ty + r, CAT_FUR)
    for tx, ty, r in (shifted[1], shifted[3], shifted[5]):
        a.ellipse(tx - r + 1, ty - r, tx + r - 1, ty + r, CAT_DARK)

    # Ears, drawn before the head so the head outline cuts their bases cleanly.
    a.poly([(110, 130), (114 + ear_flick, 112 - ear_flick), (124, 130)], CAT_FUR, CAT_LINE)
    a.poly([(128, 128), (136, 111), (144, 130)], CAT_FUR, CAT_LINE)
    a.poly([(113, 128), (116 + ear_flick, 118), (121, 129)], CAT_EAR)
    a.poly([(131, 127), (135, 117), (140, 128)], CAT_EAR)

    # Head: a clear circle, well to the left, overlapping only the body's edge.
    a.ellipse(104, 126, 146, 166, CAT_FUR, CAT_LINE)
    for sx in (114, 124, 134):
        a.arc(sx - 9, 124, sx + 9, 140, 205, 335, CAT_DARK, 2)

    # Face: a compact cream mask, much smaller than the head.
    a.ellipse(106, 144, 134, 166, CAT_CREAM)
    a.ellipse(110, 150, 128, 164, (250, 244, 233))

    # Two closed eyes, the far one smaller — this is a three-quarter view.
    a.arc(110, 138, 122, 148, 200, 340, CAT_LINE, 2)
    a.arc(128, 140, 138, 148, 205, 335, CAT_LINE, 2)

    # Nose and mouth.
    a.poly([(116, 150), (122, 150), (119, 154)], (198, 138, 134))
    a.d.line([(119, 154), (119, 157)], fill=CAT_LINE, width=1)
    a.arc(112, 154, 119, 160, 250, 20, CAT_LINE, 1)
    a.arc(119, 154, 126, 160, 160, 290, CAT_LINE, 1)

    for wy, dy in ((149, -3), (153, 0), (157, 3)):
        a.d.line([(108, wy), (94, wy + dy)], fill=(236, 229, 216), width=1)


# -------------------------------------------------------------- artwork ---


def dominant_colour(image: Image.Image) -> tuple[int, int, int]:
    small = image.convert("RGB").resize((32, 32), Image.LANCZOS)
    quantised = small.quantize(colors=8, method=Image.Quantize.MEDIANCUT).convert("RGB")
    counts = quantised.getcolors(1024) or [(1, (128, 128, 128))]
    return max(counts)[1]


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


def light_overlay() -> Image.Image:
    """The window-shaped patch on the floor. One shape, recoloured per time of
    day — warm yellow now, amber at evening, pale blue at night."""
    layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.polygon([(8, 154), (78, 154), (92, 192), (4, 192)], fill=SUNPATCH)
    d.line([(43, 154), (52, 192)], fill=(255, 240, 190, 40), width=2)
    d.line([(12, 172), (86, 172)], fill=(255, 240, 190, 40), width=2)
    return layer


def build_room(artwork: Image.Image, *, breath: int = 0, cone: int = 0) -> Image.Image:
    a = Art()
    draw_shell(a)
    draw_picture(a)
    draw_window(a)
    draw_bed(a)
    draw_sideboard(a)
    draw_amp(a)
    draw_speaker(a, 0, 14, cone)
    draw_speaker(a, 176, 192, cone)
    draw_sleeve(a, artwork)
    draw_turntable(a, 25.0, dominant_colour(artwork))
    draw_plant(a)
    draw_rug(a)
    draw_cat(a, breath=breath)
    a.img.alpha_composite(light_overlay())
    return a.img


def scale(image: Image.Image, factor: int) -> Image.Image:
    return image.resize(
        (image.width * factor, image.height * factor), Image.Resampling.NEAREST
    )


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
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

    # Breathing proof: the cat's own rhythm, unrelated to playback.
    hero = Image.open(next(iter(available.values())))
    art = fit_artwork(hero)
    frames = [
        scale(build_room(art, breath=b).convert("RGB"), 2)
        for b in (0, 1, 2, 2, 1, 0, 0, 0)
    ]
    frames[0].save(
        OUT / "cat-breathing.gif",
        save_all=True,
        append_images=frames[1:],
        duration=220,
        loop=0,
    )
    print("breathing   8 frames      -> cat-breathing.gif")
    return 0


if __name__ == "__main__":
    sys.exit(main())
