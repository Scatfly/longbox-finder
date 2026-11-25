"""Draws the app icons (no extra libraries needed). Run: py make_icons.py"""
import struct
import zlib
from pathlib import Path

YELLOW = (255, 210, 63)
MAGENTA = (214, 36, 110)
CYAN = (0, 148, 198)
INK = (21, 23, 28)
WHITE = (255, 255, 255)


def draw(n):
    px = [[YELLOW for _ in range(n)] for _ in range(n)]

    def rect(x0, y0, x1, y1, color):
        for y in range(max(0, int(y0 * n)), min(n, int(y1 * n))):
            row = px[y]
            for x in range(max(0, int(x0 * n)), min(n, int(x1 * n))):
                row[x] = color

    # halftone dots in the background
    step = max(4, n // 24)
    r = step * 0.22
    for cy in range(step // 2, n, step):
        for cx in range(step // 2, n, step):
            for y in range(int(cy - r), int(cy + r) + 1):
                for x in range(int(cx - r), int(cx + r) + 1):
                    if 0 <= x < n and 0 <= y < n and (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                        px[y][x] = (240, 190, 40)
    b = 0.022  # border
    # back comic (cyan), front comic (magenta) with ink borders
    rect(0.36 - b, 0.20 - b, 0.76 + b, 0.76 + b, INK)
    rect(0.36, 0.20, 0.76, 0.76, CYAN)
    rect(0.24 - b, 0.26 - b, 0.64 + b, 0.82 + b, INK)
    rect(0.24, 0.26, 0.64, 0.82, MAGENTA)
    # title bar and a starburst-ish block
    rect(0.27, 0.30, 0.61, 0.39, WHITE)
    rect(0.30, 0.47, 0.50, 0.67, YELLOW)
    rect(0.33, 0.50, 0.47, 0.64, INK)
    return px


def png(px):
    n = len(px)
    raw = b"".join(b"\x00" + bytes(c for p in row for c in p) for row in px)

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", n, n, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


out = Path(__file__).parent / "icons"
out.mkdir(exist_ok=True)
for name, size in [("icon-192.png", 192), ("icon-512.png", 512), ("apple-touch-icon.png", 180)]:
    (out / name).write_bytes(png(draw(size)))
    print("wrote", name)
