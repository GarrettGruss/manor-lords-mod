"""Spec 21 spike A helper: centre the camera on a point, zoom with the mouse wheel, take a screenshot.

    uv run python harness/tools/s21_view.py <run id> <x> <y> <wheel clicks> <name>

Wheel clicks: positive zooms in, negative zooms out (the game zooms the camera by wheel).
Single player only. No save call. The cursor is restored afterwards.
"""
import ctypes
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import s94_drive  # noqa: E402

WHEEL_EVENT = 0x0800
WHEEL_DELTA = 120


def zoom(run_id, clicks):
    from runlib import osinput
    from runlib.game import find_game_processes
    from runlib.windows import list_windows, pick_game_window

    window = pick_game_window(list_windows(), {process.pid for process in find_game_processes()})
    api = osinput.Win32Input()
    osinput.focus_game(api, window["hwnd"], time.sleep)
    with osinput.cursor_restored(api):
        point = osinput.point_in_window(api.window_rect(window["hwnd"]), 0.5, 0.5)
        osinput.move_cursor(api, window["hwnd"], point, time.sleep)
        step = 1 if clicks > 0 else -1
        for _ in range(abs(clicks)):
            ctypes.windll.user32.mouse_event(WHEEL_EVENT, 0, 0, step * WHEEL_DELTA, 0)
            time.sleep(0.15)
        time.sleep(1.5)


def main():
    run_id, x, y, clicks, name = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
    bridge = s94_drive.make_bridge(run_id)
    print("ground", bridge.centre_camera_on(x, y, tries=4))
    zoom(run_id, clicks)
    print("ground", bridge.centre_camera_on(x, y, tries=3))
    time.sleep(2.0)
    s94_drive.screenshot(run_id, name)


if __name__ == "__main__":
    main()
