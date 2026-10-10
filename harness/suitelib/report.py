"""report.json (small) and report.md (human table) for one suite run (spec 08)."""

from __future__ import annotations

import json
from pathlib import Path

from . import baselines
from .baselines import DriftFinding
from .runner import STOP_ITERATION_CAP, EntryOutcome, SuiteOutcome

MAX_REPORT_JSON_BYTES = 4096  # for a passing suite
MAX_TEXT_CHARS = 60
MAX_REASON_CHARS = 120
MAX_FAILED_ASSERTS = 5
MAX_FAILED_RUNS = 5
MAX_DRIFT_FINDINGS = 3
MAX_DURATIONS = 12

EXIT_PASS, EXIT_FAIL, EXIT_CRASH, EXIT_BUDGET, EXIT_HARNESS_ERROR = 0, 1, 2, 3, 4


def cut(text, limit: int = MAX_TEXT_CHARS) -> str:
    text = str(text)
    return text if len(text) <= limit else text[: limit - 3] + "..."


def collect_drift(entry: EntryOutcome, baseline: baselines.Baseline | None) -> list[DriftFinding] | None:
    """Drift findings over the passing runs of an entry. None if there is no baseline.

    Only passing runs are compared. A failed run has its own verdict.
    Each metric is reported once, with the first value that is out of range.
    """
    if baseline is None:
        return None
    found: dict[str, DriftFinding] = {}
    for attempt in entry.attempts:
        if attempt.verdict == "pass":
            for finding in baselines.compare(baseline, attempt.metrics):
                found.setdefault(finding.metric, finding)
    return list(found.values())


def evaluate_baselines(outcome: SuiteOutcome, baselines_dir: Path) -> dict[str, list[DriftFinding] | None]:
    return {
        item.entry.scenario: collect_drift(item, baselines.load_baseline(item.entry.scenario, baselines_dir))
        for item in outcome.entries
        if not item.skipped_note
    }


def _baseline_status(findings: list[DriftFinding] | None) -> str:
    if findings is None:
        return "none"
    if any(finding.strict for finding in findings):
        return "strict-drift"
    return "drift" if findings else "ok"


def _value_for_json(value):
    return value if isinstance(value, (int, float, bool)) or value is None else cut(value)


def _failed_asserts(entry: EntryOutcome) -> list[dict]:
    failed = []
    for attempt in entry.attempts:
        for item in attempt.failed_asserts:
            found = {"name": cut(item["name"]), "value": _value_for_json(item["value"])}
            # A retry that fails the same way adds no information.
            if found not in failed:
                failed.append(found)
    return failed[:MAX_FAILED_ASSERTS]


def scenario_report(entry: EntryOutcome, findings: list[DriftFinding] | None, flake_rate: float | None) -> dict:
    attempts = entry.attempts
    data: dict = {
        "scenario": entry.entry.scenario,
        "verdict": entry.verdict,
        "attempts": len(attempts),
        "passes": sum(1 for attempt in attempts if attempt.verdict == "pass"),
        "stability": "flaky" if entry.flaky else "stable",
        "durations": [round(attempt.duration_s, 1) for attempt in attempts][:MAX_DURATIONS],
        "baseline": _baseline_status(findings),
    }
    if flake_rate is not None:
        data["flake_rate"] = flake_rate
    optional_parts = {
        "failed": _failed_asserts(entry),
        "failed_runs": [attempt.run_id for attempt in attempts if attempt.verdict != "pass"][:MAX_FAILED_RUNS],
        "drift": [finding.to_dict() for finding in (findings or [])][:MAX_DRIFT_FINDINGS],
        "note": cut(entry.skipped_note, MAX_REASON_CHARS) if entry.skipped_note else None,
    }
    data.update({key: value for key, value in optional_parts.items() if value})
    if entry.verdict not in ("pass", "skipped") and attempts[-1].reason:
        data["reason"] = cut(attempts[-1].reason, MAX_REASON_CHARS)
    return data


def decide_exit_code(outcome: SuiteOutcome, statuses: list[str]) -> int:
    """4 harness error, 3 incomplete, 2 unresolved crash or timeout, 1 fail or strict drift, else 0."""
    verdicts = [entry.verdict for entry in outcome.entries]
    if "harness_error" in verdicts:
        return EXIT_HARNESS_ERROR
    if outcome.stop_reason:
        return EXIT_BUDGET
    if "crash" in verdicts or "timeout" in verdicts:
        return EXIT_CRASH
    if "fail" in verdicts or "strict-drift" in statuses:
        return EXIT_FAIL
    return EXIT_PASS


def _suite_verdict(exit_code: int, statuses: list[str]) -> str:
    if exit_code in (EXIT_FAIL, EXIT_CRASH, EXIT_HARNESS_ERROR):
        return "fail"
    if exit_code == EXIT_BUDGET:
        return "incomplete"
    return "drift" if "drift" in statuses else "pass"


def build_report(
    outcome: SuiteOutcome,
    findings: dict[str, list[DriftFinding] | None],
    flake_rates: dict[str, float | None] | None = None,
) -> dict:
    flake_rates = flake_rates or {}
    scenarios = [
        scenario_report(item, findings.get(item.entry.scenario), flake_rates.get(item.entry.scenario))
        for item in outcome.entries
    ]
    statuses = [item["baseline"] for item in scenarios]
    exit_code = decide_exit_code(outcome, statuses)
    attempts = [attempt for item in outcome.entries for attempt in item.attempts]
    report: dict = {
        "suite": outcome.suite.name,
        "suite_id": outcome.suite_id,
        "verdict": _suite_verdict(exit_code, statuses),
        "exit_code": exit_code,
        "totals": {
            "scenarios": len(scenarios),
            "runs": len(attempts),
            "passed_runs": sum(1 for attempt in attempts if attempt.verdict == "pass"),
            "flaky": sum(1 for item in scenarios if item["stability"] == "flaky"),
        },
        "elapsed_s": round(outcome.elapsed_s, 1),
        "budget_s": outcome.budget_s,
        "scenarios": scenarios,
    }
    if outcome.stop_reason:
        report["stopped"] = _stop_text(outcome)
    if outcome.not_run:
        report["not_run"] = sorted(set(outcome.not_run))
    skipped = [item["note"] for item in scenarios if item["verdict"] == "skipped"]
    if skipped:
        report["skipped"] = skipped
    return report


def _stop_text(outcome: SuiteOutcome) -> str:
    if outcome.stop_reason == STOP_ITERATION_CAP:
        return "iteration cap reached. Raise --max-runs of run.py or reset runs/.iterations."
    return f"time budget of {outcome.budget_s:.0f} s used up. The suite is incomplete."


def render_json(report: dict) -> str:
    return json.dumps(report, indent=1, separators=(",", ":")) + "\n"


def render_markdown(report: dict) -> str:
    totals = report["totals"]
    lines = [
        f"# Suite {report['suite']} ({report['suite_id']}): {report['verdict']}",
        "",
        f"Exit code {report['exit_code']}. {totals['runs']} runs, {totals['passed_runs']} passed, "
        f"{totals['flaky']} flaky scenario(s). {report['elapsed_s']} s of {report['budget_s']:.0f} s.",
    ]
    for key, label in (("stopped", "Stopped"), ("not_run", "Not run"), ("skipped", "Skipped")):
        if report.get(key):
            value = report[key] if isinstance(report[key], str) else "; ".join(report[key])
            lines.append(f"{label}: {value}")
    lines += ["", "| Scenario | Verdict | Passes | Stability | Durations (s) | Baseline |", "|---|---|---|---|---|---|"]
    for item in report["scenarios"]:
        durations = ", ".join(str(value) for value in item["durations"]) or "-"
        lines.append(
            f"| {item['scenario']} | {item['verdict']} | {item['passes']}/{item['attempts']} "
            f"| {item['stability']} | {durations} | {item['baseline']} |"
        )
    lines += _detail_lines(report["scenarios"])
    return "\n".join(lines) + "\n"


def _detail_lines(scenarios: list[dict]) -> list[str]:
    lines: list[str] = []
    for item in scenarios:
        details = []
        if item.get("reason"):
            details.append(f"reason: {item['reason']}")
        details += [f"failed assertion {entry['name']} = {entry['value']}" for entry in item.get("failed", [])]
        details += [
            f"drift {entry['metric']} = {entry['value']} is {entry['direction']} {entry['range']}"
            + (" (strict)" if entry["strict"] else "")
            for entry in item.get("drift", [])
        ]
        if item.get("failed_runs"):
            details.append("run folders: " + ", ".join(item["failed_runs"]))
        if item.get("note"):
            details.append(item["note"])
        if details:
            lines += ["", f"## {item['scenario']}", *[f"- {text}" for text in details]]
    return lines


def write_report(report: dict, folder: Path) -> tuple[Path, Path]:
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    json_path, markdown_path = folder / "report.json", folder / "report.md"
    json_path.write_text(render_json(report), encoding="utf-8")
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    return json_path, markdown_path
