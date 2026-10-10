"""The object a scenario function receives: bridge helpers, a log, the run folder and assertions."""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .actions import Actions
from .bridge_client import Bridge
from .commands import CommandChannel
from .expectations import Expectations
from .game import ensure_game_alive
from .runner import PhaseContext
from .snapshot import snapshot
from .telemetry import TelemetryReader
from .timectl import TimeControl


MAX_REASON_CHARS = 300


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
        commands = CommandChannel(self.run_dir / "commands", check_alive=self.ensure_alive)
        self.actions = Actions(bridge, self.expect, self.notes, self.log.info, self.ensure_alive, commands)

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

    def screenshot(self, name: str) -> None:
        if self._screenshot_fn:
            self._screenshot_fn(self.phase, name)

    def snapshot(self) -> dict:
        self.ensure_alive()
        return snapshot(self.bridge)

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
