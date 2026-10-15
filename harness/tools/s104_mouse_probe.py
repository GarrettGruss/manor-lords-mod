"""Probe: does a relative mouse move (mouse_event MOVE) make the game see the cursor? Issue 104 research tool.

    uv run python harness/tools/s104_mouse_probe.py <run id> <fx> <fy>

Activates building mode 30, moves the cursor by SetCursorPos, then wiggles it with relative moves, and prints getMouse3d after each step.
"""

import ctypes
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "harness" / "tools"))

import s94_drive  # noqa: E402

MOVE = 0x0001


def main(argv):
    from runlib import osinput
    from runlib.game import find_game_processes
    from runlib.windows import list_windows, pick_game_window

    bridge = s94_drive.make_bridge(argv[0])
    player = bridge.player_path()
    window = pick_game_window(list_windows(), {p.pid for p in find_game_processes()})
    api = osinput.Win32Input()
    osinput.focus_game(api, window["hwnd"], time.sleep)
    rect = api.window_rect(window["hwnd"])
    print("rect", rect, "dpi-aware", ctypes.windll.user32.IsProcessDPIAware())
    bridge.call_function(player, "activateBuildingMode", [30])
    point = osinput.point_in_window(rect, float(argv[1]), float(argv[2]))
    api.set_cursor(*point)
    time.sleep(0.5)
    print("after set", bridge.call_function(player, "getMouse3d"))
    for step in range(6):
        ctypes.windll.user32.mouse_event(MOVE, 6 if step % 2 == 0 else -6, 4 if step % 2 == 0 else -4, 0, 0)
        time.sleep(0.3)
    print("after wiggle", bridge.call_function(player, "getMouse3d"), "cursor", api.get_cursor())
    bridge.call_function(player, "resetBuildingMode")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
