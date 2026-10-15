"""Drive a `--keep-open` run by hand for the Siege Camp spike (issue 94). Research tool, not a test.

    uv run python harness/tools/s94_drive.py <run id> <command> [args...]

Commands:
  village                      centre of the masters of the player region (count, bounding box, types)
  camera X Y                   centre the camera on a world point
  shot NAME                    save a screenshot to runs/<id>/screenshots/NAME.png
  ghost TYPE FX FY NAME        activate build mode, hover at the window fractions, save a screenshot, cancel (no click)
  place TYPE FX FY             activate build mode, real click at the window fractions
  masters TYPE                 state of every master of a type
  give ITEM AMOUNT             MLCheatManager:GiveItemByID (timber 16, planks 17)
  days N SPEED                 run N game days at SPEED (1 to 3), then pause
The tool calls no save function.
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "harness"))
sys.path.insert(0, str(ROOT / "mcp"))

MASTER_FIELDS = ("Region", "ownerPawn", "buildingFunction", "constructionGoods", "Resources")
CHEAT_MANAGER = "first:MLCheatManager"


def make_bridge(run_id):
    os.environ["UE4SS_BRIDGE_DATA_DIR"] = str(ROOT / "runs" / run_id / "bridge")
    from ue4ss_bridge import server
    from runlib.bridge_client import Bridge

    return Bridge(server.one)


def object_name(value):
    if isinstance(value, dict) and "__object" in value:
        return value["__object"].split(" ", 1)[-1].rsplit(".", 1)[-1]
    return value


def master_paths(bridge):
    found = bridge._result("objects", class_name="SMBuildingMaster", limit=1000)["objects"]
    return [text.split(" ", 1)[1] for text in found]


def master_state(bridge, path):
    props = bridge._result("props", ref=path, include_super=False)["properties"]
    by_name = {prop["name"]: prop["value"] for prop in props}
    data = by_name.get("Data", {})
    state = {"path": path.rsplit(".", 1)[-1], "type": data.get("bType"), "constructed": data.get("constructed"),
             "hp": data.get("hp"), "maxHp": data.get("maxHp")}
    for name in MASTER_FIELDS:
        value = by_name.get(name)
        state[name] = object_name(value) if not isinstance(value, list) else json.dumps(value, default=str)[:300]
    state["parts"] = len(by_name.get("buildings", []))
    return state


def command_village(bridge, _args):
    region = bridge.player_region_path()
    points = []
    types = {}
    region_counts = {}
    for path in master_paths(bridge):
        props = bridge._result("props", ref=path, include_super=False)["properties"]
        by_name = {prop["name"]: prop["value"] for prop in props}
        name = object_name(by_name.get("Region"))
        region_counts[name] = region_counts.get(name, 0) + 1
        if name != region.rsplit(".", 1)[-1]:
            continue
        kind = by_name["Data"]["bType"]
        types[kind] = types.get(kind, 0) + 1
        points.append(bridge.call_function(path, "K2_GetActorLocation"))
    print("masters by region", region_counts)
    if not points:
        raise SystemExit(f"no master in the player region {region}")
    xs = [p["X"] for p in points]
    ys = [p["Y"] for p in points]
    print(json.dumps({"region": region, "masters": len(points), "types": types,
                      "x": [min(xs), sum(xs) / len(xs), max(xs)], "y": [min(ys), sum(ys) / len(ys), max(ys)]}))


def command_camera(bridge, args):
    print(bridge.centre_camera_on(float(args[0]), float(args[1])))


def screenshot(run_id, name):
    from runlib.game import find_game_processes
    from runlib.screenshot import capture_game_window

    folder = ROOT / "runs" / run_id / "screenshots"
    folder.mkdir(exist_ok=True)
    note = capture_game_window(folder / f"{name}.png", {process.pid for process in find_game_processes()})
    print("screenshot", name, note or "ok")


def command_place(bridge, run_id, args, click):
    from runlib import osinput
    from runlib.game import find_game_processes
    from runlib.windows import list_windows, pick_game_window

    type_id, fx, fy = int(args[0]), float(args[1]), float(args[2])
    player = bridge.player_path()
    window = pick_game_window(list_windows(), {process.pid for process in find_game_processes()})
    if click:
        steps = osinput.PlacementSteps(
            activate=lambda: bridge.call_function(player, "activateBuildingMode", [type_id]),
            cancel=lambda: bridge.call_function(player, "resetBuildingMode"),
            ground_under_cursor=lambda: osinput.is_ground_point(bridge.call_function(player, "getMouse3d")),
            unpause=bridge.unpause, pause=bridge.pause)
        osinput.place_with_mouse(osinput.Win32Input(), window["hwnd"], steps, fx, fy)
        print("clicked", type_id, fx, fy)
        return
    api = osinput.Win32Input()
    osinput.focus_game(api, window["hwnd"], __import__("time").sleep)
    with osinput.cursor_restored(api):
        bridge.call_function(player, "activateBuildingMode", [type_id])
        point = osinput.point_in_window(api.window_rect(window["hwnd"]), fx, fy)
        osinput.move_cursor(api, window["hwnd"], point, __import__("time").sleep)
        __import__("time").sleep(1.5)
        print("ground", bridge.call_function(player, "getMouse3d"))
        screenshot(run_id, args[3])
        bridge.call_function(player, "resetBuildingMode")


def command_masters(bridge, args):
    wanted = int(args[0])
    for path in master_paths(bridge):
        state = master_state(bridge, path)
        if state["type"] == wanted:
            print(json.dumps(state, default=str))


def command_give(bridge, args):
    print(bridge.call_function(CHEAT_MANAGER, "GiveItemByID", [int(args[0]), int(args[1])]))


def command_days(bridge, args):
    from runlib.timectl import TimeControl

    control = TimeControl(bridge, log=print)
    print(control.run_game_days(int(args[0]), speed=int(args[1])))


def command_mod(run_id, args):
    """Send one HarnessActions command: name key=value ... The request number continues after the answers already in the folder."""
    from runlib.commands import CommandChannel

    folder = ROOT / "runs" / run_id / "commands"
    channel = CommandChannel(folder)
    channel._number = len(list(folder.glob("*.result.json"))) if folder.is_dir() else 0
    fields = {}
    for pair in args[1:]:
        key, value = pair.split("=", 1)
        fields[key] = int(value) if value.lstrip("-").isdigit() else value
    print(json.dumps(channel.send(args[0], **fields), default=str)[:3000])


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    run_id, command, args = argv[0], argv[1], argv[2:]
    if command == "mod":
        command_mod(run_id, args)
        return 0
    bridge = make_bridge(run_id)
    if command == "village":
        command_village(bridge, args)
    elif command == "camera":
        command_camera(bridge, args)
    elif command == "shot":
        screenshot(run_id, args[0])
    elif command == "ghost":
        command_place(bridge, run_id, args, click=False)
    elif command == "place":
        command_place(bridge, run_id, args, click=True)
    elif command in ("click", "hover"):  # issue 90: real mouse at window fractions
        from runlib import osinput
        from runlib.game import find_game_processes
        from runlib.windows import list_windows, pick_game_window

        window = pick_game_window(list_windows(), {process.pid for process in find_game_processes()})
        action = osinput.click_at if command == "click" else osinput.hover_at
        print(action(osinput.Win32Input(), window["hwnd"], float(args[0]), float(args[1])))
    elif command == "call":  # call <player|path> <function> [int args...]
        target = bridge.player_path() if args[0] == "player" else args[0]
        print(bridge.call_function(target, args[1], [int(a) for a in args[2:]]))
    elif command == "mouse3d":
        print(bridge.call_function(bridge.player_path(), "getMouse3d"))
    elif command == "unpause":
        print(bridge.unpause())
    elif command == "pause":
        print(bridge.pause())
    elif command == "prop":  # prop <object path or first:Class> <property>
        target = bridge.player_path() if args[0] == "player" else args[0]
        value = bridge.read_property(target, args[1])
        print(f"len {len(value)}" if isinstance(value, list) else json.dumps(value, default=str)[:3000])
    elif command == "masters":
        command_masters(bridge, args)
    elif command == "give":
        command_give(bridge, args)
    elif command == "days":
        command_days(bridge, args)
    else:
        raise SystemExit(f"unknown command {command!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
