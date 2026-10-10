"""Run folder, config file, run lock and iteration counter."""

from __future__ import annotations

import json
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import psutil


DEFAULT_MAX_RUNS = 400  # a safety rail for unattended loops. Delete runs/.iterations to reset the counter.
MAX_RUNS_ENV = "HARNESS_MAX_RUNS"  # overrides the default. The option --max-runs of run.py overrides both.


class RunLockedError(RuntimeError):
    """Another live process holds the run lock."""

    def __init__(self, holder_pid: int | None, lock_path: Path):
        self.holder_pid = holder_pid
        who = f"process {holder_pid}" if holder_pid is not None else "an unknown process"
        super().__init__(f"Run lock {lock_path} is held by {who}. Wait for that run to end.")


class IterationLimitError(RuntimeError):
    """The session reached its cap on the number of runs."""


def new_run_id(now: datetime | None = None) -> str:
    """Return YYYYMMDD-HHMMSS-<4 hex>. The time is UTC. The suffix avoids clashes in one second."""
    now = now or datetime.now(timezone.utc)
    return f"{now:%Y%m%d-%H%M%S}-{secrets.token_hex(2)}"


def atomic_write_text(path: Path, text: str) -> None:
    """Write a .tmp file, then rename it, so a reader never sees half a file."""
    tmp_path = path.with_name(path.name + ".tmp")
    tmp_path.write_text(text, encoding="utf-8")
    os.replace(tmp_path, path)


@dataclass(frozen=True)
class RunFolder:
    path: Path
    run_id: str

    @property
    def summary_path(self) -> Path:
        return self.path / "summary.json"

    @property
    def config_path(self) -> Path:
        return self.path / "config.json"

    @property
    def boot_path(self) -> Path:
        return self.path / "boot.json"

    @property
    def screenshots_dir(self) -> Path:
        return self.path / "screenshots"

    @property
    def crash_dir(self) -> Path:
        return self.path / "crash"

    @property
    def bridge_dir(self) -> Path:
        return self.path / "bridge"


def create_run_folder(runs_root: Path, run_id: str | None = None) -> RunFolder:
    """Create runs/<id>/ with its sub folders. Refuse an id that already exists."""
    run_id = run_id or new_run_id()
    folder = RunFolder(path=Path(runs_root) / run_id, run_id=run_id)
    # exist_ok=False makes the check and the creation one step.
    folder.path.mkdir(parents=True, exist_ok=False)
    for sub_dir in (folder.screenshots_dir, folder.crash_dir, folder.bridge_dir):
        sub_dir.mkdir()
    return folder


def write_config(run_folder: RunFolder, config: dict) -> None:
    atomic_write_text(run_folder.config_path, json.dumps(config, indent=2, sort_keys=True))


class RunLock:
    """Lock file runs/.lock that holds the PID of the owner. Use as a context manager."""

    def __init__(self, runs_root: Path):
        self.lock_path = Path(runs_root) / ".lock"
        self.took_over_pid: int | None = None

    def __enter__(self) -> "RunLock":
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._try_create():
            self._take_over_if_stale()
        return self

    def __exit__(self, *exc_info) -> None:
        # Remove the lock only if it is still ours.
        if self._read_pid() == os.getpid():
            self.lock_path.unlink(missing_ok=True)

    def _try_create(self) -> bool:
        try:
            fd = os.open(self.lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            return False
        with os.fdopen(fd, "w") as lock_file:
            lock_file.write(str(os.getpid()))
        return True

    def _read_pid(self) -> int | None:
        try:
            return int(self.lock_path.read_text().strip())
        except (FileNotFoundError, ValueError):
            return None

    def _take_over_if_stale(self) -> None:
        holder_pid = self._read_pid()
        if holder_pid is None or psutil.pid_exists(holder_pid):
            raise RunLockedError(holder_pid, self.lock_path)
        self.lock_path.unlink(missing_ok=True)
        if not self._try_create():
            # Another process took the lock between our delete and create.
            raise RunLockedError(self._read_pid(), self.lock_path)
        self.took_over_pid = holder_pid


def default_max_runs(environ: dict | None = None) -> int:
    """The cap on runs: the environment variable HARNESS_MAX_RUNS, else DEFAULT_MAX_RUNS. A bad value is an error."""
    text = (os.environ if environ is None else environ).get(MAX_RUNS_ENV, "").strip()
    if not text:
        return DEFAULT_MAX_RUNS
    try:
        value = int(text)
    except ValueError:
        value = 0
    if value < 1:
        raise ValueError(f"{MAX_RUNS_ENV}={text!r} is not a whole number of 1 or more. Fix or unset it.")
    return value


def bump_iterations(runs_root: Path, max_runs: int) -> int:
    """Add one to runs/.iterations and return the new count. Refuse to pass max_runs."""
    counter_path = Path(runs_root) / ".iterations"
    try:
        current = int(counter_path.read_text().strip())
    except FileNotFoundError:
        current = 0
    except ValueError as error:
        raise ValueError(f"Iteration counter {counter_path} is not a number. Fix or delete it.") from error
    if current >= max_runs:
        raise IterationLimitError(
            f"Iteration limit reached: {current} runs done, max is {max_runs}. "
            f"Raise --max-runs (or set {MAX_RUNS_ENV}) or reset {counter_path}."
        )
    atomic_write_text(counter_path, str(current + 1))
    return current + 1
