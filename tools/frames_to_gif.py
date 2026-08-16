"""Assemble captured window frames into a GIF.

The counterpart to `capture_window.ps1 -Seconds`, which grabs the frames. Kept
separate because the capture has to be Win32 and the assembly wants Pillow.

Two things here are not the defaults, and both are the same rule the room's own
art follows:

- **One palette for the whole loop.** Pillow will happily pick a fresh palette
  per frame, which makes flat surfaces shimmer between frames even though the
  source pixels never changed. The palette is built once, from frames sampled
  across the whole recording, and every frame is mapped onto it.
- **No dithering.** Ordered dither across flat wall and flat wood is the one
  thing this art style cannot survive — `docs/art-brief.md` says so at length,
  and it would be perverse to have the bake respect that and the recording undo
  it.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

# How many frames to sample when building the shared palette. The room only has
# a few hundred colours in it, so this is plenty, and it keeps the palette pass
# quick on a long recording.
PALETTE_SAMPLES = 12


def build_palette(frames: list[Image.Image]) -> Image.Image:
    """One palette for every frame, taken from a strip of samples across the loop.

    Sampled across the recording rather than off the first frame: a loop that
    starts paused and ends playing would otherwise have no palette entries for
    anything the lit room does.
    """
    step = max(1, len(frames) // PALETTE_SAMPLES)
    sampled = frames[::step][:PALETTE_SAMPLES]
    width, height = sampled[0].size
    strip = Image.new("RGB", (width, height * len(sampled)))
    for i, frame in enumerate(sampled):
        strip.paste(frame, (0, i * height))
    # 255 rather than 256, leaving one index spare: some GIF readers treat a full
    # 256-colour table plus transparency as malformed.
    return strip.quantize(colors=255, method=Image.Quantize.MEDIANCUT)


def main(argv: list[str]) -> int:
    if len(argv) != 4:
        print("usage: frames_to_gif.py <frames-dir> <out.gif> <interval-ms>")
        return 2
    source, out, interval = Path(argv[1]), Path(argv[2]), int(argv[3])

    paths = sorted(source.glob("frame-*.png"))
    if not paths:
        print(f"No frames in {source}")
        return 1

    frames = [Image.open(p).convert("RGB") for p in paths]
    palette = build_palette(frames)
    mapped = [
        f.quantize(palette=palette, dither=Image.Dither.NONE) for f in frames
    ]

    out.parent.mkdir(parents=True, exist_ok=True)
    mapped[0].save(
        out,
        save_all=True,
        append_images=mapped[1:],
        duration=interval,
        loop=0,
        optimize=True,
    )
    size = out.stat().st_size
    seconds = len(frames) * interval / 1000
    print(f"gif    {len(frames)} frames, {seconds:.1f}s, "
          f"{frames[0].width}x{frames[0].height}, {size / 1_000_000:.1f} MB")
    print(f"saved  {out}")
    if size > 10_000_000:
        print("       Large for a README. Run the app at 2x, or record fewer seconds.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
