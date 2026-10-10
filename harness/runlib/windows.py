"""Find the window of the game. The Windows calls are in `list_windows`. The choice is pure code."""

from __future__ import annotations

import ctypes
from ctypes import wintypes


def list_windows() -> list[dict]:
    """Return all top-level windows as dicts: hwnd, pid, title, visible, iconic, rect (left, top, right, bottom)."""
    user32 = ctypes.windll.user32
    _make_process_dpi_aware()
    windows: list[dict] = []

    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def collect(hwnd, _lparam) -> bool:
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        rect = wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        title = ctypes.create_unicode_buffer(256)
        user32.GetWindowTextW(hwnd, title, 256)
        windows.append({
            "hwnd": int(hwnd or 0),
            "pid": pid.value,
            "title": title.value,
            "visible": bool(user32.IsWindowVisible(hwnd)),
            "iconic": bool(user32.IsIconic(hwnd)),
            "rect": (rect.left, rect.top, rect.right, rect.bottom),
        })
        return True

    user32.EnumWindows(callback_type(collect), 0)
    return windows


def _make_process_dpi_aware() -> None:
    # Without this, window rectangles can be scaled and not match the screen pixels that mss reads.
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except (OSError, AttributeError):
        pass  # already set, or not available: the rectangles are used as they are


def _area(window: dict) -> int:
    left, top, right, bottom = window["rect"]
    return max(0, right - left) * max(0, bottom - top)


def pick_game_window(windows: list[dict], pids: set[int]) -> dict:
    """Return the largest visible, not minimized window of the given processes.

    Raise LookupError with a reason if there is none.
    """
    own = [w for w in windows if w["pid"] in pids]
    if not own:
        raise LookupError(f"no window belongs to the game process {sorted(pids)}")
    visible = [w for w in own if w["visible"] and _area(w) > 0]
    if not visible:
        raise LookupError("the game has no visible window")
    shown = [w for w in visible if not w["iconic"]]
    if not shown:
        raise LookupError("the game window is minimized")
    return max(shown, key=_area)
