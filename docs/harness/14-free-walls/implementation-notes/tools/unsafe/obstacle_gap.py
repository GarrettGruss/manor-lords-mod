"""Spec 14 intervention: make the obstacle segments of the middle part of a wall zero length (the visible wall stays).
obstacle_gap.py <walls.json> <wall_index> <min_m_from_ends> <backup.json>
Saves the original point bytes to backup.json first. Restore with obstacle_gap.py restore <backup.json>.
UNSAFE: writes game memory. Refused unless HARNESS_ALLOW_UNSAFE=1 (checked in obstacles_mem.open_game_rw). Test games only."""
import importlib.util
import json
import math
import pathlib
import struct
import sys

TOOLS_DIR = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("om", TOOLS_DIR / "obstacles_mem.py")
om = importlib.util.module_from_spec(spec)
spec.loader.exec_module(om)


def along(poly, x, y):
    """Distance along the polyline to the nearest point, and the distance from the polyline, both in cm."""
    best, walked = (1e18, 0.0), 0.0
    for (ax, ay), (bx, by) in zip(poly, poly[1:]):
        seg = math.hypot(bx - ax, by - ay) or 1e-9
        t = max(0.0, min(1.0, ((x - ax) * (bx - ax) + (y - ay) * (by - ay)) / seg ** 2))
        px, py = ax + t * (bx - ax), ay + t * (by - ay)
        dist = math.hypot(x - px, y - py)
        if dist < best[0]:
            best = (dist, walked + t * seg)
        walked += seg
    return best[1], best[0], walked


if sys.argv[1] == "restore":
    handle = om.open_game_rw()
    for row in json.load(open(sys.argv[2])):
        om.write(handle, int(row["ptr"], 16), bytes.fromhex(row["bytes"]))
    print("restored")
    raise SystemExit
walls = json.load(open(sys.argv[1]))["walls"]
poly = walls[int(sys.argv[2])]
margin = float(sys.argv[3]) * 100
handle = om.open_game_rw()
backup, changed = [], []
for i, address, ptr, n, points in om.entries_live(handle):
    if n != 2:
        continue
    seg = om.read(handle, ptr, 32)
    x0, y0, x1, y1 = struct.unpack("<4d", seg)
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    pos, off, total = along(poly, mx, my)
    if off < 200 and margin <= pos <= total - margin:
        original = om.read(handle, ptr, 32 * n)  # n segments of 32 bytes (x0, y0, x1, y1)
        backup.append({"i": i, "ptr": hex(ptr), "bytes": original.hex()})
        for k in range(n):
            x0, y0 = struct.unpack("<2d", original[k * 32:k * 32 + 16])
            om.write(handle, ptr + k * 32, struct.pack("<4d", x0, y0, x0, y0))
        changed.append({"i": i, "at_m": round(pos / 100, 1)})
json.dump(backup, open(sys.argv[4], "w"))
print(json.dumps({"changed": len(changed), "rows": changed}))
