"""Screenshot of the game window. A failure returns a note. It never fails the run."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from .windows import list_windows, pick_game_window


def clip_to_bounds(rect: tuple[int, int, int, int], bounds: dict) -> dict | None:
    """Cut a window rectangle to the screen area. Return an mss region, or None if nothing is left."""
    left = max(rect[0], bounds["left"])
    top = max(rect[1], bounds["top"])
    right = min(rect[2], bounds["left"] + bounds["width"])
    bottom = min(rect[3], bounds["top"] + bounds["height"])
    if right <= left or bottom <= top:
        return None
    return {"left": left, "top": top, "width": right - left, "height": bottom - top}


def _default_grabber():
    import mss  # imported late, so the rest of the launcher works if mss is missing

    return mss.mss()


def _write_png(shot, path: Path) -> None:
    import mss.tools

    mss.tools.to_png(shot.rgb, shot.size, output=str(path))


def capture_game_window(
    path: Path,
    pids: set[int],
    windows_fn: Callable[[], list[dict]] = list_windows,
    grabber_factory: Callable = _default_grabber,
    png_writer: Callable = _write_png,
) -> str | None:
    """Save a PNG of the game window. Return None on success, or a note that says why it failed."""
    try:
        window = pick_game_window(windows_fn(), pids)
        with grabber_factory() as grabber:
            region = clip_to_bounds(window["rect"], grabber.monitors[0])
            if region is None:
                return f"window {window['rect']} is outside the screen"
            png_writer(grabber.grab(region), Path(path))
        return None
    except Exception as error:  # noqa: BLE001 - a screenshot problem must not fail the run
        return f"{type(error).__name__}: {error}"
