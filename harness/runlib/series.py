"""Run the launcher several times and report the results as a table. Used by harness/run_series.py."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable

from .scenario import run_timeout_s

RUN_LINE = re.compile(r"^(?P<run_id>\S+) (?P<verdict>\w+) reason=(?P<reason>.*?) summary=(?P<summary>.+)$")
RUN_TIMEOUT_S = 600  # the least time one run may take. A scenario with a longer limit gets more (see scenario.run_timeout_s)
COLUMNS = ("n", "run_id", "verdict", "exit", "total_s", "boot_s", "reason")


def parse_run_line(output: str) -> dict | None:
    """Find the result line that run.py prints at the end. Return None if there is none."""
    for line in reversed(output.strip().splitlines()):
        match = RUN_LINE.match(line.strip())
        if match:
            return match.groupdict()
    return None


def _boot_seconds(summary: dict) -> float | None:
    boot = summary.get("boot") or {}
    return boot.get("seconds")


def build_row(index: int, exit_code: int, total_s: float, output: str, read_text: Callable = Path.read_text) -> dict:
    """One table row. If the run printed no result line, the row says harness_error."""
    row = {"n": index, "run_id": None, "verdict": "harness_error", "exit": exit_code,
           "total_s": round(total_s, 1), "boot_s": None, "reason": None}
    parsed = parse_run_line(output)
    if not parsed:
        row["reason"] = "no result line: " + output.strip()[-120:].replace("\n", " ")
        return row
    row.update(run_id=parsed["run_id"], verdict=parsed["verdict"], reason=None if parsed["reason"] == "-" else parsed["reason"])
    try:
        row["boot_s"] = _boot_seconds(json.loads(read_text(Path(parsed["summary"]), encoding="utf-8")))
    except (OSError, json.JSONDecodeError):
        row["reason"] = (row["reason"] or "") + " (summary.json not readable)"
    return row


def format_table(rows: list[dict]) -> str:
    cells = [[str(row[column]) if row[column] is not None else "-" for column in COLUMNS] for row in rows]
    widths = [max(len(column), *(len(line[i]) for line in cells)) if cells else len(column) for i, column in enumerate(COLUMNS)]
    lines = ["  ".join(column.ljust(widths[i]) for i, column in enumerate(COLUMNS))]
    lines += ["  ".join(value.ljust(widths[i]) for i, value in enumerate(line)).rstrip() for line in cells]
    return "\n".join(lines)


def tally(rows: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["verdict"]] = counts.get(row["verdict"], 0) + 1
    return counts


def run_launcher_once(run_py: Path, scenario: str, extra_args: list[str], timeout_s: float | None = None) -> tuple[int, str]:
    """Run run.py once. Return (exit code, stdout). A launcher that hangs is stopped and reported."""
    command = [sys.executable, str(run_py), "--scenario", scenario, *extra_args]
    if timeout_s is None:
        timeout_s = run_timeout_s(scenario, RUN_TIMEOUT_S)
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout_s)
    except subprocess.TimeoutExpired:
        return 4, f"launcher did not end in {timeout_s} s"
    return result.returncode, result.stdout + result.stderr


def run_series(run_py: Path, scenario: str, count: int, extra_args: list[str],
               run_once: Callable = run_launcher_once, clock: Callable[[], float] = time.monotonic) -> list[dict]:
    rows = []
    for index in range(1, count + 1):
        started = clock()
        exit_code, output = run_once(run_py, scenario, extra_args)
        rows.append(build_row(index, exit_code, clock() - started, output))
        print(f"run {index}/{count}: {rows[-1]['verdict']} {rows[-1]['run_id']}", flush=True)
    return rows
