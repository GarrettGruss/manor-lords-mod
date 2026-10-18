"""report.json (small) and report.md (human table) for one suite run (spec 08)."""

from __future__ import annotations

import json
from pathlib import Path

from . import ab, baselines, stats
from .baselines import DriftFinding
from .runner import STOP_ITERATION_CAP, STOP_NO_SLOTS, EntryOutcome, SuiteOutcome
from .runresult import worst_verdict

MAX_REPORT_JSON_BYTES = 4096  # for a passing suite without A/B variants
MAX_AB_REPORT_JSON_BYTES = 8192  # with the "ab" section: at most 8 metrics per compared variant
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
    if entry.entry.has_variants and not entry.skipped_note:
        data["variants"] = [variant_report(entry, name) for name in entry.variant_order]
    return data


def variant_report(entry: EntryOutcome, name: str) -> dict:
    """One line per variant: runs, passes, the Wilson interval of the pass rate and the median duration."""
    finals = [repeat[-1] for repeat in entry.repeats_of(name)]
    passes = sum(1 for final in finals if final.verdict == "pass")
    interval = stats.pass_rate(passes, len(finals))
    durations = [final.duration_s for final in finals if final.verdict == "pass"]
    data = {
        "name": name,
        "verdict": worst_verdict([final.verdict for final in finals]),
        "runs": len(finals),
        "passes": passes,
        "pass_interval": [round(interval["low"], 2), round(interval["high"], 2)],
    }
    if durations:
        data["median_duration_s"] = round(stats.summarize(durations)["median"], 1)
    return data


def _rounded(value, digits: int = 3):
    return None if value is None else round(value, digits)


def comparison_report(item: ab.MetricComparison) -> dict:
    result = item.result
    return {
        "variant": item.variant,
        "metric": cut(item.metric),
        "verdict": result["verdict"],
        "effect_size": _rounded(result["effect_size"], 2),
        "rel_diff": _rounded(result["rel_diff"]),
        "p_value": _rounded(result["p_value"]),
        "overlap": result["overlap"],
        "medians": [_rounded(result["a_summary"]["median"]), _rounded(result["b_summary"]["median"])],
        "n": [result["a_summary"]["n"], result["b_summary"]["n"]],
    }


def ab_report(entry: EntryOutcome, comparisons: list[ab.MetricComparison]) -> dict:
    data: dict = {
        "scenario": entry.entry.scenario,
        "reference": entry.variant_order[0],
        "compared": [comparison_report(item) for item in ab.strongest(comparisons)],
    }
    if entry.entry.expect:
        data["expect"] = ab.check_expectation(entry.entry.expect, comparisons, entry.variant_order)
    return data


def decide_exit_code(outcome: SuiteOutcome, statuses: list[str], expectation_failed: bool = False) -> int:
    """4 harness error, 3 incomplete, 2 unresolved crash or timeout, 1 fail, strict drift or a missed A/B expectation, else 0."""
    verdicts = [entry.verdict for entry in outcome.entries]
    if "harness_error" in verdicts:
        return EXIT_HARNESS_ERROR
    if outcome.stop_reason:
        return EXIT_BUDGET
    if "crash" in verdicts or "timeout" in verdicts:
        return EXIT_CRASH
    if "fail" in verdicts or "strict-drift" in statuses or expectation_failed:
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
    all_comparisons = {id(item): ab.compare_entry(item) for item in outcome.entries if item.entry.has_variants and not item.skipped_note}
    ab_sections = [ab_report(item, all_comparisons[id(item)]) for item in outcome.entries if id(item) in all_comparisons]
    expectation_failed = any(not section["expect"]["met"] for section in ab_sections if "expect" in section)
    exit_code = decide_exit_code(outcome, statuses, expectation_failed)
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
    if ab_sections:
        report["ab"] = ab_sections
        different = sum(ab.count_different(found) for found in all_comparisons.values())
        report["notes"] = [f"ab: different on {different} metrics"]
    if outcome.stop_reason:
        report["stopped"] = _stop_text(outcome)
    if outcome.bad_slots:
        report["bad_slots"] = [f"slot {slot}: {cut(reason)}" for slot, reason in sorted(outcome.bad_slots.items())]
    if outcome.not_run:
        report["not_run"] = sorted(set(outcome.not_run))
    skipped = [item["note"] for item in scenarios if item["verdict"] == "skipped"]
    if skipped:
        report["skipped"] = skipped
    return report


def _stop_text(outcome: SuiteOutcome) -> str:
    if outcome.stop_reason == STOP_ITERATION_CAP:
        return "iteration cap reached. Raise --max-runs of run.py (or set HARNESS_MAX_RUNS) or reset runs/.iterations."
    if outcome.stop_reason == STOP_NO_SLOTS:
        return "no game slot could start a run (see bad_slots). Check harness/install.ps1 and game_status."
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
    for key, label in (("stopped", "Stopped"), ("bad_slots", "Bad slots"), ("not_run", "Not run"), ("skipped", "Skipped"), ("notes", "Notes")):
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
    lines += _ab_lines(report)
    return "\n".join(lines) + "\n"


def _ab_lines(report: dict) -> list[str]:
    """The A/B tables. The first variant is the reference. Effect size is Cohen's d, positive when the variant is higher."""
    lines: list[str] = []
    variants_by_scenario = {item["scenario"]: item.get("variants", []) for item in report["scenarios"]}
    for section in report.get("ab", []):
        lines += ["", f"## A/B: {section['scenario']} (reference: {section['reference']})", "",
                  "| Variant | Runs | Passes | Pass rate 95% | Median duration (s) |", "|---|---|---|---|---|"]
        for variant in variants_by_scenario.get(section["scenario"], []):
            low, high = variant["pass_interval"]
            lines.append(f"| {variant['name']} | {variant['runs']} | {variant['passes']} | {low:.2f} to {high:.2f} "
                         f"| {variant.get('median_duration_s', '-')} |")
        lines += ["", "| Variant | Metric | Verdict | Effect d | Rel. diff | p | Ranges overlap | Median ref -> variant | n |",
                  "|---|---|---|---|---|---|---|---|---|"]
        for item in section["compared"]:
            lines.append(f"| {item['variant']} | {item['metric']} | {item['verdict']} | {item['effect_size']} | {item['rel_diff']} "
                         f"| {item['p_value']} | {'yes' if item['overlap'] else 'no'} | {item['medians'][0]} -> {item['medians'][1]} "
                         f"| {item['n'][0]}/{item['n'][1]} |")
        if "expect" in section:
            expect = section["expect"]
            lines += ["", f"Expectation: {expect['metric']} {expect['direction']} by at least {expect['min_rel_diff']}: "
                          f"{'MET' if expect['met'] else 'NOT MET'} ({expect['reason']})"]
    if lines:
        lines += ["", "Verdicts use a permutation test and an effect size. They are heuristics for small samples "
                      "(see openspec/changes/archive/2026-10-15-legacy-10-invasion-testability/implementation-notes/ab-statistics.md)."]
    return lines


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
