"""Probe: which window is in front and under the cursor, and the monitor layout. Issue 104 research tool."""

import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32


def title(hwnd):
    buffer = ctypes.create_unicode_buffer(256)
    user32.GetWindowTextW(hwnd, buffer, 256)
    return buffer.value


def main():
    print("foreground", title(user32.GetForegroundWindow()))
    point = wintypes.POINT(2021, 1105)
    print("under 2021,1105:", title(user32.WindowFromPoint(point)), "root", title(user32.GetAncestor(user32.WindowFromPoint(point), 2)))
    print("screen", user32.GetSystemMetrics(78), user32.GetSystemMetrics(79), "origin", user32.GetSystemMetrics(76), user32.GetSystemMetrics(77))
    print("primary", user32.GetSystemMetrics(0), user32.GetSystemMetrics(1))
    clip = wintypes.RECT()
    user32.GetClipCursor(ctypes.byref(clip))
    print("clip", clip.left, clip.top, clip.right, clip.bottom)


main()
