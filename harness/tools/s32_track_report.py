"""Report for spec 32: read the track of probe-manor-wagenburg runs and count wall crossings.

Usage: uv run python harness/tools/s32_track_report.py runs/s32-8 runs/s32-9 ...
A unit is matched to the nearest unit of the previous sample (units have no id in the track). A step crosses the wall when the
segment between the two positions cuts a wall edge of the ring. The wall edges are the polygon of the built wall pieces; the
edge that holds the gate is skipped, so a unit that walks through the gate is not a crossing.
"""

import json
import math
import sys
from pathlib import Path

MAX_STEP_CM = 600.0
GATE_SKIP_CM = 700.0


def cut(p1, p2, p3, p4) -> bool:
    def side(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    return side(p1, p2, p3) * side(p1, p2, p4) < 0 and side(p3, p4, p1) * side(p3, p4, p2) < 0


def wall_edges(ring: dict) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    centre = ring["centre"]
    ordered = sorted(ring["pieces"], key=lambda p: math.atan2(p["y"] - centre[1], p["x"] - centre[0]))
    points = [(p["x"], p["y"]) for p in ordered]
    gate = ring.get("gate")
    edges = []
    for a, b in zip(points, points[1:] + points[:1]):
        middle = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        near_gate = gate and math.hypot(middle[0] - gate["x"], middle[1] - gate["y"]) < GATE_SKIP_CM
        if not near_gate:
            edges.append((a, b))
    return edges


def steps(samples: list[dict]):
    previous = None
    for row in samples:
        units = [(u["x"], u["y"]) for u in row["units"]]
        if previous:
            for point in units:
                nearest = min(previous, key=lambda q: math.hypot(point[0] - q[0], point[1] - q[1]), default=None)
                if nearest and math.hypot(point[0] - nearest[0], point[1] - nearest[1]) <= MAX_STEP_CM:
                    yield nearest, point
        previous = units


def report(run: Path) -> dict:
    ring = json.loads((run / "ring.json").read_text(encoding="utf-8"))
    samples = [json.loads(line) for line in (run / "track.jsonl").read_text(encoding="utf-8").splitlines()]
    edges = wall_edges(ring)
    crossings = sum(1 for a, b in steps(samples) if any(cut(a, b, e1, e2) for e1, e2 in edges))
    inside = [row["inside"] for row in samples]
    first = next((row["n"] for row in samples if row["inside"]), None)
    return {"run": run.name, "samples": len(samples), "wall_edges": len(edges), "wall_crossings": crossings,
            "first_inside_sample": first, "max_inside": max(inside, default=0), "alive_start": len(samples[0]["units"]) if samples else 0}


if __name__ == "__main__":
    for argument in sys.argv[1:]:
        print(json.dumps(report(Path(argument))))
