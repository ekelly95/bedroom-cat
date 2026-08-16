# The Bedroom

A small Windows companion that shows an animated pixel-art bedroom reflecting
whatever music is already playing elsewhere on the machine.

It reads Windows' own "now playing" information. It never captures audio, never
analyses sound, never plays music itself, never scans a library, and never talks
to Spotify's servers.

## Running it

```
uv run bedroom
```

## The probe

`probe.py` is the diagnostic that decided whether this project was viable, and it
stays in the repo for when a player stops cooperating.

```
uv run python probe.py          # watch continuously, reprints only on change
uv run python probe.py --once   # single snapshot
```

## What Windows actually reports

Measured on 2026-08-15, Windows 11 26200, with all three players running at once.

| | Spotify desktop | foobar2000 2.25 | YouTube in Brave 151 |
|---|---|---|---|
| **title** | yes | yes | yes, but the raw video title |
| **artist** | yes | yes | usually, sometimes `X - Topic` |
| **album** | yes | **no** | **no** |
| **artwork** | 300×300 PNG | 600×600 JPEG | **150×83 PNG** |
| **position / duration** | yes | **no** — always 0:00 | yes |
| **play** | no | no | no |
| **pause** | yes | yes | yes |
| **next** | yes | yes | **no** |
| **previous** | **no** | yes | **no** |
| **stop** | yes | yes | yes |
| **seek** | yes | **no** | yes |

### What this means for the app

**No single player reports everything, and each one is missing something
different.** The app degrades field by field, never player by player. There is no
"supported players" list in the code — anything that publishes to Windows works,
and each field is used only if it arrives.

Specifically:

- **Nothing essential can depend on track position.** foobar2000 publishes no
  timeline whatsoever, so any progress indication has to be an optional
  decoration that simply isn't drawn when the numbers aren't there.
- **Album is effectively Spotify-only.** It cannot appear anywhere the layout
  depends on it.
- **Artwork varies wildly in shape and size** — from a 150×83 widescreen video
  still to a 600×600 square cover. The record sleeve has to look right with
  both, so wide images are centre-cropped to square rather than letterboxed.
- **Transport controls must grey out from the live `controls` flags, per player
  and per moment.** They are not fixed per application: Spotify reported
  `previous` as unavailable throughout this session.
- **Several players publish at once, all reporting `PLAYING`.** This is the
  normal case, not an edge case. Windows names one of them "current" — the most
  recently interacted-with — and that is the right thing to follow.
- **Spotify keeps publishing when the music is playing on a phone**, mirrored
  over Spotify Connect. The room works for remote playback too.

### Corrections and open questions

- **foobar2000 was expected to publish nothing** — corrected. Its components
  folder contains only the nine that ship with it, and SMTC support has
  historically needed a separate plugin. It publishes fine regardless, and gives
  the best artwork of the three. No plugin needed.
- **Why Spotify reports no `previous` is still open.** It was unavailable in
  every snapshot taken here, but playback was being mirrored from a phone over
  Spotify Connect and it was not confirmed whether it ever ran locally on the
  desktop during the test. So "Spotify never supports previous" is not
  established — only that it did not during this session. It makes no difference
  to the app, which greys the button from the live flag either way.

## Development

```
uv run pytest
uv run ruff check .
```
