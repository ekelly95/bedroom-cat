# Art brief — the bedroom

This document has two halves that serve different people.

**Part 1 is for you.** It is a prompt to paste into an image generator, plus the
rules the resulting images must respect to be useful. What comes back is
*reference only* — mood, colour, and the feel of the room. None of it ships.

**Part 2 is for me.** It is the exact pixel geometry I will hand-author the real
sprites to. It is written down here so the reference and the finished art are
aiming at the same room, and so a later session can pick the work up without
having to re-derive where anything goes.

---

## Part 1 — Generating the reference

### How to use it

Generate at whatever resolution the tool prefers — 1024×640 or similar, in a
roughly 16:10 shape. **Do not ask it for 320×200 pixel art.** Image generators
produce something that looks like pixel art from a distance but has thousands of
colours, soft edges, and an inconsistent grid, which is worse than useless as a
source. Ask for a clean illustration instead and let me do the pixel work.

Generate **three images with identical composition**, differing only in light.
If the tool supports it, generate the daytime one first and then ask for the
other two as re-lights of the same picture.

Send me whichever ones you like. If none of them feel right, say so — I can work
from a description alone, and a bad reference is worse than none.

### The prompt

> A cosy, lived-in small bedroom, drawn as a flat side-on cross-section — like
> looking into a dollhouse with the front wall removed. Strictly straight-on
> view, camera level with the middle of the room, no perspective vanishing
> point, no tilt. Wide 16:10 framing.
>
> Left half of the room: a long low wooden sideboard against the wall. Standing
> upright on it, leaning back against the wall, a square vinyl album sleeve
> facing the viewer dead-on. Beside it on the same sideboard, a record player
> with a visible circular platter and tonearm. A tall slim floor-standing
> speaker at the far left edge, and a second one at the right end of the
> sideboard.
>
> Right half of the room: a window with a simple four-pane frame and a sill,
> and below it a single bed with a rumpled blanket and one pillow.
>
> Centre foreground: a small round rug on the floorboards, and sitting on it,
> facing the speakers, an extremely fat cat — round as a loaf of bread, short
> legs tucked under, thick tail curled round, contented half-closed eyes. The
> cat is the heart of the picture.
>
> A few restrained extras and no more: a potted plant, a mug, a small framed
> picture on the wall.
>
> Mood: warm, quiet, lived-in, a little nostalgic. Uncluttered — every object
> clearly separated with breathing space around it, nothing overlapping
> confusingly.
>
> Style: limited-palette pixel-art-inspired illustration in the spirit of a
> late-1990s handheld game. Chunky readable shapes, strong silhouettes, flat
> colour, minimal shading. No gradients, no glow, no lens flare, no blur, no
> depth of field, no text or lettering anywhere.

Then the three lighting variants, appended one at a time:

> **Day** — bright cool daylight through the window, pale blue sky, crisp light
> falling across the floor, the room evenly lit and cheerful.

> **Evening** — low warm orange sun, long amber light through the window, deep
> soft shadows, the room golden and drowsy.

> **Night** — dark blue room lit mainly by a warm lamp, the window showing a
> deep navy sky and distant city lights, everything hushed and low-contrast.

### Rules the reference must respect

If a generated image breaks one of these, it is not usable and is worth
regenerating:

1. **Flat side-on.** No three-quarter view, no perspective, no floor receding
   into the distance.
2. **The album sleeve is a perfect square, face-on, and completely
   unobstructed.** Nothing leans against it or crosses in front of it. Its
   interior can be blank, plain, or an abstract shape — the real album art is
   inserted there by the app, so whatever the generator puts inside is
   discarded.
3. **The cat is unmistakably fat** and clearly readable as a separate silhouette
   against the floor and rug behind it.
4. **No text anywhere**, including on the sleeve, posters or record labels.
5. **The composition is identical across all three lighting versions** — same
   objects in the same places, only the light changes.

---

## Part 2 — Composition spec

The canvas is **320 × 200 logical pixels**, displayed at 2× (640 × 400) by
default. All coordinates below are in logical pixels, origin at the top left,
and are what I author the sprites to.

### Bands

| Zone | Vertical extent |
|---|---|
| Back wall | y 0 – 151 |
| Floor | y 152 – 199 |

### Objects

| Object | x | y | Size | Notes |
|---|---|---|---|---|
| Speaker, left | 0 – 14 | 84 – 152 | 14 × 68 | floor-standing, against the left edge |
| Sideboard | 16 – 172 | 104 – 152 | 156 × 48 | top surface at y 104 |
| **Album sleeve** | 24 – 80 | 48 – 104 | **56 × 56** | leaning on the wall, standing on the sideboard |
| Turntable | 92 – 152 | 78 – 104 | 60 × 26 | platter seen at a slight angle |
| Record label | 118 – 128 | 88 – 98 | 10 × 10 | album art again, tiny, centre of the platter |
| Amp display | 28 – 60 | 114 – 124 | 32 × 10 | on the sideboard front; blinks |
| Speaker, right | 176 – 192 | 84 – 152 | 16 × 68 | between sideboard and bed |
| **Cat** | 112 – 176 | 110 – 158 | **64 × 48** | on the rug, in front of the sideboard, facing the speakers |
| Rug | 96 – 200 | 146 – 170 | 104 × 24 | under the cat |
| Window | 212 – 296 | 24 – 92 | 84 × 68 | the whole time-of-day story happens here |
| Bed | 200 – 316 | 118 – 180 | 116 × 62 | mattress top at y 118 |

### Layer order, back to front

1. Wall and floor
2. Window view — sky, city, and light (swapped per time of day)
3. Window frame and sill
4. Bed, sideboard, rug
5. Album sleeve, turntable, amp display
6. Record and its label (animated)
7. Speakers (animated)
8. Cat (animated)
9. Lighting overlay (one authored image per time of day)

The cat is in front of the sideboard on purpose — it gives the flat room a
little depth without needing real perspective.

### The album artwork slot

The sleeve interior is a **fixed 52 × 52 square**, inset 2px inside the 56 × 56
sleeve so the sleeve edge always reads as an edge.

Windows hands over wildly different images. Measured on this machine:

| Source | Artwork |
|---|---|
| Spotify | 300 × 300 square |
| foobar2000 | 600 × 600 square |
| YouTube in Brave | **150 × 83 widescreen** |

**Nothing is ever cropped.** The rule is:

1. Scale the artwork down to fit *entirely* within the 52 × 52 square, keeping
   its proportions, using nearest-neighbour so it stays crisp.
2. A square cover fills the slot exactly.
3. A 16:9 image lands as 52 × 29, leaving two bands of about 11px above and
   below.
4. Fill those bands with a colour **derived from the artwork itself** — the
   dominant colour of the image, darkened slightly so the artwork still reads as
   the brightest thing in the sleeve.
5. Draw a 1px inner border between the artwork and the fill, so the letterboxing
   looks like a deliberately mounted print rather than a rendering failure.

The same derived colour is reused for the tiny record label, which is too small
to show a scaled-down cover legibly.

### Animation states

Everything except the cat follows playback directly:

- **Record** — spins while playing, slows to a stop when paused.
- **Speaker cones** — move while playing, still when paused.
- **Amp display** — blinks while playing.
- **Window** — follows the real clock, not playback.

**The cat does not follow playback.** It runs on its own clock: breathing,
blinking, ear flicks and tail movement, continuously, whether or not anything is
playing. Playback only nudges it, and each nudge resolves back into its own
rhythm rather than becoming a mode it stays in:

| Event | Reaction |
|---|---|
| Music starts | perks up, then settles into a relaxed tail sway |
| Track changes | ears twitch, or a brief glance towards the speakers |
| Paused | stretches, settles, and eventually falls asleep |

Reaction timings vary slightly so the same event never looks identical twice.

There is deliberately **no beat synchronisation** anywhere. That would need
system audio capture and analysis, and would make the cat look mechanically
tied to the music instead of alive.

### One thing the art must not depend on

**Track position is optional.** foobar2000 publishes no timeline at all — it
reports 0:00 forever. So no part of the room may depend on knowing how far
through a track we are. Any progress decoration is drawn only when a valid
timeline exists and is simply absent otherwise, with nothing left behind to look
broken. There is no workaround for this and none should be attempted.
