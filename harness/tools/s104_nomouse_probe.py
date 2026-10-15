"""Spike #104/#115: does the world cursor trace work without a mouse device? Needs a --keep-open run.

    uv run python harness/tools/s104_nomouse_probe.py <run id> [ground]

Moves the Windows cursor with SetCursorPos, enters building mode for a hitching post (30), and reads getMouse and getMouse3d.
It skips the mouse check of osinput on purpose. It calls no save function and sends no click.
"""

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "harness"))
sys.path.insert(0, str(ROOT / "harness" / "tools"))

POINTS = ((0.5, 0.5), (0.43, 0.27), (0.65, 0.65))


def read_mouse(bridge, player):
    return {"mouse": bridge.call_function(player, "getMouse"), "mouse3d": bridge.call_function(player, "getMouse3d")}


def main(argv):
    from runlib import osinput
    from runlib.game import find_game_processes
    from runlib.windows import list_windows, pick_game_window
    from s94_drive import make_bridge

    bridge = make_bridge(argv[0])
    player = bridge.player_path()
    window = pick_game_window(list_windows(), {process.pid for process in find_game_processes()})
    api = osinput.Win32Input()
    print("mouse_present", api.mouse_present())
    api.bring_to_front(window["hwnd"])
    time.sleep(1)
    bridge.call_function(player, "activateBuildingMode", [30])
    with osinput.cursor_restored(api):
        for fx, fy in POINTS:
            point = osinput.point_in_window(api.window_rect(window["hwnd"]), fx, fy)
            api.set_cursor(*point)
            time.sleep(0.1)
            api.set_cursor(point[0] + 1, point[1])
            time.sleep(1.0)
            print("cursor", api.get_cursor(), read_mouse(bridge, player))
    bridge.call_function(player, "resetBuildingMode")


main(sys.argv[1:])
