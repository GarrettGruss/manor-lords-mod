"""runs/suite-history.jsonl: one line per run, to compute flake rates over time (spec 08)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .runner import SuiteOutcome

DEFAULT_WINDOW = 20


def history_lines(outcome: SuiteOutcome, now: datetime | None = None) -> list[dict]:
    stamp = (now or datetime.now(timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ")
    return [
        {
            "time": stamp,
            "suite": outcome.suite.name,
            "scenario": entry.entry.scenario,
            "verdict": attempt.verdict,
            "duration_s": round(attempt.duration_s, 2),
        }
        for entry in outcome.entries
        for attempt in entry.attempts
    ]


def append_history(path: Path, outcome: SuiteOutcome, now: datetime | None = None) -> None:
    lines = history_lines(outcome, now)
    if not lines:
        return
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as history_file:
        history_file.write("".join(json.dumps(line) + "\n" for line in lines))


def read_history(path: Path) -> list[dict]:
    if not Path(path).is_file():
        return []
    rows = []
    for number, text in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
        if not text.strip():
            continue
        try:
            rows.append(json.loads(text))
        except json.JSONDecodeError as error:
            raise ValueError(f"{path} line {number} is not valid JSON: {error}.") from error
    return rows


def flake_rate(rows: list[dict], scenario: str, window: int = DEFAULT_WINDOW) -> float | None:
    """Share of non-pass runs among the last `window` runs of a scenario.

    None if there is no data. A rate of 0 or 1 means stable or broken. Values between mean flaky.
    harness_error runs are ignored: they say nothing about the scenario.
    """
    verdicts = [row["verdict"] for row in rows if row["scenario"] == scenario and row["verdict"] != "harness_error"]
    recent = verdicts[-window:]
    if not recent:
        return None
    return round(sum(1 for verdict in recent if verdict != "pass") / len(recent), 3)
