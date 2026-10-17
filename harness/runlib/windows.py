"""Find the window of the game. The Windows calls are in `list_windows`. The choice is pure code."""

from __future__ import annotations

import ctypes
from ctypes import wintypes


def list_windows() -> list[dict]:
    """Return all top-level windows as dicts: hwnd, pid, title, class, visible, iconic, rect (left, top, right, bottom)."""
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
        window_class = ctypes.create_unicode_buffer(128)
        user32.GetClassNameW(hwnd, window_class, 128)
        windows.append({
            "hwnd": int(hwnd or 0),
            "pid": pid.value,
            "title": title.value,
            "class": window_class.value,
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


GAME_WINDOW_CLASS = "UnrealWindow"  # the window class of an Unreal Engine game window
# Windows of the game process that are not the game: the UE4SS debug GUI and the UE4SS console.
OVERLAY_CLASSES = {"GLFW30": "UE4SS Debugging Tools", "ConsoleWindowClass": ""}


def pick_game_window(windows: list[dict], pids: set[int]) -> dict:
    """Return the game window of the given processes.

    The game window is the window of class UnrealWindow. The UE4SS debug GUI and console are windows of the
    same process too: if the game window is minimized, the largest other window would be a debug window,
    and the screenshot would show it by mistake. So when an UnrealWindow exists, only it can be picked.
    If no UnrealWindow exists (another game, a changed class), fall back to the largest visible window.

    Raise LookupError with a reason if there is none.
    """
    own = [w for w in windows if w["pid"] in pids]
    if not own:
        raise LookupError(f"no window belongs to the game process {sorted(pids)}")

    game = [w for w in own if w.get("class") == GAME_WINDOW_CLASS and _area(w) > 0]
    if game:
        window = max(game, key=_area)
        if window["iconic"]:
            raise LookupError("the game window is minimized")
        if not window["visible"]:
            raise LookupError("the game window is not visible")
        return window

    visible = [w for w in own if w["visible"] and _area(w) > 0]
    if not visible:
        raise LookupError("the game has no visible window")
    shown = [w for w in visible if not w["iconic"]]
    if not shown:
        raise LookupError("the game window is minimized")
    return max(shown, key=_area)


def overlay_windows(windows: list[dict], pids: set[int]) -> list[dict]:
    """The visible debug windows of the game process (UE4SS GUI and console) that can cover the game in a screenshot."""
    found = []
    for window in windows:
        if window["pid"] not in pids or not window["visible"] or window["iconic"] or _area(window) == 0:
            continue
        prefix = OVERLAY_CLASSES.get(window.get("class", ""))
        if prefix is not None and window["title"].startswith(prefix):
            found.append(window)
    return found


SW_MINIMIZE = 6


def minimize_window(hwnd: int) -> None:
    """Minimize a window without giving it the focus."""
    ctypes.windll.user32.ShowWindow(hwnd, SW_MINIMIZE)


SWP_NOSIZE = 0x0001
SWP_NOZORDER = 0x0004
SWP_NOACTIVATE = 0x0010


def move_window(hwnd: int, x: int, y: int) -> None:
    """Move a window to a screen point without a resize and without the focus. The game ignores -WinX and -WinY (spec 11)."""
    if not ctypes.windll.user32.SetWindowPos(hwnd, 0, x, y, 0, 0, SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE):
        raise OSError(f"SetWindowPos failed for window {hwnd}")
