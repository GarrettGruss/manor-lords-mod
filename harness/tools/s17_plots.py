"""Drive a `--keep-open` run for the spec 17 bailey retest (issue 68). Research tool, not a test.

    uv run python harness/tools/s17_plots.py <run id> setup | spots | row X Y Z | days N | report

setup   give goods, give the manor a storehouse worker slot and timber
spots   free spots for a tent (used as the outside control place)
row     commit 2 burgage plots mouse-free; the front edge starts at X Y Z
days    run N game days at speed 3
report  plot count (all and built) and the ids of built plots
The tool calls no save function.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import s94_drive  # noqa: E402  (sets up sys.path for runlib and the bridge)

from runlib import plotgeom  # noqa: E402
from runlib.commands import CommandChannel  # noqa: E402

ROOT = s94_drive.ROOT
TIMBER = 16
FOODS = (171, 172, 230, 296, 30)


def channel_for(run_id):
    folder = ROOT / "runs" / run_id / "commands"
    channel = CommandChannel(folder)
    channel._number = len(list(folder.glob("*.result.json"))) if folder.is_dir() else 0
    return channel


def show(label, value):
    print(label, json.dumps(value, default=str)[:1500])


def setup(bridge, channel):
    for good, amount in [(TIMBER, 80)] + [(food, 30 if food == 30 else 50) for food in FOODS]:
        bridge.call_function(s94_drive.CHEAT_MANAGER, "GiveItemByID", [good, amount])
    show("slot", channel.send("manor_worker_slot", job=45, slots=3))
    for _ in range(3):
        show("assign", channel.send("manor_assign_worker"))
    show("put", channel.send("manor_put", good=TIMBER, amount=60))


def row(bridge, channel, x, y, z, depth=plotgeom.PLOT_DEPTH):
    player = bridge.player_path()
    before = bridge.call_function(bridge.player_region_path(), "getBuildingCount", [3, False])
    bridge.write_property(player, "placePlotType", 3)
    bridge.write_property(player, "placeFieldMode", True)
    channel.send("plot_field_place", plots=plotgeom.make_plots(x, y, z, 1, 0, 2, depth=depth))
    bridge.call_function(player, "addCommitFieldRequest")
    show("row", {"at": [x, y, z], "before": before})


def report(bridge, channel):
    region = bridge.player_region_path()
    show("count", {"all": bridge.call_function(region, "getBuildingCount", [3, False]),
                   "built": bridge.call_function(region, "getBuildingCount", [3, True])})
    housing = channel.send("housing_state")
    show("plots", [{"id": b["id"], "built": b["built"]} for b in housing["residential"]])


def main(argv):
    run_id, command, args = argv[0], argv[1], argv[2:]
    bridge = s94_drive.make_bridge(run_id)
    channel = channel_for(run_id)
    if command == "setup":
        setup(bridge, channel)
    elif command == "spots":
        show("spots", channel.send("tent_find_spot"))
    elif command == "row":
        row(bridge, channel, *[float(value) for value in args])
    elif command == "days":
        s94_drive.command_days(bridge, args + ["3"])
    elif command == "report":
        report(bridge, channel)
    else:
        raise SystemExit(f"unknown command {command!r}")


if __name__ == "__main__":
    main(sys.argv[1:])
