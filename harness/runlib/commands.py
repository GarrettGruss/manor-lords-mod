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


class CommandRefused(CommandError):
    """The mod answered with ok=false. `reason` is the text of the mod, without the harness wording."""

    def __init__(self, command: str, reason: str):
        super().__init__(f"command {command} was refused by the game: {reason}")
        self.command = command
        self.reason = reason


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
            raise CommandRefused(command, str(answer.get("error")))
        return answer

    def _write_request(self, name: str, body: dict) -> None:
        self.folder.mkdir(parents=True, exist_ok=True)
        temp = self.folder / f"{name}.tmp"
        temp.write_text(json.dumps(body), encoding="utf-8")
        os.replace(temp, self.folder / f"{name}.json")

    @staticmethod
    def _read_answer(path: Path) -> dict | None:
        """Return the answer, or None when it is not ready. The mod may still hold the file open or half written (Windows says PermissionError)."""
        if not path.is_file():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (PermissionError, ValueError):
            return None

    def _wait_for_answer(self, name: str, command: str) -> dict:
        path = self.folder / f"{name}.result.json"
        started = self._monotonic()
        while True:
            self._check_alive()
            answer = self._read_answer(path)
            if answer is not None:
                return answer
            if self._monotonic() - started > self._timeout_s:
                raise CommandError(
                    f"no answer to command {command} ({name}) in {self._timeout_s:.0f} s. Is the mod HarnessActions loaded?")
            self._sleep(POLL_S)


class ModDidNotAnswer(CommandError):
    """A mod did not answer in time. The mod may not be loaded. `mod` is the name of the mod."""

    def __init__(self, mod: str, message: str):
        super().__init__(f"mod did not answer: {mod}. {message}")
        self.mod = mod


class ModCommandChannel:
    """The client side of the command channel of a mod (HarnessCommands, spec 10).

    Each mod serves its own folder `<run>/modcmd/<ModName>/` in its own Lua state. A request is `<number>.json`
    with `{"command", "args"}`. The answer is `<number>.result.json` with `{"ok", "result" | "error"}`.
    The mod creates its folder when it registers its first command or metric. A missing folder means the mod is not loaded.
    """

    def __init__(self, folder: Path, timeout_s: float = ANSWER_TIMEOUT_S, sleep: Callable[[float], None] = time.sleep,
                 monotonic: Callable[[], float] = time.monotonic, check_alive: Callable[[], None] = lambda: None):
        self.folder = Path(folder)
        self._timeout_s = timeout_s
        self._sleep = sleep
        self._monotonic = monotonic
        self._check_alive = check_alive
        self._numbers: dict[str, int] = {}

    def send(self, mod: str, command: str, args: dict | None = None) -> dict:
        """Send one command to a mod and wait for its answer.

        Raise ModDidNotAnswer when there is no folder or no answer. Raise CommandRefused when the mod says ok=false.
        """
        mod_folder = self.folder / mod
        started = self._monotonic()
        self._wait_for_folder(mod, command, mod_folder, started)
        name = f"{self._next_number(mod, mod_folder):04d}"
        self._write_request(mod_folder, name, {"command": command, "args": args or {}})
        answer = self._wait_for_answer(mod, command, mod_folder / f"{name}.result.json", name, started)
        if not answer.get("ok"):
            raise CommandRefused(command, str(answer.get("error")))
        return answer

    def _wait_for_folder(self, mod: str, command: str, mod_folder: Path, started: float) -> None:
        while not mod_folder.is_dir():
            self._check_alive()
            if self._monotonic() - started > self._timeout_s:
                raise ModDidNotAnswer(mod, f"There is no folder {mod_folder} for command {command}. Is the mod {mod} loaded and does it register a command?")
            self._sleep(POLL_S)

    def _next_number(self, mod: str, mod_folder: Path) -> int:
        """Continue after the highest request that is already in the folder, so a second client never reuses a number."""
        if mod not in self._numbers:
            existing = [int(path.stem) for path in mod_folder.glob("*.json") if path.stem.isdigit()]
            self._numbers[mod] = max(existing, default=0)
        self._numbers[mod] += 1
        return self._numbers[mod]

    @staticmethod
    def _write_request(mod_folder: Path, name: str, body: dict) -> None:
        temp = mod_folder / f"{name}.tmp"
        temp.write_text(json.dumps(body), encoding="utf-8")
        os.replace(temp, mod_folder / f"{name}.json")

    def _wait_for_answer(self, mod: str, command: str, path: Path, name: str, started: float) -> dict:
        while True:
            self._check_alive()
            answer = CommandChannel._read_answer(path)
            if answer is not None:
                return answer
            if self._monotonic() - started > self._timeout_s:
                raise ModDidNotAnswer(mod, f"No answer to command {command} ({name}) in {self._timeout_s:.0f} s. Is the mod {mod} loaded?")
            self._sleep(POLL_S)
