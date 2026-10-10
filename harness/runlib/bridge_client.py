"""Game questions and commands through the ue4ss-bridge, for scenarios.

Every call looks up the objects again. The path of the player pawn changes in each game session,
and a lookup costs only one round trip.
"""

from __future__ import annotations

import time
from typing import Any, Callable

ENGINE_CLASS = "RTSMultiEngineCPP"
# The clock counts as stopped when it moves less than this between two reads (game seconds).
STILL_LIMIT = 0.001

BridgeCall = Callable[..., dict]  # signature of ue4ss_bridge.server.one: one(op, **args) -> {"result": ...}


def object_path(value: Any) -> str:
    """Return the path of an object from a bridge value.

    The bridge returns objects as {"__object": "<Class> <path>", ...} and lists them as "<Class> <path>".
    """
    text = value["__object"] if isinstance(value, dict) else value
    if not isinstance(text, str) or " " not in text:
        raise ValueError(f"Not an object reference from the bridge: {value!r}")
    return text.split(" ", 1)[1]


class Bridge:
    """A thin client. `one` and `sleep` are parameters so tests can use fakes."""

    def __init__(self, one: BridgeCall, sleep: Callable[[float], None] = time.sleep):
        self._one = one
        self._sleep = sleep

    def _result(self, op: str, **args: Any) -> Any:
        return self._one(op, **args)["result"]

    def engine_path(self) -> str:
        found = self._result("objects", class_name=ENGINE_CLASS, limit=1)["objects"]
        if not found:
            raise RuntimeError(f"No {ENGINE_CLASS} object exists. The game world is not loaded.")
        return object_path(found[0])

    def player_path(self) -> str:
        return object_path(self._result("get", ref=self.engine_path(), name="playerRef"))

    def read_clock_value(self, engine: str | None = None) -> float:
        """Read the game clock. Pass `engine` (from engine_path) to save one round trip in a fast loop."""
        return self._result("call", ref=engine or self.engine_path(), function="getGameTimeAdjusted", args=[])

    def call_function(self, ref: str, function: str, args: list | None = None) -> Any:
        return self._result("call", ref=ref, function=function, args=args or [])

    def read_property(self, ref: str, name: str) -> Any:
        return self._result("get", ref=ref, name=name)

    def calendar_path(self, engine: str | None = None) -> str:
        return object_path(self.read_property(engine or self.engine_path(), "TemporalComponent"))

    def read_game_speed(self) -> float:
        """The game speed factor: 0 paused, 1, 4 or 8 (see spec 04 time-measurements)."""
        return self.read_property(self.engine_path(), "gameSpeed")

    def read_calendar(self) -> dict:
        calendar_path = object_path(self._result("get", ref=self.engine_path(), name="TemporalComponent"))
        names = {"day": "day", "month": "month", "year": "Year"}
        return {key: self._result("get", ref=calendar_path, name=name) for key, name in names.items()}

    def call_on_player(self, function: str, args: list | None = None) -> None:
        self._result("call", ref=self.player_path(), function=function, args=args or [])

    def measure_clock(self, wait_s: float) -> dict:
        first = self.read_clock_value()
        self._sleep(wait_s)
        second = self.read_clock_value()
        change = round(second - first, 3)
        return {"clock": second, "change": change, "seconds": wait_s, "paused": abs(change) < STILL_LIMIT}

    def wait_until_clock_moves(self, timeout_s: float, step_s: float = 0.5) -> dict:
        """Read the clock until it differs from the first read, or until the time is over."""
        first = self.read_clock_value()
        waited = 0.0
        while True:
            self._sleep(step_s)
            waited += step_s
            second = self.read_clock_value()
            change = round(second - first, 3)
            if abs(change) >= STILL_LIMIT or waited >= timeout_s:
                return {"clock": second, "change": change, "seconds": waited, "paused": abs(change) < STILL_LIMIT}

    def pause(self, hold_s: float = 3.0, attempts: int = 3) -> dict:
        """Call pauseGame, then check that the clock stands still for `hold_s`.

        The game can undo a pause in the first seconds after a load (spec 02), so the call is repeated.
        """
        last: dict = {}
        for attempt in range(1, attempts + 1):
            self.call_on_player("pauseGame")
            self._sleep(0.5)  # lets the pause take effect before the measurement starts
            last = self.measure_clock(hold_s)
            if last["paused"]:
                return {**last, "ok": True, "attempts": attempt}
        return {**last, "ok": False, "attempts": attempts}

    def unpause(self, timeout_s: float = 5.0, attempts: int = 2) -> dict:
        """Call unPauseGame, then wait until the clock moves."""
        last: dict = {}
        for attempt in range(1, attempts + 1):
            self.call_on_player("unPauseGame")
            last = self.wait_until_clock_moves(timeout_s)
            if not last["paused"]:
                return {**last, "ok": True, "attempts": attempt}
        return {**last, "ok": False, "attempts": attempts}
