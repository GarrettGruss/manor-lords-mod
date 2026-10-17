"""Game time control for scenarios: set the speed, run for N game seconds or N game days, then pause.

Facts measured in the real game (docs/harness/04-telemetry-and-assertions/implementation-notes/time-measurements.md):
  - The speed index 1, 2, 3 gives a game clock rate of 1, 4 and 8 game seconds for each wall second.
  - One game day is 40 game seconds.
  - `daysTotal` counts days without a wrap. `day` is the day of the year (1 to 365) and wraps with `Year`.
  - A pop-up (for example "Hunger!") pauses the game until a player closes it. The clock then stands still.
    A run calls its `guard` every 2 s (the scenario context passes `ctx.popups`), so a pop-up cannot stall a run.
  - When an army is spotted, the game sets the speed to 1x. An army in a forest is hidden and seen again quickly, so this
    repeats many times while armies march (user note and spike S11, 2026-10-11: 19 drops in 110 s). A run therefore checks
    the speed about once a second and sets it again.
"""

from __future__ import annotations

import time
from typing import Callable

from .bridge_client import Bridge
from .waiting import ScenarioFailure

SPEED_FACTOR = {1: 1.0, 2: 4.0, 3: 8.0}  # speed index -> game seconds for each wall second
CLOCK_SECONDS_PER_DAY = 40.0
DAYS_PER_YEAR = 365
POLL_S = 0.2
START_TIMEOUT_S = 5.0
SETTLE_S = 3.0
# The game set the speed back to 1x once, about 3 s after the first speed change after a boot (seen in 2 real runs).
# A second try holds, so set_speed tries again.
SPEED_ATTEMPTS = 3
LIMIT_FACTOR = 3  # the wall time limit is this many times the expected time (spec 04, Part A)
LIMIT_EXTRA_S = 10.0
HOLD_CHECK_S = 1.0  # how often a run checks that the game kept the speed
GUARD_CHECK_S = 2.0  # how often a run calls the guard (it closes pop-ups)


class TimeControlError(ScenarioFailure):
    """The game clock did not behave as the scenario asked. The message says why."""


def absolute_day(date: dict) -> int:
    """A day number that does not wrap at the year end. `date` has `day` (of the year) and `year`."""
    return date["year"] * DAYS_PER_YEAR + date["day"]


def wall_limit_s(expected_game_seconds: float, speed: int) -> float:
    return expected_game_seconds / SPEED_FACTOR[speed] * LIMIT_FACTOR + LIMIT_EXTRA_S


class TimeControl:
    """`sleep` and `monotonic` are parameters so tests can use a fake clock."""

    def __init__(
        self,
        bridge: Bridge,
        sleep: Callable[[float], None] = time.sleep,
        monotonic: Callable[[], float] = time.monotonic,
        check_alive: Callable[[], None] = lambda: None,
        log: Callable[[str], None] = lambda message: None,
        guard: Callable[[], object] = lambda: None,
    ):
        self._bridge = bridge
        self._guard = guard
        self._sleep = sleep
        self._monotonic = monotonic
        self._check_alive = check_alive
        self._log = log

    # ---- speed and pause ----

    def set_speed(self, speed: int) -> dict:
        """Set speed 1, 2 or 3 and check that it holds. This also unpauses the game.

        The game keeps a "player paused" flag that `changeGameSpeed` does not clear. With the flag set,
        the game drops back to 1x after about 3 s. So `unPauseGame` comes first.
        """
        if speed not in SPEED_FACTOR:
            raise TimeControlError(f"unknown speed {speed!r}. Use one of {sorted(SPEED_FACTOR)}.")
        self._check_alive()
        started = self._bridge.unpause(START_TIMEOUT_S)
        if not started["ok"]:
            raise TimeControlError(
                f"the clock did not move after unPauseGame in {START_TIMEOUT_S:.0f} s. "
                "A pop-up window in the game may hold the pause."
            )
        for attempt in range(1, SPEED_ATTEMPTS + 1):
            self._bridge.call_on_player("changeGameSpeed", [speed, False])
            self._sleep(SETTLE_S)
            factor = self._bridge.read_game_speed()
            if factor == SPEED_FACTOR[speed]:
                self._log(f"set_speed {speed} -> gameSpeed {factor} (attempt {attempt})")
                return {"speed": speed, "game_speed": factor, "attempts": attempt}
        raise TimeControlError(
            f"speed {speed} should give gameSpeed {SPEED_FACTOR[speed]}, but the game reports {factor} "
            f"after {SPEED_ATTEMPTS} tries"
        )

    def pause(self) -> dict:
        """Pause and check that the clock stands still for 3 s. Raise if it does not."""
        self._check_alive()
        result = self._bridge.pause()
        self._log(f"pause {result}")
        if not result["ok"]:
            raise TimeControlError(f"the clock still moved after pauseGame ({result['attempts']} tries, change {result['change']})")
        return result

    # ---- run for a time ----

    def run_game_seconds(self, seconds: float, speed: int = 1) -> dict:
        """Run the game until the clock has advanced by `seconds`, then pause."""
        start = self._bridge.read_clock_value()
        target = start + seconds
        return self._run_until(lambda clock: clock >= target, speed, wall_limit_s(seconds, speed), f"{seconds} game seconds")

    def run_game_days(self, days: int, speed: int = 1) -> dict:
        """Run the game until `daysTotal` has grown by `days`, then pause.

        `daysTotal` is used because it never wraps at the year end. The record also has `day_start` and
        `day_end` as absolute day numbers (see absolute_day), so a scenario can compare the date.
        """
        engine = self._bridge.engine_path()
        calendar = self._bridge.calendar_path(engine)
        read_total = lambda: self._bridge.read_property(calendar, "daysTotal")  # noqa: E731
        start_total = read_total()
        start_date = self._read_date(calendar)
        record = self._run_until(
            lambda clock: read_total() >= start_total + days,
            speed, wall_limit_s(days * CLOCK_SECONDS_PER_DAY, speed), f"{days} game days",
        )
        end_date = self._read_date(calendar)
        record.update(days_start=start_total, days_end=read_total(),
                      day_start=absolute_day(start_date), day_end=absolute_day(end_date))
        return record

    def _read_date(self, calendar: str) -> dict:
        return {"day": self._bridge.read_property(calendar, "day"), "year": self._bridge.read_property(calendar, "Year")}

    def _run_until(self, done: Callable[[float], bool], speed: int, limit_s: float, what: str) -> dict:
        engine = self._bridge.engine_path()
        clock_start = self._bridge.read_clock_value(engine)
        started = self._monotonic()
        self.set_speed(speed)
        resets = 0
        last_check = last_guard = self._monotonic()
        while not done(self._bridge.read_clock_value(engine)):
            self._check_alive()
            if self._monotonic() - started > limit_s:
                self._pause_after_timeout()
                raise TimeControlError(f"timeout: {what} at speed {speed} were not done in {limit_s:.0f} wall seconds")
            if self._monotonic() - last_check >= HOLD_CHECK_S:
                last_check = self._monotonic()
                resets += self._hold_speed(speed)
            if self._monotonic() - last_guard >= GUARD_CHECK_S:
                # A pop-up can open at any time and pauses the game. Close it here, not only between chunks.
                last_guard = self._monotonic()
                self._guard()
            self._sleep(POLL_S)
        wall_s = self._monotonic() - started
        paused = self.pause()
        record = {"clock_start": clock_start, "clock_end": paused["clock"], "wall_s": round(wall_s, 1),
                  "paused_at_end": paused["paused"], "speed": speed, "speed_resets": resets}
        self._log(f"run {what}: {record}")
        return record

    def _hold_speed(self, speed: int) -> int:
        """Set the speed again if the game dropped it (an army was spotted). Returns 1 for a reset, else 0."""
        if self._bridge.read_game_speed() == SPEED_FACTOR[speed]:
            return 0
        self._bridge.call_on_player("changeGameSpeed", [speed, False])
        return 1

    def _pause_after_timeout(self) -> None:
        # Never leave the game running after a timeout. A failed pause must not hide the timeout error.
        try:
            self._bridge.pause()
        except Exception as error:  # noqa: BLE001
            self._log(f"pause after timeout failed: {error}")


