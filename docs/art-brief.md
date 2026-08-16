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

**Generate the daytime image first, on its own.** Once you are happy with it,
produce evening and night as *relighting edits of that approved image* — not as
fresh generations. Three independent generations will not agree with each other
on where anything is, and the whole point of the three is that only the light
differs.

If none of the daytime attempts feel right, say so — I can work from the spec
alone, and a bad reference is worse than none.

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
> Centre foreground: a small round rug on the floorboards, and sitting on it, an
> extremely fat cat — round as a loaf of bread, short legs tucked under, thick
> tail curled round, contented half-closed eyes. The cat is drawn in
> three-quarter profile, head towards the **viewer's left**, facing the stereo,
> with its tail curled round to the viewer's right and both ears and the curve
> of its back clearly visible. The cat is the heart of the picture.
>
> A few restrained extras and no more: a potted plant, a mug, a small framed
> picture on the wall.
>
> Mood: warm, quiet, lived-in, a little nostalgic. Uncluttered — every object
> clearly separated with breathing space around it, nothing overlapping
> confusingly.
>
> Style: clean, flat concept illustration intended to be redrawn later as pixel
> art. Chunky readable shapes, strong silhouettes, hard edges, limited colours,
> and minimal flat shading. No pixel texture, gradients, glow, blur, depth of
> field, text, or lettering.

Then the three lighting variants, appended one at a time:

> **Day** — bright cool daylight through the window, pale blue sky, crisp light
> falling across the floor, the room evenly lit and cheerful.

> **Evening** — low warm orange sun, long amber light through the window, deep
> soft shadows, the room golden and drowsy.

> **Night** — dark blue room lit by cool moonlight through the window, deep navy
> sky, a moon over the water and a few distant lights on the far shore,
> everything hushed and low-contrast.

**Superseded:** the night brief originally asked for a room "lit mainly by a
warm lamp". The approved night reference kept the daytime's warm, window-shaped
patch of light on the floor, which cannot be right — a warm rectangle carrying
the window's mullion pattern, cast at night, under a cool blue moon, with no
lamp anywhere in the room. So:

- The floor patch keeps its shape across all three times of day and only changes
  colour — warm yellow, deep amber, pale blue. One authored shape, three
  colours, which is close to free.
- The warmth at night comes from a **small wall sconce** over the sideboard, plus
  a glow around the amp and turntable.

The sconce replaced the empty picture frame in the polish pass. The original
reasoning here — "rather than add a lamp object that would have to exist unlit in
the day and evening art too" — no longer applies: the lamp is baked unlit into
the one background image, and its light lives entirely in the evening and night
overlays, so it costs nothing in the daytime and the night finally has a visible
source for its warmth.

### Rules the reference must respect

If a generated image breaks one of these, it is not usable and is worth
regenerating:

1. **Flat side-on.** No three-quarter view of the room, no perspective, no floor
   receding into the distance. **One deliberate exception:** the turntable alone
   uses a shallow stylised top surface, so that the circular platter and the
   tonearm stay readable — a strictly front-on camera would see the platter
   edge-on and lose them entirely. This cheat applies to the turntable and
   nothing else, and must not pull the rest of the room into perspective.
2. **The album sleeve is a perfect square, face-on, and completely
   unobstructed.** Nothing leans against it or crosses in front of it. Its
   interior can be blank, plain, or an abstract shape — the real album art is
   inserted there by the app, so whatever the generator puts inside is
   discarded.
3. **The cat is unmistakably fat**, in three-quarter profile with its head
   towards the viewer's left facing the stereo, and clearly readable as a
   separate silhouette against the floor and rug behind it. ("Turned to its
   left" is ambiguous — the cat's left is the viewer's right. State it as the
   viewer sees it.)
4. **No text anywhere**, including on the sleeve, posters or record labels.
5. **The composition is identical across all three lighting versions.** This is
   why evening and night are produced as relighting edits of the approved
   daytime image rather than generated separately — same objects in the same
   places, only the light changes.

### The approved daytime reference

Approved 2026-08-15. Saved at `docs/reference/day.png`.

It matched the composition spec closely without having been given the numbers —
sideboard, cat, window, bed and both speakers all landed within a few logical
pixels of their specified positions. The palette, the flat hard-edged style, the
sunlight falling across the floorboards and the cat itself are all taken as-is.

It also added three things worth keeping: curtains and a rod at the window, a
double bed rather than a single, and a view of trees and sea rather than
rooftops. The night relight should keep the trees and sea — it must not become a
city skyline.

**Three deliberate deviations when the sprites are authored:**

1. **The album sleeve is drawn larger than the reference shows it.** The
   reference sleeve is roughly 44 × 42 logical pixels; the spec calls for
   56 × 56. Album artwork is the entire point of the app, so the spec size wins
   and the sleeve grows a little relative to everything around it.
2. **A small amplifier with a display is added** to the sideboard beside the
   turntable. The reference has no amp, so there is nowhere for the blinking
   display to live.
3. **The cat is drawn slightly higher and smaller** than the reference places
   it, to sit within its specified 64 × 48 box and keep clear of the sideboard's
   drawers.

None of these need a regenerated reference. The reference exists for mood,
palette and lighting; the geometry comes from Part 2.

---

## Part 2 — Composition spec

The canvas is **320 × 200 logical pixels**, displayed at 2× (640 × 400) by
default. All coordinates below are in logical pixels, origin at the top left,
and are what I author the sprites to.

**All coordinate ranges are half-open: the starting coordinate is included and
the ending coordinate is excluded.** So `24 – 80` is exactly 56 pixels wide,
covering columns 24 through 79.

### Bands

| Zone | Vertical extent |
|---|---|
| Back wall | y 0 – 152 |
| Floor | y 152 – 200 |

### Objects

| Object | x | y | Size | Notes |
|---|---|---|---|---|
| Speaker, left | 0 – 14 | 84 – 152 | 14 × 68 | floor-standing, against the left edge |
| Sideboard | 16 – 172 | 104 – 152 | 156 × 48 | top surface at y 104 |
| **Album sleeve** | 24 – 80 | 48 – 104 | **56 × 56** | leaning on the wall, standing on the sideboard |
| Turntable | 92 – 152 | 78 – 104 | 60 × 26 | platter seen at a slight angle |
| Record label | 118 – 128 | 88 – 98 | 10 × 10 | album art again, tiny, centre of the platter |
| Amp display | 28 – 60 | 114 – 124 | 32 × 10 | on the sideboard front; baked dark, lit at runtime in the album's colour, pulses while playing |
| Speaker, right | 176 – 192 | 84 – 152 | 16 × 68 | between sideboard and bed |
| **Cat** | 94 – 196 | 105 – 176 | **102 × 71** | on the rug, in front of the sideboard, facing the speakers |
| Rug | 94 – 202 | 145 – 176 | 108 × 31 | under the cat |
| Wall lamp | 119 – 146 | 22 – 51 | 27 × 29 | small sconce; unlit by day |
| Window | 212 – 296 | 24 – 92 | 84 × 68 | the whole time-of-day story happens here |
| Bed | 200 – 316 | 118 – 180 | 116 × 62 | mattress top at y 118 |

### Layer order, back to front

1. Wall and floor
2. Window view — sky, city, and light (swapped per time of day)
3. Window frame and sill
4. Bed, sideboard, rug
5. Album sleeve, turntable, amp display
6. Record and its label (animated) — a runtime sprite; the deck under it is not
7. Speakers
8. Cat (animated)
9. Lighting overlay (one authored image per time of day)

The cat is in front of the sideboard on purpose — it gives the flat room a
little depth without needing real perspective.

**The lighting overlay sits on top of the album artwork, not under it.** In the
night reference the sleeve's artwork stayed fully saturated while the rest of
the room dimmed, and it read as pasted on. Since the artwork arrives from
Windows at full brightness whatever the hour, it has to be dimmed by the same
overlay as everything else or it will always look like a sticker.

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
   its proportions, using **high-quality smooth downscaling**. Nearest-neighbour
   is wrong here: shrinking a 600 × 600 photographic cover by dropping pixels
   makes it jagged and noisy. Smooth downscaling to the logical size is what
   preserves it.
2. A square cover fills the slot exactly.
3. A 16:9 image lands as 52 × 29, leaving 23 rows of fill split as evenly as
   possible above and below.
4. Fill those bands with a colour **derived from the artwork itself** — the
   dominant colour of the image, darkened slightly so the artwork still reads as
   the brightest thing in the sleeve.
5. Draw a 1px inner border between the artwork and the fill, so the letterboxing
   looks like a deliberately mounted print rather than a rendering failure.

The same derived colour is reused for the tiny record label, which is too small
to show a scaled-down cover legibly, and — pulled into a readable band of
lightness and saturation, but keeping its hue — for the amp's display. Those two
are the only places it appears. Each record tints the room slightly; nothing else
is recoloured, because recolouring the room to match the sleeve stops the room
being a room.

**Nearest-neighbour belongs at the other end of the pipeline.** The completed
320 × 200 room — album artwork already composited into it at logical size — is
enlarged to 2×, 3× or 4× with nearest-neighbour, which is what keeps the pixels
square and hard. Smooth on the way down, hard on the way up.

### Animation states

Everything except the cat follows playback directly:

- **Record** — spins while playing, and coasts to a stop when paused, parking
  wherever it happened to be rather than at a home position. It takes a moment to
  come up to speed, too: a platter has mass and the room should look like it
  knows that. See *The turning record* below.
- **Speaker cones** — do not move. They were meant to, and the sprite was built
  and then taken out: one pixel on a five-pixel dust cap reads as flicker rather
  than as a cone. The reasoning is in *The turning record* below, and it is a
  decision, not an omission.
- **Amp display** — blinks while playing.
- **Window** — follows the real clock, not playback.

**The cat does not follow playback.** It runs on its own clock: breathing
continuously whether or not anything is playing. Playback only nudges it, and
each nudge resolves back into its own rhythm rather than becoming a mode it stays
in. On top of that pace sit the reaction clips, listed in *The reactions* below.

Reaction timings vary slightly so the same event never looks identical twice.

There is deliberately **no beat synchronisation** anywhere. That would need
system audio capture and analysis, and would make the cat look mechanically
tied to the music instead of alive.

### The polish pass — 2026-08-16

The daytime room was approved on 2026-08-15 as **the foundation, not the final
polish**. This is the polish. What it settled, and what must not be undone:

**The hierarchy is cat, then album sleeve, then window.** Everything else is
quiet. That is what the sideboard's cooler wood, the softened bed outlines and
the slightly lighter rug are all for, and it is the test to apply to any later
change: if it makes the bed or the furniture louder, it is wrong.

**The tone is silly but played straight.** The lighting, the artwork, the shadows
and the times of day are treated seriously and finished properly. The absurdly
large cat is the joke, and it only works because nothing around it is joking. The
cat is deliberately a little too big for the room — do not tidy it back down to
fit a bounding box.

**The cat is one silhouette, not a head plus a body.** Every shape is stroked
once, oversized, then filled, which leaves a single continuous outline. Outlining
each shape on its own boundary put a hard line down the middle of the animal and
it read as a snowman. Within that:

- The **cream face mask stays well clear of the cream chest**, with a band of fur
  between them. This rule predates the merge and survives it: when the two pale
  areas met, the cat lost its face and read as one lump with ears in the middle.
  The chest is drawn wider and shallower than the face so the two do not read as
  a matching pair.
- The **tail is one tapered polygon** and never a chain of circles — circles left
  scalloped bumps, and a row of even bumps low on a cat reads unmistakably as
  **six feet**, which is what fresh eyes saw first. It now lies **out to the
  viewer's right along the rug**, tapering to a point, entirely outside the body.
  Tucked against the flank it read as a shadow; run along the underside — where
  every earlier version put it — it read as feet again however smoothly it was
  drawn. There is no dark round tip: that was a bead.
- There are **no drawn paws**, only a crease in the cream suggesting one tucked
  underneath.

**Light and shadow have one direction.** Daylight enters at the window, crosses
the bed faintly, and lands as one hard-edged band running down and to the left
across the floorboards until it reaches the cat's tail. Every contact shadow
falls the other way, down and to the left, away from the window. The beam is pale
rather than yellow on purpose: a saturated warm beam disappeared against the warm
floor, so the light has to arrive as brightness.

The cat's contact shadow lives in the background, not in the cat's own frames. A
shadow that rose and fell with the breathing made the floor look like it was
moving.

**Breathing is one pixel.** The back rises one, the underside spreads one, and
the belly lags the back by a frame so the movement has four states instead of
two. Nothing else on the cat moves. At two pixels the whole animal visibly grew
and shrank, which read as bobbing.

**Speaker, record and display animation stays restrained.** These are ambient
movement, not the show. The cat carries the personality.

### The reactions — 2026-08-16

The cat's reactions are where the comedy actually lives, and they only work
because the room around them is played straight.

**Every pose is the same cat.** `draw_cat` takes a `Pose` whose defaults are the
resting loaf, and a clip is a list of poses. Nothing draws a second cat, so a bad
clip can only ever change what it names. The face moves as a unit from one
origin, which is what makes a raised head possible at all.

| Clip | Earned by | What happens |
|---|---|---|
| `breathe` | nothing — this is the resting loop | one pixel of back, one of belly |
| `perk` | the music starting | head up, ears hard forward, eyes wide, a look at the speakers, then loses interest |
| `twitch` | a track change, sometimes | one ear, twice; nothing else moves |
| `glance` | a track change, less often | an eye opens and slides towards the stereo |
| `thump` | three track changes inside eight seconds | half an eye, and the tail slapped down twice |
| `stretch` | a long enough silence, on the way into sleep | one enormous yawn, the loaf pulled out long, then it settles and is gone |

**They are rare, and that is the feature.** Roughly one track change in five gets
anything at all, no two incidental reactions come within seven seconds, and over
a normal listening session the cat is in its resting loop about 98% of the time.
A cat that performed on every track change would be a toy; the joke is an animal
that mostly ignores you. Keep it that way.

The cooldown holds back the incidental reactions **only**. A run of skips or the
music starting has been earned by something the listener actually did, and must
never be swallowed because an ear happened to twitch a moment earlier.

**Both open eyes are the same size**, whatever the lids around them do. Scaling
the far eye down with its lid is correct perspective and looks simply wrong — one
small eye and one large one reads as a squint. The three-quarter view survives in
the lids instead.

Three states of eye, drawn rather than tweened. At twelve pixels across there is
nothing between a line and a circle to interpolate through, and looking for one
produced a smear that read as a wound.

Still absent, and deliberately: any reaction to the *content* of the music. There
is no beat detection here and there is not going to be.

### The Lamplight grade — 2026-08-16

The room went out for review and came back with a fair headline: *"The room is
charming. It just has no light in it."* One value band, a lamp that lit nothing,
a cat that floated, and an album sleeve no brighter than its own frame. The
reviewer supplied two graded directions and, in `work/grade.js.txt`, the shader
that produced them. **Direction A, "Lamplight", was chosen, and that shader is
the specification** — `grade()` follows its numbers rather than an impression of
its pictures.

| Term | Value |
|---|---|
| Contrast / lift | `1.18` / `-0.02` on luminance, hue preserved by ratio |
| Shadow tint | `0.34` toward plum `(92,54,58)` — except at night, below |
| Highlight tint | `0.22` toward amber `(255,196,120)` |
| Vignette | `0.26`, centred `(160,100)`, radii `(195,140)`, power `2.4` |
| Lamp halo | `(132,50)` radii `(88,86)`, `0.34`, `(255,196,110)` |
| Floor warmth | `(146,158)` radii `(110,56)`, `0.14`, `(255,186,120)` |
| Sleeve | gain `1.14`, saturation `1.25`, spill `0.26` over `36px` |
| Cat | form `0.30` amber over the top half, body `×0.94` |
| Contact shadow | `0.32`, ellipse `(146,175)` radii `(66,10)` |
| Quantize / dither | `16` steps everywhere; dither `0.7`, ramps only |

**The grade owns the lamp.** `light_overlay` used to cast a halo of its own and
now keeps only the window — sky tint, beam, wash. Two halos on one sconce was the
first thing that went wrong here.

**Dither goes only where the light actually ramps.** The shader dithered every
pixel, which speckles flat wall and flat wood — the one thing this style cannot
survive. `_dither_field` measures how fast the lighting is changing and spends
the dither there: the halo, the floor warmth, the sleeve spill, the contact
shadow. The vignette is deliberately excluded; it moves about one value step
across the whole canvas and bands once, softly, where nobody will find it.

**Three deliberate departures from the shader:**

1. **No cone.** It threw a beam from the lamp across the room. That was rejected
   twice during the polish pass, and soft edges did not change the answer.
2. **Night gets its own shadow.** One warm plum shadow at every hour raised the
   night room's blacks to mauve and took the blue out entirely — it came out
   *lighter* at midnight than at noon. Night uses slate `(24,32,60)` at `0.16`
   rather than `0.34`, so the lamp still has something to glow against. The halo
   is off during the day and strongest at night.
3. **The sleeve is not dithered.** Ordered dither across a 52-pixel cover is
   noise over the only part of the frame carrying real information. It is
   quantized to the room's sixteen steps and otherwise left alone, checked
   against all three real covers. Recognising the record beats matching the
   shader.

Two things worth knowing about the review itself. Its prose describes wall,
window and bed "hazed 16% toward the ambient tone" for depth, but the code never
sets `haze` — so the approved stills do not have it, and neither does this. And
the sleeve's `1.14` gain, once the vignette across the sleeve takes back its
`0.92`, nets to less than one of the sixteen value steps: the sleeve reads as
lifted because the *room* is pushed down around it by a shadow tint the sleeve is
exempt from, not because the artwork itself got brighter.

**Contact shadows are shared work now.** The grade casts the cat's, far stronger
and better placed than the flat one it replaced. Nothing in the grade touches the
sideboard, the speakers or the bed, so those keep their authored shadows in
`draw_shadows` — delete them and the furniture floats again, which is the
criticism this whole exercise was answering.

**The bake changed shape to allow any of it.** A grade is a per-pixel pass over a
finished frame and the app composites live, so the window's light is folded into
the background at bake time and there is now a full set of art per time of day:
`background-<band>.png` and `cat/<band>/<clip>-NN.png`. Live album art is graded
to match in `artwork.py`, from numbers exported into `layout.json` so the app
never restates them.

Grading three layers separately is **not** the same arithmetic as grading the
finished frame once. It is the usual production approximation, and the rendered
result decides whether it holds up, not the reasoning — the places to check are
the cat's outline against the floor and the sleeve's edge against its frame.

### The turning record — 2026-08-16

The record spins now, and slows to a stop when the music is paused. That was
promised in *Animation states* from the beginning and the drawing code for it had
been sitting unused: `draw_turntable` took a rotation angle and `build_background`
passed it a fixed 25 degrees forever.

**It is a sprite, not more backgrounds.** The art is already multiplied by three
time-of-day bands, and multiplying that again by record position is the road to
an asset set nobody can hold in their head. Twelve frames of the record alone,
graded per band exactly as the cat's frames are, composited over the room at
runtime: `record/<band>/NN.png`, thirty-six files and about forty kilobytes.

**The background has no record on it at all.** `draw_turntable` now draws the
plinth, the top face and a bare platter, and stops; the disc, the grooves, the
label and the tonearm are all in the sprite, stopped as well as turning. A parked
copy baked underneath would have been one more thing that could quietly disagree
with the thing on top, and the way to have no such bug is to have no second copy.

**Twelve frames, over half a turn, at one frame per tick.** The glint is drawn as
a full diameter of the disc, so it puts the same pixels on screen at an angle and
at that angle plus 180 degrees — a spin has only half a turn of distinct frames
in it. Twelve of them at one authored frame per 120ms tick sweeps the mark
through that half turn in 1.44 seconds. One frame per tick is the same rule the
cat's reaction clips already run on, and it is what stops the glint stuttering (a
frame drawn twice) or skipping (a frame never drawn).

**The glint had to be brightened to survive the grade.** At its authored 72 it
had never had a job: it sat still, and nobody had to be able to find it. Turning,
it has to be told apart from the two *static* groove rings beside it, and the
night band puts the lamp's halo directly over the turntable and lifts the whole
deck — at 72 the moving mark and the still rings landed one value step apart and
the spin simply was not there after dark. At 104 it clears the rings by three
steps by day, two in the evening, one at night. Night is as good as it gets: past
88 the halo compresses everything into the same step, so more brightness buys day
and evening only. It is still far below the tonearm, which is the brightest thing
on the deck and always was.

**The glint's vertical radius is the disc's own half-height, 4.5 and not a round
5.** At 5 the mark overshot the bottom of the record by a single pixel at the
steepest angle, so once every turn a bright dot appeared on the platter. One
pixel, one frame in twelve, and it read as a stuck pixel rather than as a record.

**The sprite carries the band's light.** The background is graded *after*
`light_overlay` is composited into it, so anything laid on top has to take the
same wash or it does not belong to the room. Unwashed, the stylus stayed
near-white while the night room went dark — a lit hole cut in the furniture. The
awkward part is that compositing a full-canvas overlay onto a sprite lights the
empty canvas too, so `lit_sprite` puts the sprite's own alpha back afterwards.
That one line is the whole fix and it looks redundant; it is not.

**The grade separates the room's treatment from the cat's.** `grade()` is now
everything that depends only on where a pixel is and what colour it is, and
`cat_form()` is the warm rim and the darkening that belong to the animal, applied
only when a cat mask is handed in. The record is furniture. It is lit by the
room, and a sprite that had to be given a cat's silhouette before it could be
graded was carrying a dependency it has no business having.

The split leaves the background and the cat byte-for-byte unchanged, which was
the point — it is a separation, not a new look. Worth knowing: the resting cat's
mask does reach the right speaker's drivers, so the background there *is* shaded
by the animal while a sprite over it would not be. Measured, that difference does
not survive the sixteen-step quantization: a resting speaker sprite came out
pixel-identical to the background in all three bands. If the cat is ever redrawn
larger or moved, that is the thing to re-measure.

**The speakers do not move, and that is the second time that has been decided.**
They were built: a two-frame sprite of both cabinets' cones, driven straight off
playback with no coasting, so they would stop dead the instant the music did. At
2x — the size the room is actually displayed at — the two positions are
indistinguishable side by side. A dust cap is five pixels across and the movement
available to it is one, so what the eye gets is not a cone pumping, it is eight
edge pixels blinking. The cat's breathing is also one pixel and does work,
because it runs along the length of the animal's back; a compact blob has no edge
to carry the movement. The answer to that is not a bigger movement, so the sprite
was taken out and the cones stay as authored. *Animation states* above has been
corrected to say so.

**Still no beat detection.** The spin follows play and pause and nothing else,
which is the same settled decision recorded above, restated here because a
spinning record is precisely where someone will be tempted.

### No progress decoration at all

foobar2000 publishes no timeline — it reports 0:00 forever — so a progress
indicator would appear for two players and vanish for the third.

**v0.1 therefore has none.** Not hidden conditionally, not degraded: simply not
built. Behaving identically for every player is worth more than a decoration the
room does not need, and it removes a whole class of "why is it missing here"
confusion. No workaround for foobar2000's missing timeline is to be attempted.
