"""Wait for a condition in a running game, with a time limit, a stall detector and a clear failure message (spec 10, U3).

`run_until(predicate, timeout_s, ...)` polls `predicate()` until it is true.
  - clock="wall": `timeout_s` counts wall seconds.
  - clock="game": `timeout_s` counts game seconds (the game clock, so it follows the speed). A paused game never times out
    by itself, so use the stall detector or a wall limit for that case.
The stall detector watches the game clock. If the clock does not move for `stall_s` wall seconds, the game is stalled
(for example a pop-up holds it). `on_stall` may try a repair (for example close the pop-ups). If the clock still does not move
after another `stall_s`, run_until raises GameStalled. Use the stall detector only while the game should run.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable

CLOCKS = ("wall", "game")
DEFAULT_POLL_S = 1.0


class ScenarioFailure(Exception):
    """The game did not behave as the scenario needed. The runner turns it into a failed scenario (verdict fail), not a harness error."""


class WaitTimeout(ScenarioFailure):
    """The condition was not true in time. The message says what was awaited and the last value."""


class GameStalled(ScenarioFailure):
    """The game clock stood still while the game should run, and the repair (if any) did not help."""


@dataclass
class WaitResult:
    value: Any
    wall_s: float
    game_s: float | None
    polls: int
    stalls: int = 0  # how many times on_stall was called
    stall_log: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {"value": self.value, "wall_s": round(self.wall_s, 1),
                "game_s": None if self.game_s is None else round(self.game_s, 1), "polls": self.polls, "stalls": self.stalls}


def _check_arguments(timeout_s: float, clock: str, read_clock, stall_s) -> None:
    if clock not in CLOCKS:
        raise ValueError(f"clock must be one of {CLOCKS}, got {clock!r}")
    if timeout_s <= 0:
        raise ValueError(f"timeout_s must be above 0, got {timeout_s!r}")
    if (clock == "game" or stall_s) and read_clock is None:
        raise ValueError("clock='game' and stall_s need read_clock (a function that returns the game clock)")
    if stall_s is not None and stall_s <= 0:
        raise ValueError(f"stall_s must be above 0, got {stall_s!r}")


class StallWatch:
    """Remembers when the game clock last moved. `check` returns "ok", "repair" (call on_stall) or "stalled"."""

    def __init__(self, stall_s: float, now: float, clock: float):
        self.stall_s = stall_s
        self.last_clock = clock
        self.since = now
        self.repaired = False

    def check(self, now: float, clock: float) -> str:
        if clock != self.last_clock:
            self.last_clock, self.since, self.repaired = clock, now, False
            return "ok"
        if now - self.since < self.stall_s:
            return "ok"
        if not self.repaired:
            self.repaired, self.since = True, now  # a new grace window for the repair
            return "repair"
        return "stalled"


def run_until(
    predicate: Callable[[], Any],
    timeout_s: float,
    *,
    what: str = "the condition",
    clock: str = "wall",
    read_clock: Callable[[], float] | None = None,
    poll_s: float = DEFAULT_POLL_S,
    stall_s: float | None = None,
    on_stall: Callable[[], Any] | None = None,
    on_poll: Callable[[], Any] | None = None,
    check_alive: Callable[[], None] = lambda: None,
    sleep: Callable[[float], None] = time.sleep,
    monotonic: Callable[[], float] = time.monotonic,
    log: Callable[[str], None] = lambda message: None,
) -> WaitResult:
    """Poll `predicate` every `poll_s` wall seconds until it returns a true value. Return a WaitResult.

    `on_poll` runs after each false predicate (for example a telemetry sample). `check_alive` runs before each poll
    and should raise when the game process ended. Raises WaitTimeout or GameStalled with a clear message.
    """
    _check_arguments(timeout_s, clock, read_clock, stall_s)
    started = monotonic()
    game_start = read_clock() if read_clock else None
    watch = StallWatch(stall_s, started, game_start) if stall_s else None
    result = WaitResult(value=None, wall_s=0.0, game_s=None, polls=0)
    while True:
        check_alive()
        result.polls += 1
        now = monotonic()
        game_now = read_clock() if read_clock else None
        value = predicate()
        result.wall_s = now - started
        result.game_s = None if game_now is None else game_now - game_start
        if value:
            result.value = value
            return result
        waited = result.wall_s if clock == "wall" else result.game_s
        if waited >= timeout_s:
            raise WaitTimeout(
                f"timeout: {what} was not true within {timeout_s:g} {clock} seconds "
                f"(waited {result.wall_s:.0f} wall s, {result.polls} polls, last value {value!r})"
            )
        if watch:
            _handle_stall(watch, now, game_now, result, on_stall, what, log)
        if on_poll:
            on_poll()
        sleep(poll_s)


def _handle_stall(watch: StallWatch, now: float, game_now: float, result: WaitResult, on_stall, what: str, log) -> None:
    state = watch.check(now, game_now)
    if state == "ok":
        return
    if state == "repair" and on_stall:
        result.stalls += 1
        message = f"game clock stands still at {game_now:.1f} for {watch.stall_s:g} s while waiting for {what}: calling the repair"
        result.stall_log.append(message)
        log(message)
        on_stall()
        return
    raise GameStalled(
        f"the game clock stood still at {game_now:.1f} for {watch.stall_s:g} s"
        f"{' after a repair' if on_stall else ''} while waiting for {what}. "
        "A pop-up window may hold the game (see action close_popups), or the game hangs."
    )
