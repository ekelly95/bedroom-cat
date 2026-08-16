"""Save whatever album artwork Windows is publishing right now.

Used to test the sleeve against real covers rather than invented ones, so the
artwork-fitting rule is proven on the sizes players actually hand over.

    uv run python tools/dump_artwork.py docs/reference/cover.png
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from winrt.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionManager as SessionManager,
)
from winrt.windows.storage.streams import Buffer, InputStreamOptions


async def dump(destination: Path) -> int:
    manager = await SessionManager.request_async()
    sessions = list(manager.get_sessions())
    if not sessions:
        print("No media sessions. Start playback somewhere first.")
        return 1

    for session in sessions:
        app = session.source_app_user_model_id or "(unknown)"
        props = await session.try_get_media_properties_async()
        if props.thumbnail is None:
            print(f"{app}: no artwork")
            continue
        stream = await props.thumbnail.open_read_async()
        # ReadAsync may return a different buffer from the one it was given, so
        # the return is what to read. See source_windows._read_artwork.
        supplied = Buffer(stream.size)
        filled = await stream.read_async(
            supplied, stream.size, InputStreamOptions.READ_AHEAD
        )
        buffer = filled if filled is not None else supplied
        data = bytes(memoryview(buffer))[: buffer.length]

        out = destination.with_stem(f"{destination.stem}-{app.split('.')[0].lower()}")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
        print(f"{app}: {len(data):,} bytes -> {out}  ({props.title} / {props.artist})")
    return 0


def main() -> int:
    target = Path(sys.argv[1] if len(sys.argv) > 1 else "docs/reference/cover.png")
    return asyncio.run(dump(target))


if __name__ == "__main__":
    sys.exit(main())
