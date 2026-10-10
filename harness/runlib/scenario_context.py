"""The object a scenario function receives: bridge helpers, a log, the run folder and assertions."""

from __future__ import annotations

import json
import math
import re
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .actions import Actions
from .bridge_client import Bridge
from .commands import CommandChannel, ModCommandChannel
from .expectations import Expectations
from . import osinput
from .game import ensure_game_alive, find_game_processes
from .modstate import ModState
from .popups import PopupGuard
from .runfolder import atomic_write_text
from .runner import PhaseContext
from .snapshot import snapshot
from .telemetry import TelemetryReader
from .windows import list_windows, pick_game_window
from .timectl import TimeControl
from .waiting import WaitResult, run_until


MAX_REASON_CHARS = 300
METRICS_FILE = "metrics.json"  # read by the suite runner (spec 10, A/B statistics)
METRIC_NAME = re.compile(r"^[A-Za-z0-9_.-]{1,60}$")


class ScenarioLog:
    """Appends lines to a file and flushes each one, so a hung scenario still leaves its log."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self._lock = threading.Lock()

    def info(self, message: str) -> None:
        line = f"{datetime.now(timezone.utc):%H:%M:%S.%f}"[:-3] + f" {message}\n"
        with self._lock, self.path.open("a", encoding="utf-8") as log_file:
            log_file.write(line)


class ScenarioContext:
    def __init__(self, phase: PhaseContext, bridge: Bridge, screenshot_fn=None):
        self.phase = phase
        self.bridge = bridge
        self.run = phase.run
        self.run_dir = phase.run.path
        self.log = ScenarioLog(self.run_dir / "scenario.log")
        self._screenshot_fn = screenshot_fn
        self.expect = Expectations(self.log.info)
        self.time = TimeControl(bridge, check_alive=self.ensure_alive, log=self.log.info)
        self.telemetry = TelemetryReader(self.run_dir)
        self.notes: list[str] = []
        self._metrics: dict[str, float] = {}
        self.commands = CommandChannel(self.run_dir / "commands", check_alive=self.ensure_alive)
        self.actions = Actions(bridge, self.expect, self.notes, self.log.info, self.ensure_alive, self.commands,
                               mouse_placer=self._place_with_mouse)
        # ctx.popups() presses Accept on open pop-ups. Use it as on_poll or on_stall of ctx.run_until in a long scenario.
        self.popups = PopupGuard(lambda: self.commands.send("close_popups"), self.log.info)
        self.mod_commands = ModCommandChannel(self.run_dir / "modcmd", check_alive=self.ensure_alive)
        self.mod = ModState(self)  # commands and metrics of mods, served by each mod itself (spec 10, U10)

    # ---- real OS mouse (used by the action place_building) ----
    def _place_with_mouse(self, type_id: int, fx: float, fy: float) -> None:
        window = pick_game_window(list_windows(), {process.pid for process in find_game_processes()})
        player = self.bridge.player_path()
        steps = osinput.PlacementSteps(
            activate=lambda: self.bridge.call_function(player, "activateBuildingMode", [type_id]),
            cancel=lambda: self.bridge.call_function(player, "resetBuildingMode"),
            ground_under_cursor=lambda: osinput.is_ground_point(self.bridge.call_function(player, "getMouse3d")),
            unpause=self.unpause,
            pause=self.pause,
        )
        osinput.place_with_mouse(osinput.Win32Input(), window["hwnd"], steps, fx, fy)

    # ---- game helpers ----
    def ensure_alive(self, where: str = "scenario") -> None:
        ensure_game_alive(self.phase, where)

    def read_clock(self, wait_s: float = 3.0) -> dict:
        self.ensure_alive()
        result = self.bridge.measure_clock(wait_s)
        self.log.info(f"read_clock {result}")
        return result

    def read_calendar(self) -> dict:
        self.ensure_alive()
        result = self.bridge.read_calendar()
        self.log.info(f"read_calendar {result}")
        return result

    def pause(self) -> dict:
        self.ensure_alive()
        result = self.bridge.pause()
        self.log.info(f"pause {result}")
        return result

    def unpause(self) -> dict:
        self.ensure_alive()
        result = self.bridge.unpause()
        self.log.info(f"unpause {result}")
        return result

    def run_until(self, predicate, timeout_s: float, *, what: str = "the condition", clock: str = "wall", **options) -> WaitResult:
        """Poll `predicate()` until it is true. `timeout_s` counts wall seconds (clock="wall") or game seconds (clock="game").

        Options: poll_s, stall_s and on_stall (stall detector), on_poll. Raises WaitTimeout or GameStalled with a clear message.
        The game does not run by itself: start it first (for example with `ctx.time.set_speed`). See runlib/waiting.py.
        """
        options.setdefault("read_clock", self.bridge.read_clock_value)
        options.setdefault("check_alive", self.ensure_alive)
        options.setdefault("log", self.log.info)
        result = run_until(predicate, timeout_s, what=what, clock=clock, **options)
        self.log.info(f"run_until {what}: {result.as_dict()}")
        return result

    def screenshot(self, name: str) -> None:
        if self._screenshot_fn:
            self._screenshot_fn(self.phase, name)

    def snapshot(self) -> dict:
        self.ensure_alive()
        return snapshot(self.bridge)

    # ---- metrics for A/B statistics ----
    def metric(self, name: str, value: float) -> None:
        """Record one number of this run (for example `ticks` or `losses`) in <run>/metrics.json.

        The suite compares these numbers between variants. A second call with the same name replaces the value.
        """
        if not METRIC_NAME.fullmatch(name):
            raise ValueError(f"bad metric name {name!r}: use 1 to 60 characters from A-Z a-z 0-9 _ . -")
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f"metric {name!r} must be a finite number, got {value!r}")
        self._metrics[name] = float(value)
        atomic_write_text(self.run_dir / METRICS_FILE, json.dumps(self._metrics, indent=1))
        self.log.info(f"metric {name} = {value}")

    # ---- assertions ----
    def check(self, name: str, ok: bool, value: Any = None, range: list | None = None) -> bool:
        """A plain assertion. Prefer the typed ones in `ctx.expect`."""
        return self.expect.record(name, ok, value, f"{range[0]}..{range[1]}" if range else "")

    def check_range(self, name: str, value: float, low: float, high: float) -> bool:
        return self.expect.in_range(name, value, low, high)

    def fail(self, name: str, reason: str) -> dict:
        """End the scenario as failed with a clear reason, for example an action that is not possible."""
        self.expect.record(name, False, reason[:MAX_REASON_CHARS], "")
        return self.result()

    def result(self) -> dict:
        result = self.expect.result()
        if self.notes:
            result["notes"] = list(self.notes)
        return result
