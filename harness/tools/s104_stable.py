"""Read animal and stable state of masters of one type in a kept-open run (issue 104). Research tool, not a test.

    uv run python harness/tools/s104_stable.py <run id> <type> [region name]

For each master of the type: location, parts, Data stable fields, animalSpaceCache, maxOxen, and every ox with its realPos.
It calls no save function.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "harness" / "tools"))

import s94_drive  # noqa: E402

FIELDS = ("oxen", "maxOxen", "activeOxen", "animals", "animalSpaceCache", "Region", "additionalWorkPositions")


def short(value):
    return json.dumps(value, default=str)[:1500]


def ox_position(bridge, ref):
    try:
        return bridge.read_property(ref, "realPos")
    except Exception as error:  # report, do not hide
        return f"error {error}"


def read_master(bridge, path):
    props = bridge._result("props", ref=path, include_super=False)["properties"]
    by_name = {prop["name"]: prop["value"] for prop in props}
    print("MASTER", path.rsplit(".", 1)[-1], "loc", short(bridge.call_function(path, "K2_GetActorLocation")),
          "rot", short(bridge.call_function(path, "K2_GetActorRotation")))
    for name in FIELDS:
        print("  ", name, short(by_name.get(name)))
    for ox in (by_name.get("oxen") or []) + (by_name.get("animals") or []):
        ref = ox["__object"].split(" ", 1)[-1] if isinstance(ox, dict) and "__object" in ox else None
        if ref:
            print("   ox", ref.rsplit(".", 1)[-1], "realPos", short(ox_position(bridge, ref)), "actor", short(bridge.call_function(ref, "K2_GetActorLocation")))
    try:
        print("   getMaxOxen", short(bridge.call_function(path, "getMaxOxen")))
    except Exception as error:
        print("   getMaxOxen error", error)


def main(argv):
    run_id, wanted = argv[0], int(argv[1])
    region = argv[2] if len(argv) > 2 else None
    bridge = s94_drive.make_bridge(run_id)
    for path in s94_drive.master_paths(bridge):
        state = s94_drive.master_state(bridge, path)
        if state["type"] == wanted and (region is None or state["Region"] == region):
            read_master(bridge, path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
