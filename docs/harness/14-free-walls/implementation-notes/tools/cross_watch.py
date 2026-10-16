"""Spec 14: does a squad cross a wall? cross_watch.py <wall_json> <squad_id> <seconds> [speed].
wall_json: a file with {"walls": [[[x, y], ...], ...]} (polylines, not closed) and "inside" [x, y] (the bait point).
Each sample (1 s) checks every unit's step since the last sample against every wall segment. A step that intersects a segment
is a crossing THROUGH the wall. Prints a summary line at the end: crossings, units that reached 10 m of the bait, time."""
import json
import os
import sys
import time

sys.path.insert(0, r"C:\Users\garre\development\manor-lords-mod\mcp")
run = os.environ["RUN"]
os.environ["UE4SS_BRIDGE_GAME_DIR"] = r"C:\Program Files (x86)\Steam\steamapps\common\Manor Lords\ManorLords\Binaries\Win64"
os.environ["UE4SS_BRIDGE_DATA_DIR"] = r"C:\Users\garre\development\manor-lords-mod\runs\\" + run + r"\bridge"
from ue4ss_bridge import server
import pathlib
sys.path.insert(0, r"C:\Users\garre\development\manor-lords-mod\harness")
from runlib.commands import CommandChannel

_channel_dir = pathlib.Path(r"C:\Users\garre\development\manor-lords-mod\runs") / run / "commands"
_channel = CommandChannel(_channel_dir, check_alive=lambda *a: None)
_channel._number = len(list(_channel_dir.glob("*.result.json")))
_last_popup_check = 0.0


def close_popups():
    """A pop-up (for example "Hunger!") stops the simulation, so close pop-ups every few seconds."""
    global _last_popup_check
    if time.monotonic() - _last_popup_check > 5:
        _channel.send("close_popups")
        _last_popup_check = time.monotonic()


def one(*a, **k):
    value = server.one(*a, **k)
    return value["result"] if isinstance(value, dict) and "result" in value else value


def intersects(p1, p2, q1, q2):
    def orient(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    d1, d2 = orient(q1, q2, p1), orient(q1, q2, p2)
    d3, d4 = orient(p1, p2, q1), orient(p1, p2, q2)
    return (d1 > 0) != (d2 > 0) and (d3 > 0) != (d4 > 0)


spec = json.load(open(sys.argv[1]))
squad, seconds = int(sys.argv[2]), float(sys.argv[3])
speed = int(sys.argv[4]) if len(sys.argv) > 4 else 0
segments = [(w[i], w[i + 1]) for w in spec["walls"] for i in range(len(w) - 1)]
bait = spec["inside"]

units = []
for line in one("objects", class_name="SMUnit", limit=2000)["objects"]:
    ref = line.split(" ", 1)[1]
    if "Default__" in ref:
        continue
    try:
        sid = one("get", ref=ref, name="assignedSquadID")
        sid = sid.get("Value") if isinstance(sid, dict) else sid
    except Exception:
        continue
    if sid == squad:
        units.append(ref)
units = units[:int(os.environ.get("TRACK_UNITS", "6"))]  # fewer units give about one sample per second, so steps stay short
last, crossings, reached = {}, 0, set()
crossing_points = []  # distance in m from each crossing to the nearest wall end
start = time.monotonic()
first_reach = None
while time.monotonic() - start < seconds:
    if speed and one("get", ref="first:RTSMultiEngineCPP", name="gameSpeed") != speed:
        one("call", ref="first:MyPawnCPP_BP3_C", function="changeGameSpeed", args=[speed, False])
    close_popups()
    dists = []
    for ref in units:
        try:
            if one("get", ref=ref, name="dead"):
                continue
            p = one("get", ref=ref, name="realPos")
        except Exception:
            continue
        here = (p["X"], p["Y"])
        prev = last.get(ref)
        hit = next(((a, b) for a, b in segments if prev and intersects(prev, here, a, b)), None)
        if hit:
            crossings += 1
            ends = [pt for w in spec["walls"] for pt in (w[0], w[-1])]
            mx, my = (hit[0][0] + hit[1][0]) / 2, (hit[0][1] + hit[1][1]) / 2
            to_end = min(((mx - e[0]) ** 2 + (my - e[1]) ** 2) ** 0.5 for e in ends) / 100
            crossing_points.append(round(to_end, 1))
        last[ref] = here
        d = ((here[0] - bait[0]) ** 2 + (here[1] - bait[1]) ** 2) ** 0.5 / 100
        dists.append(d)
        if d < 10:
            reached.add(ref)
    if reached and first_reach is None:
        first_reach = round(time.monotonic() - start)
    if dists:
        print(json.dumps({"t": round(time.monotonic() - start), "min_m": round(min(dists)), "max_m": round(max(dists)),
                          "crossings": crossings, "reached": len(reached)}), flush=True)
    time.sleep(0.2)
print(json.dumps({"summary": True, "units": len(units), "crossings_through_wall": crossings, "reached_bait": len(reached),
                  "first_reach_s": first_reach, "crossing_m_from_wall_end": crossing_points}), flush=True)
