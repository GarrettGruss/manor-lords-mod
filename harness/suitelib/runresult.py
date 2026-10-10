"""The result of one run, as the suite runner sees it."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field, replace
from pathlib import Path

# Order of "how bad", worst first. Used to pick one verdict for many runs.
VERDICTS_WORST_FIRST = ("harness_error", "crash", "timeout", "fail")


@dataclass(frozen=True)
class RunResult:
    run_id: str
    verdict: str  # pass, fail, crash, timeout or harness_error
    duration_s: float
    reason: str | None = None
    failed_asserts: list[dict] = field(default_factory=list)  # [{"name": ..., "value": ...}]
    metrics: dict[str, float] = field(default_factory=dict)
    # The launcher refused the run because the session run cap is reached.
    iteration_cap: bool = False
    # The launcher does not know the scenario. An optional entry is skipped then.
    unknown_scenario: bool = False


def _is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _asserts(summary: dict) -> list[dict]:
    return (summary.get("scenario_result") or {}).get("asserts") or []


def extract_metrics(summary: dict) -> dict[str, float]:
    """Metrics for baselines: duration_s and every numeric assertion value."""
    metrics: dict[str, float] = {}
    if _is_number(summary.get("duration_s")):
        metrics["duration_s"] = float(summary["duration_s"])
    for item in _asserts(summary):
        if _is_number(item.get("value")) and item.get("name"):
            metrics[str(item["name"])] = float(item["value"])
    return metrics


def extract_failed_asserts(summary: dict) -> list[dict]:
    return [{"name": str(item.get("name")), "value": item.get("value")} for item in _asserts(summary) if not item.get("ok")]


METRICS_FILE = "metrics.json"


def read_metrics_file(run_folder: Path) -> dict[str, float]:
    """The numbers a scenario wrote with ctx.metric(): a flat {name: number} file in the run folder.

    A missing or broken file gives no metrics. The run keeps its verdict: metrics are extra data.
    """
    try:
        data = json.loads((Path(run_folder) / METRICS_FILE).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {str(name): float(value) for name, value in data.items() if _is_number(value) and math.isfinite(value)}


def with_run_folder_metrics(result: RunResult, run_folder: Path) -> RunResult:
    """Add the metrics.json values. A metrics.json value wins over a summary value of the same name."""
    extra = read_metrics_file(run_folder)
    return replace(result, metrics={**result.metrics, **extra}) if extra else result


def result_from_summary(run_id: str, summary: dict) -> RunResult:
    return RunResult(
        run_id=run_id,
        verdict=str(summary.get("verdict", "harness_error")),
        duration_s=float(summary.get("duration_s") or 0.0),
        reason=summary.get("reason"),
        failed_asserts=extract_failed_asserts(summary),
        metrics=extract_metrics(summary),
    )


def worst_verdict(verdicts: list[str]) -> str:
    """pass if all pass. Otherwise the worst verdict."""
    for verdict in VERDICTS_WORST_FIRST:
        if verdict in verdicts:
            return verdict
    return "pass" if verdicts else "not_run"
