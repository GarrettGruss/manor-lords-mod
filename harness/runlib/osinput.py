"""Real OS mouse input for the game window (spec 07). It moves the real cursor and takes the keyboard focus.

Do not use it while a person works on this computer. The Windows calls are in `Win32Input`.
The checks and the steps are pure code: the window and cursor functions are injected, so tests need no game.
"""

from __future__ import annotations

import ctypes
import time
from contextlib import contextmanager
from dataclasses import dataclass
from ctypes import wintypes
from typing import Callable, Iterator, Protocol

from .windows import _make_process_dpi_aware

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
SW_RESTORE = 9
SM_MOUSEPRESENT = 19
CLICK_HOLD_S = 0.15
KEYEVENTF_KEYUP = 0x0002
VK_F7 = 0x76
KEY_HOLD_S = 0.1
EDGE_MARGIN_PX = 20  # a click this close to the window border could hit the frame or the HUD edge


class InputError(Exception):
    """The input was not sent because a safety check failed."""


class InputApi(Protocol):
    def mouse_present(self) -> bool: ...
    def foreground_window(self) -> int: ...
    def bring_to_front(self, hwnd: int) -> None: ...
    def window_rect(self, hwnd: int) -> tuple[int, int, int, int]: ...
    def get_cursor(self) -> tuple[int, int]: ...
    def set_cursor(self, x: int, y: int) -> None: ...
    def release_cursor_clip(self) -> None: ...
    def button(self, down: bool) -> None: ...
    def right_button(self, down: bool) -> None: ...


def point_in_window(rect: tuple[int, int, int, int], fx: float, fy: float) -> tuple[int, int]:
    """The screen point at a fraction of the window width and height (0..1)."""
    if not (0 <= fx <= 1 and 0 <= fy <= 1):
        raise InputError(f"fractions must be between 0 and 1, got {fx}, {fy}")
    left, top, right, bottom = rect
    return int(left + (right - left) * fx), int(top + (bottom - top) * fy)


def check_inside(rect: tuple[int, int, int, int], point: tuple[int, int], margin: int = EDGE_MARGIN_PX) -> None:
    left, top, right, bottom = rect
    x, y = point
    if not (left + margin <= x < right - margin and top + margin <= y < bottom - margin):
        raise InputError(f"point {point} is not inside the game window {rect}")


def check_mouse_present(api: InputApi) -> None:
    """The game finds the cursor in the 3D world only while Windows reports a mouse device (spike #115).

    Without one, UE returns no mouse position: getMouse3d gives Z -100000 and no ghost follows the cursor.
    Hover tooltips still work, so the failure looks like a bad click spot. Fail early instead.
    """
    if not api.mouse_present():
        raise InputError("Windows reports no mouse device (GetSystemMetrics SM_MOUSEPRESENT = 0). "
                         "The game then ignores the cursor in the world. Plug in a mouse, or install a virtual mouse, and restart the game; no input sent")


def check_foreground(api: InputApi, hwnd: int) -> None:
    current = api.foreground_window()
    if current != hwnd:
        raise InputError(f"the game window {hwnd} is not in the foreground (foreground window is {current}); no input sent")


def focus_game(api: InputApi, hwnd: int, sleep: Callable[[float], None] = time.sleep, settle_s: float = 0.5) -> None:
    """Bring the game window to the front. Raise InputError if it does not get the focus."""
    check_mouse_present(api)
    if api.foreground_window() == hwnd:
        return  # repeated focus tricks can open the Windows task switcher
    api.bring_to_front(hwnd)
    sleep(settle_s)
    check_foreground(api, hwnd)


@contextmanager
def cursor_restored(api: InputApi) -> Iterator[tuple[int, int]]:
    """Put the cursor back where it was, also after an error."""
    original = api.get_cursor()
    try:
        yield original
    finally:
        api.release_cursor_clip()  # the game can confine the cursor to its window
        api.set_cursor(*original)


def move_cursor(api: InputApi, hwnd: int, point: tuple[int, int], sleep: Callable[[float], None] = time.sleep) -> None:
    """Move the real cursor to a point inside the game window. A 1 pixel step makes the game see a mouse move."""
    check_foreground(api, hwnd)
    check_inside(api.window_rect(hwnd), point)
    api.set_cursor(*point)
    sleep(0.05)
    api.set_cursor(point[0] + 1, point[1])
    sleep(0.05)
    api.set_cursor(*point)
    sleep(0.1)


def left_click(api: InputApi, hwnd: int, sleep: Callable[[float], None] = time.sleep, hold_s: float = CLICK_HOLD_S) -> None:
    """Press and release the left button at the cursor. The cursor must be inside the game window."""
    check_foreground(api, hwnd)
    check_inside(api.window_rect(hwnd), api.get_cursor())
    api.button(True)
    try:
        sleep(hold_s)
    finally:
        api.button(False)  # never leave the button down


def right_click(api: InputApi, hwnd: int, sleep: Callable[[float], None] = time.sleep, hold_s: float = CLICK_HOLD_S) -> None:
    """Press and release the right button at the cursor (a move order for the selected squads). The cursor must be inside the game window."""
    check_foreground(api, hwnd)
    check_inside(api.window_rect(hwnd), api.get_cursor())
    api.right_button(True)
    try:
        sleep(hold_s)
    finally:
        api.right_button(False)  # never leave the button down


@dataclass
class PlacementSteps:
    """The game calls that the placement needs. They are injected, so the logic is testable without a game."""

    activate: Callable[[], None]  # start the building mode of the chosen building
    cancel: Callable[[], None]  # leave the building mode
    ground_under_cursor: Callable[[], bool]  # true when the game sees terrain under the cursor
    unpause: Callable[[], None]
    pause: Callable[[], None]


PREVIEW_WAIT_S = 1.0
RUN_BEFORE_CLICK_S = 2.0
RUN_AFTER_CLICK_S = 3.0


def place_with_mouse(api: InputApi, hwnd: int, steps: PlacementSteps, fx: float, fy: float,
                     sleep: Callable[[float], None] = time.sleep) -> None:
    """Place the chosen building with a real left click at a point of the game window.

    The game runs for a few seconds around the click and is paused again at the end, also after an error.
    Raise InputError if the game window has no focus or the cursor is not over terrain. The cursor is restored.
    """
    focus_game(api, hwnd, sleep)
    with cursor_restored(api):
        steps.activate()
        try:
            move_cursor(api, hwnd, point_in_window(api.window_rect(hwnd), fx, fy), sleep)
            sleep(PREVIEW_WAIT_S)
            if not steps.ground_under_cursor():
                raise InputError(f"no terrain under the cursor at window fraction ({fx}, {fy})")
            steps.unpause()
            try:
                sleep(RUN_BEFORE_CLICK_S)
                left_click(api, hwnd, sleep)
                sleep(RUN_AFTER_CLICK_S)
            finally:
                steps.pause()
        finally:
            steps.cancel()


def order_with_mouse(api: InputApi, hwnd: int, ground_point: Callable[[], dict], fx: float | None, fy: float | None,
                     sleep: Callable[[float], None] = time.sleep) -> dict:
    """Send the selected squads to a point with a real right click at a fraction (fx, fy) of the game window (spike #59).

    Returns the terrain point under the cursor (the game's own getMouse3d), read just before the click.
    Raise InputError if the game window has no focus or the cursor is not over terrain. The cursor is restored.
    """
    focus_game(api, hwnd, sleep)
    with cursor_restored(api):
        if fx is not None and fy is not None:  # None: the cursor is already over the point (put there by the mod)
            move_cursor(api, hwnd, point_in_window(api.window_rect(hwnd), fx, fy), sleep)
        sleep(PREVIEW_WAIT_S)
        point = ground_point()
        if not is_ground_point(point):
            raise InputError(f"no terrain under the cursor at window fraction ({fx}, {fy})")
        right_click(api, hwnd, sleep)
        return point


def click_at(api: InputApi, hwnd: int, fx: float, fy: float, sleep: Callable[[float], None] = time.sleep) -> tuple[int, int]:
    """Left click at a fraction (fx, fy) of the game window (a UI button, spec 16). Returns the screen point. The cursor is restored."""
    focus_game(api, hwnd, sleep)
    with cursor_restored(api):
        point = point_in_window(api.window_rect(hwnd), fx, fy)
        move_cursor(api, hwnd, point, sleep)
        focus_game(api, hwnd, sleep)  # another window can take the focus between the move and the click
        left_click(api, hwnd, sleep)
        sleep(0.2)
        return point


def press_key(api, hwnd: int, virtual_key: int, sleep: Callable[[float], None] = time.sleep, hold_s: float = KEY_HOLD_S) -> None:
    """Press and release one key while the game window is in the foreground (a mod key bind, spec 16)."""
    focus_game(api, hwnd, sleep)
    api.key(virtual_key, True)
    try:
        sleep(hold_s)
    finally:
        api.key(virtual_key, False)  # never leave the key down
    sleep(0.2)


GROUND_MIN_Z = -99999.0  # getMouse3d returns z = -100000 when no terrain is under the cursor


def is_ground_point(mouse3d: dict) -> bool:
    return float(mouse3d["Z"]) > GROUND_MIN_Z


class Win32Input:
    """The real Windows calls."""

    def __init__(self):
        _make_process_dpi_aware()  # window rectangles and cursor positions must use screen pixels
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32
        self.user32.GetForegroundWindow.restype = wintypes.HWND

    def mouse_present(self) -> bool:
        return bool(self.user32.GetSystemMetrics(SM_MOUSEPRESENT))

    def foreground_window(self) -> int:
        return int(self.user32.GetForegroundWindow() or 0)

    def bring_to_front(self, hwnd: int) -> None:
        # Windows refuses SetForegroundWindow from a background process. Attaching to the input queue of the
        # current foreground thread lifts that rule.
        foreground = self.user32.GetForegroundWindow()
        foreground_thread = self.user32.GetWindowThreadProcessId(foreground, None) if foreground else 0
        own_thread = self.kernel32.GetCurrentThreadId()
        attached = bool(foreground_thread) and foreground_thread != own_thread and \
            bool(self.user32.AttachThreadInput(own_thread, foreground_thread, True))
        try:
            if self.user32.IsIconic(hwnd):
                self.user32.ShowWindow(hwnd, SW_RESTORE)
            self.user32.BringWindowToTop(hwnd)
            self.user32.SetForegroundWindow(hwnd)
        finally:
            if attached:
                self.user32.AttachThreadInput(own_thread, foreground_thread, False)

    def window_rect(self, hwnd: int) -> tuple[int, int, int, int]:
        rect = wintypes.RECT()
        self.user32.GetWindowRect(hwnd, ctypes.byref(rect))
        return rect.left, rect.top, rect.right, rect.bottom

    def get_cursor(self) -> tuple[int, int]:
        point = wintypes.POINT()
        self.user32.GetCursorPos(ctypes.byref(point))
        return point.x, point.y

    def set_cursor(self, x: int, y: int) -> None:
        self.user32.SetCursorPos(int(x), int(y))

    def release_cursor_clip(self) -> None:
        self.user32.ClipCursor(None)

    def button(self, down: bool) -> None:
        self.user32.mouse_event(MOUSEEVENTF_LEFTDOWN if down else MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

    def right_button(self, down: bool) -> None:
        self.user32.mouse_event(MOUSEEVENTF_RIGHTDOWN if down else MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)

    def key(self, virtual_key: int, down: bool) -> None:
        self.user32.keybd_event(virtual_key, 0, 0 if down else KEYEVENTF_KEYUP, 0)


def hover_at(api, hwnd: int, fx: float, fy: float, sleep: Callable[[float], None] = time.sleep) -> tuple[int, int]:
    """Move the real cursor to a fraction of the game window and leave it there (the caller restores it by clicking)."""
    focus_game(api, hwnd, sleep)
    point = point_in_window(api.window_rect(hwnd), fx, fy)
    move_cursor(api, hwnd, point, sleep)
    return point
