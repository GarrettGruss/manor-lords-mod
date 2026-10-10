"""The default run_one: start harness/run.py as a subprocess and read its summary.json."""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path

from runlib.scenario import run_timeout_s as scenario_run_timeout_s

from .runresult import RunResult, result_from_summary, with_run_folder_metrics
from .suitefile import Variant

HARNESS_DIR = Path(__file__).resolve().parent.parent
LAUNCHER_ENV = "HARNESS_SUITE_LAUNCHER"
DEFAULT_RUN_TIMEOUT_S = 900.0  # the least time a run may take. A scenario with a longer limit gets more (runlib.scenario.run_timeout_s)
STDERR_TAIL_CHARS = 300
GAME_CLOSE_SCRIPT = HARNESS_DIR / "game-close.ps1"
GAME_CLOSE_GRACE_S = 10


def close_game() -> None:
    """Stop the game after a run timeout. run.py was killed, so its own teardown did not run."""
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(GAME_CLOSE_SCRIPT), "-GraceSeconds", str(GAME_CLOSE_GRACE_S)],
        capture_output=True,
        text=True,
    )


def kill_process_tree(process: subprocess.Popen) -> None:
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True)
    else:
        process.kill()


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


def variant_arguments(variant: Variant | None) -> list[str]:
    """The run.py options of a variant. The list form keeps a value with spaces in one piece (no shell)."""
    if variant is None:
        return []
    arguments: list[str] = []
    for pak_name in variant.paks:
        arguments += ["--pak", pak_name]
    for key, value in variant.env.items():
        arguments += ["--env", f"{key}={value}"]
    return arguments


class SubprocessLauncher:
    """Callable with the run_one signature. One call is one run.py process."""

    def __init__(self, runs_root: Path, command: list[str] | None = None, run_timeout_s: float | None = None, on_timeout=None):
        # on_timeout runs after a timeout kill. suite.py sets it to close_game for the real run.py.
        # run_timeout_s None: each run gets scenario_run_timeout_s(scenario, DEFAULT_RUN_TIMEOUT_S). A number is a fixed limit for all runs.
        self.on_timeout = on_timeout
        self.runs_root = Path(runs_root)
        self.command = command or default_command()
        self.run_timeout_s = run_timeout_s

    def __call__(self, scenario: str, run_id: str, fixture: str | None = None, variant: Variant | None = None) -> RunResult:
        arguments = ["--scenario", scenario, "--run-id", run_id, "--runs-root", str(self.runs_root)]
        if fixture:
            arguments += ["--fixture", fixture]
        arguments += variant_arguments(variant)
        started = time.monotonic()
        stderr, timed_out, start_error = "", False, None
        timeout_s = self.run_timeout_s if self.run_timeout_s is not None else scenario_run_timeout_s(scenario, DEFAULT_RUN_TIMEOUT_S)
        try:
            stderr, timed_out = self._run_process(arguments, timeout_s)
        except OSError as error:
            start_error = f"could not start the launcher: {error}"
        wall_s = time.monotonic() - started
        if timed_out and self.on_timeout:
            self.on_timeout()
        return self._read_result(run_id, wall_s, stderr, timed_out, start_error, timeout_s)

    def _run_process(self, arguments: list[str], timeout_s: float) -> tuple[str, bool]:
        """Return (stderr, timed_out). On a timeout the whole process tree is killed."""
        process = subprocess.Popen([*self.command, *arguments], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            _, stderr = process.communicate(timeout=timeout_s)
            return stderr or "", False
        except subprocess.TimeoutExpired:
            kill_process_tree(process)
            process.communicate()
            return "", True

    def _read_result(self, run_id, wall_s, stderr, timed_out, start_error, timeout_s) -> RunResult:
        summary_path = self.runs_root / run_id / "summary.json"
        if summary_path.is_file():
            return self._result_from_file(run_id, summary_path, wall_s)
        if start_error:
            return RunResult(run_id, "harness_error", wall_s, reason=start_error)
        if timed_out:
            return RunResult(run_id, "timeout", wall_s, reason=f"run.py did not end within {timeout_s:.0f} s")
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
            result = result_from_summary(run_id, json.loads(path.read_text(encoding="utf-8")))
            return with_run_folder_metrics(result, path.parent)
        except (json.JSONDecodeError, OSError, AttributeError) as error:
            return RunResult(run_id, "harness_error", wall_s, reason=f"summary.json is unreadable: {error}")
