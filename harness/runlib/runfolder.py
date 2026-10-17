"""Run folder, config file, run lock and iteration counter."""

from __future__ import annotations

import json
import os
import secrets
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import psutil

from .shared import lock_root


DEFAULT_MAX_RUNS = 400  # a safety rail for unattended loops. Delete runs/.iterations to reset the counter.
UNLINK_RETRY_S = 2.0  # how long a lock release retries a delete that another process blocks
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


class PidLock:
    """A lock file that holds the PID of the owner. A lock of a dead process is taken over. Use as a context manager."""

    def __init__(self, lock_path: Path):
        self.lock_path = Path(lock_path)
        self.took_over_pid: int | None = None
        self.held = False

    def __enter__(self) -> "PidLock":
        if not self.held:  # a lock taken with acquire() first can still be used in a with block
            self.acquire()
        return self

    def __exit__(self, *exc_info) -> None:
        self.release()

    def acquire(self) -> None:
        """Take the lock or raise RunLockedError."""
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._try_create():
            self._take_over_if_stale()
        self.held = True

    def release(self) -> None:
        # Remove the lock only if it is still ours.
        if self._read_pid() == os.getpid():
            self._unlink()
        self.held = False

    def _unlink(self) -> None:
        # Windows refuses the delete while a waiting process reads the file. The read takes milliseconds.
        deadline = time.monotonic() + UNLINK_RETRY_S
        while True:
            try:
                self.lock_path.unlink(missing_ok=True)
                return
            except PermissionError:
                if time.monotonic() >= deadline:
                    raise
                time.sleep(0.01)

    def _try_create(self) -> bool:
        try:
            fd = os.open(self.lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except (FileExistsError, PermissionError):
            # Windows gives PermissionError while another process deletes the file: it still counts as taken.
            return False
        with os.fdopen(fd, "w") as lock_file:
            lock_file.write(str(os.getpid()))
        return True

    def _read_pid(self) -> int | None:
        try:
            return int(self.lock_path.read_text().strip())
        except (FileNotFoundError, PermissionError, ValueError):
            return None  # PermissionError: another process deletes or writes the file right now

    def _take_over_if_stale(self) -> None:
        holder_pid = self._read_pid()
        if holder_pid is None or psutil.pid_exists(holder_pid):
            raise RunLockedError(holder_pid, self.lock_path)
        self.lock_path.unlink(missing_ok=True)
        if not self._try_create():
            # Another process took the lock between our delete and create.
            raise RunLockedError(self._read_pid(), self.lock_path)
        self.took_over_pid = holder_pid


def run_lock_name(slot: int = 0) -> str:
    """Slot 0 keeps the old name runs/.lock, so older tools still see it."""
    return ".lock" if slot == 0 else f".lock-{slot}"


class RunLock(PidLock):
    """The run lock of one game slot: runs/.lock or runs/.lock-<n>. Two runs in the same slot cannot overlap."""

    def __init__(self, runs_root: Path, slot: int = 0):
        super().__init__(lock_root(runs_root) / run_lock_name(slot))  # shared by all worktrees
        self.slot = slot


class LockTimeoutError(RuntimeError):
    """A short shared lock was not free in time."""


class WaitLock(PidLock):
    """A short lock that waits until it is free: for shared state that parallel runs change (the user's save folder, counters).

    An empty or unreadable lock file counts as held, because its writer may be half way through the write.
    """

    def __init__(self, lock_path: Path, timeout_s: float = 120.0, poll_s: float = 0.1):
        super().__init__(lock_path)
        self.timeout_s = timeout_s
        self.poll_s = poll_s

    def acquire(self) -> None:
        deadline = time.monotonic() + self.timeout_s
        while True:
            try:
                PidLock.acquire(self)
                return
            except RunLockedError as error:
                if time.monotonic() >= deadline:
                    raise LockTimeoutError(f"{self.lock_path} was not free in {self.timeout_s:.0f} s: {error}") from error
            time.sleep(self.poll_s)


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
    counter_path = lock_root(runs_root) / ".iterations"
    with WaitLock(lock_root(runs_root) / ".iterations.lock", timeout_s=30):  # parallel runs must not lose a count
        return _bump_locked(counter_path, max_runs)


def _bump_locked(counter_path: Path, max_runs: int) -> int:
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
