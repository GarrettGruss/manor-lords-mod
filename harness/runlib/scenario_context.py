"""The object a scenario function receives: bridge helpers, a log, the run folder and assertions."""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .bridge_client import Bridge
from .game import ensure_game_alive
from .runner import PhaseContext


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
        self._asserts: list[dict] = []
        self._screenshot_fn = screenshot_fn

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

    # ---- assertions ----
    def check(self, name: str, ok: bool, value: Any = None, range: list | None = None) -> bool:
        entry: dict = {"name": name, "ok": bool(ok), "value": value}
        if range is not None:
            entry["range"] = range
        self._asserts.append(entry)
        self.log.info(f"assert {'ok' if ok else 'FAILED'}: {name} value={value} range={range}")
        return bool(ok)

    def check_range(self, name: str, value: float, low: float, high: float) -> bool:
        return self.check(name, low <= value <= high, value, [low, high])

    def result(self) -> dict:
        return {"passed": all(item["ok"] for item in self._asserts), "asserts": list(self._asserts)}
