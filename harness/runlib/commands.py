"""The client side of the HarnessActions command channel (spec 07).

A command is the file `<run>/commands/<number>.json`. The mod answers with `<number>.result.json`.
The numbers are 0001, 0002, ... in order, because UE4SS Lua cannot list a folder. Files are written
to `.tmp` first and then renamed, so the reader never sees half a file.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Callable

ANSWER_TIMEOUT_S = 10.0
POLL_S = 0.1


class CommandError(Exception):
    """The mod did not answer, or it answered with ok=false. The message says why."""


class CommandChannel:
    """`sleep` and `monotonic` are parameters so tests can use a fake clock."""

    def __init__(self, folder: Path, timeout_s: float = ANSWER_TIMEOUT_S, sleep: Callable[[float], None] = time.sleep,
                 monotonic: Callable[[], float] = time.monotonic, check_alive: Callable[[], None] = lambda: None):
        self.folder = Path(folder)
        self._timeout_s = timeout_s
        self._sleep = sleep
        self._monotonic = monotonic
        self._check_alive = check_alive
        self._number = 0

    def send(self, command: str, **fields) -> dict:
        """Send one command and wait for its answer. Raise CommandError if there is none, or if it says ok=false."""
        self._number += 1
        name = f"{self._number:04d}"
        self._write_request(name, {"id": name, "command": command, **fields})
        answer = self._wait_for_answer(name, command)
        if not answer.get("ok"):
            raise CommandError(f"command {command} was refused by the game: {answer.get('error')}")
        return answer

    def _write_request(self, name: str, body: dict) -> None:
        self.folder.mkdir(parents=True, exist_ok=True)
        temp = self.folder / f"{name}.tmp"
        temp.write_text(json.dumps(body), encoding="utf-8")
        os.replace(temp, self.folder / f"{name}.json")

    def _wait_for_answer(self, name: str, command: str) -> dict:
        path = self.folder / f"{name}.result.json"
        started = self._monotonic()
        while True:
            self._check_alive()
            if path.is_file():
                return json.loads(path.read_text(encoding="utf-8"))
            if self._monotonic() - started > self._timeout_s:
                raise CommandError(
                    f"no answer to command {command} ({name}) in {self._timeout_s:.0f} s. Is the mod HarnessActions loaded?")
            self._sleep(POLL_S)
