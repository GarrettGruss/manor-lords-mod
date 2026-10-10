"""Close game pop-ups while a long scenario runs (spec 10, spike S8).

An open pop-up ("Hunger!") pauses the game until the player presses Accept. The mod command `close_popups` presses Accept.
`PopupGuard` wraps that command, so it can be the `on_poll` (every poll) or `on_stall` (repair) of `ctx.run_until`,
and it remembers what it closed.
"""

from __future__ import annotations

from typing import Callable


class PopupGuard:
    """Callable. `close` runs the command and returns its answer: {"closed": [types], ...}."""

    def __init__(self, close: Callable[[], dict], log: Callable[[str], None] = lambda message: None):
        self._close = close
        self._log = log
        self.closed: list[str] = []
        self.calls = 0

    def __call__(self) -> list[str]:
        self.calls += 1
        closed = list(self._close().get("closed") or [])
        if closed:
            self.closed += closed
            self._log(f"closed pop-up(s): {closed}")
        return closed
