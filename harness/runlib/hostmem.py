"""Sample free physical memory of the PC into <run>/hostmem.jsonl while a scenario runs.

Why: the crash spike (spike-lua-crash-after-spawn) must rule memory pressure in or out. The game Lua cannot read it.
"""
from __future__ import annotations

import json
import threading
import time
from pathlib import Path

import psutil

FILE_NAME = "hostmem.jsonl"
INTERVAL_S = 2.0


def sample_line(game_pid: int | None, now: float | None = None) -> str:
    """One JSON line: unix time, free and total physical MB of the PC, and the resident MB of the game process."""
    memory = psutil.virtual_memory()
    rss_mb = None
    if game_pid is not None:
        try:
            rss_mb = round(psutil.Process(game_pid).memory_info().rss / 1048576)
        except psutil.Error:
            rss_mb = None
    return json.dumps({"t": round(now if now is not None else time.time(), 1),
                       "free_mb": round(memory.available / 1048576),
                       "total_mb": round(memory.total / 1048576),
                       "game_rss_mb": rss_mb})


class HostMemorySampler:
    """Background thread. start() before the scenario, stop() after. Append only, flushed at each line."""

    def __init__(self, run_path: Path, game_pid: int | None, interval_s: float = INTERVAL_S):
        self._path = Path(run_path) / FILE_NAME
        self._game_pid = game_pid
        self._interval_s = interval_s
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._loop, name="hostmem", daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=5)

    def _loop(self) -> None:
        with open(self._path, "a", encoding="utf-8") as handle:
            while True:
                handle.write(sample_line(self._game_pid) + "\n")
                handle.flush()
                if self._stop.wait(self._interval_s):
                    return
