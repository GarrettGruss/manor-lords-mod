"""Move the Manor Lords window fully onto the primary screen (issue 104 research tool)."""

import ctypes
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))
from runlib.game import find_game_processes  # noqa: E402
from runlib.windows import list_windows, pick_game_window  # noqa: E402

user32 = ctypes.windll.user32
window = pick_game_window(list_windows(), {p.pid for p in find_game_processes()})
hwnd = window["hwnd"]
user32.SetWindowPos(hwnd, 0, 0, 0, 2000, 1200, 0x0004)
print("moved to 0,0 size 2000x1200")
