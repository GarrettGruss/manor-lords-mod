"""The default run_one: start harness/run.py as a subprocess and read its summary.json."""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path

from .runresult import RunResult, result_from_summary

HARNESS_DIR = Path(__file__).resolve().parent.parent
LAUNCHER_ENV = "HARNESS_SUITE_LAUNCHER"
DEFAULT_RUN_TIMEOUT_S = 900.0
STDERR_TAIL_CHARS = 300


def default_command() -> list[str]:
    return [sys.executable, str(HARNESS_DIR / "run.py")]


def split_command(text: str) -> list[str]:
    # posix=False keeps Windows backslashes. It also keeps quotes, so they are removed here.
    return [part.strip('"') for part in shlex.split(text, posix=False)]


def resolve_command(option_text: str | None = None) -> list[str]:
    """The launcher command: the option, else the environment variable, else run.py."""
    for text in (option_text, os.environ.get(LAUNCHER_ENV)):
        if text and text.strip():
            return split_command(text)
    return default_command()


class SubprocessLauncher:
    """Callable with the run_one signature. One call is one run.py process."""

    def __init__(self, runs_root: Path, command: list[str] | None = None, run_timeout_s: float = DEFAULT_RUN_TIMEOUT_S):
        self.runs_root = Path(runs_root)
        self.command = command or default_command()
        self.run_timeout_s = run_timeout_s

    def __call__(self, scenario: str, run_id: str, fixture: str | None = None) -> RunResult:
        arguments = ["--scenario", scenario, "--run-id", run_id, "--runs-root", str(self.runs_root)]
        if fixture:
            arguments += ["--fixture", fixture]
        started = time.monotonic()
        stderr, timed_out, start_error = "", False, None
        try:
            done = subprocess.run([*self.command, *arguments], capture_output=True, text=True, timeout=self.run_timeout_s)
            stderr = done.stderr or ""
        except subprocess.TimeoutExpired:
            timed_out = True
        except OSError as error:
            start_error = f"could not start the launcher: {error}"
        wall_s = time.monotonic() - started
        return self._read_result(run_id, wall_s, stderr, timed_out, start_error)

    def _read_result(self, run_id, wall_s, stderr, timed_out, start_error) -> RunResult:
        summary_path = self.runs_root / run_id / "summary.json"
        if summary_path.is_file():
            return self._result_from_file(run_id, summary_path, wall_s)
        if start_error:
            return RunResult(run_id, "harness_error", wall_s, reason=start_error)
        if timed_out:
            return RunResult(run_id, "timeout", wall_s, reason=f"run.py did not end within {self.run_timeout_s:.0f} s")
        tail = stderr.strip()[-STDERR_TAIL_CHARS:]
        return RunResult(
            run_id,
            "harness_error",
            wall_s,
            reason=f"no summary.json. stderr: {tail or '(empty)'}",
            iteration_cap="Iteration limit" in stderr,
            unknown_scenario="Unknown scenario" in stderr,
        )

    @staticmethod
    def _result_from_file(run_id: str, path: Path, wall_s: float) -> RunResult:
        try:
            return result_from_summary(run_id, json.loads(path.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError, AttributeError) as error:
            return RunResult(run_id, "harness_error", wall_s, reason=f"summary.json is unreadable: {error}")
