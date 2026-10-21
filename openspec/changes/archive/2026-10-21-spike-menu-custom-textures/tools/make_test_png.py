"""Write the test PNG of the spike: parchment colour, 16 px dark border, red 32 px marker in the top left corner.

Run: uv run python openspec/changes/spike-menu-custom-textures/tools/make_test_png.py
Uses only the standard library (zlib), so no new package is needed.
"""
import struct
import sys
import zlib
from pathlib import Path

SIZE, BORDER, MARKER = 256, 16, 32
PARCHMENT, DARK, RED = (226, 208, 165), (60, 40, 20), (200, 30, 30)


def pixel(x: int, y: int) -> tuple[int, int, int]:
    if x < MARKER and y < MARKER:
        return RED
    if min(x, y, SIZE - 1 - x, SIZE - 1 - y) < BORDER:
        return DARK
    return PARCHMENT


def chunk(kind: bytes, data: bytes) -> bytes:
    body = kind + data
    return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))


def png_bytes() -> bytes:
    rows = b"".join(b"\x00" + bytes(c for x in range(SIZE) for c in pixel(x, y)) for y in range(SIZE))
    header = struct.pack(">IIBBBBB", SIZE, SIZE, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b"")


if __name__ == "__main__":
    target = Path(__file__).resolve().parent.parent / "assets" / "test_frame.png"
    target.write_bytes(png_bytes())
    print(f"wrote {target}", file=sys.stderr)
