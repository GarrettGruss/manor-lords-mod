"""A/B comparison of the variants of one suite entry (spec 10, U4).

The first variant of an entry is the reference. Every later variant is compared with it, metric by metric.
Only passing runs give values: a failed run has partial metrics and its own verdict.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import stats
from .runner import EntryOutcome
from .suitefile import Expectation

MAX_AB_METRICS = 8  # per compared variant: the metrics with the largest effect size


@dataclass(frozen=True)
class MetricComparison:
    variant: str
    metric: str
    result: dict  # the output of stats.compare


def collect_samples(outcome: EntryOutcome) -> dict[str, dict[str, list[float]]]:
    """{variant: {metric: [values]}}. A repeat counts through its last attempt, and only if that attempt passed."""
    samples: dict[str, dict[str, list[float]]] = {name: {} for name in outcome.variant_order}
    for repeat, name in zip(outcome.repeats, outcome.variant_names):
        final = repeat[-1]
        if final.verdict != "pass":
            continue
        for metric, value in final.metrics.items():
            samples[name].setdefault(metric, []).append(value)
    return samples


def compare_entry(outcome: EntryOutcome, alpha: float = stats.DEFAULT_ALPHA) -> list[MetricComparison]:
    """All comparisons of later variants with the first, for each metric both sides have."""
    order = outcome.variant_order
    if len(order) < 2:
        return []
    samples = collect_samples(outcome)
    reference = samples[order[0]]
    found: list[MetricComparison] = []
    for name in order[1:]:
        for metric in sorted(set(reference) & set(samples[name])):
            found.append(MetricComparison(name, metric, stats.compare(reference[metric], samples[name][metric], alpha)))
    return found


def strongest(comparisons: list[MetricComparison], limit: int = MAX_AB_METRICS) -> list[MetricComparison]:
    """For each variant, the `limit` comparisons with the largest absolute effect size. Order of variants is kept."""
    kept: list[MetricComparison] = []
    for name in dict.fromkeys(item.variant for item in comparisons):
        own = [item for item in comparisons if item.variant == name]
        own.sort(key=lambda item: abs(item.result["effect_size"] or 0.0), reverse=True)
        kept += own[:limit]
    return kept


def count_different(comparisons: list[MetricComparison]) -> int:
    return sum(1 for item in comparisons if item.result["verdict"] == "different")


def check_expectation(expect: Expectation, comparisons: list[MetricComparison], variant_names: list[str]) -> dict:
    """Does every later variant meet the rule? Returns {met, reason, ...}.

    Met needs: the verdict for the metric is 'different', the median moved in the wanted direction,
    and the relative difference of the medians is at least min_rel_diff. 'inconclusive' is not met.
    """
    problems: list[str] = []
    for name in variant_names[1:]:
        match = [item for item in comparisons if item.variant == name and item.metric == expect.metric]
        problems += _problems_for(expect, name, match[0].result if match else None)
    return {
        "metric": expect.metric,
        "direction": expect.direction,
        "min_rel_diff": expect.min_rel_diff,
        "met": not problems,
        "reason": "; ".join(problems) if problems else "met",
    }


def _problems_for(expect: Expectation, variant: str, result: dict | None) -> list[str]:
    if result is None:
        return [f"{variant}: metric {expect.metric!r} is missing in a variant (no passing run wrote it)"]
    if result["verdict"] != "different":
        return [f"{variant}: verdict is {result['verdict']}, not different"]
    rel_diff = result["rel_diff"]
    if rel_diff is None:
        return [f"{variant}: relative difference is undefined (median of the first variant is 0)"]
    moved_right = rel_diff < 0 if expect.direction == "lower" else rel_diff > 0
    if not moved_right:
        return [f"{variant}: {expect.metric} went {'up' if rel_diff > 0 else 'down'}, wanted {expect.direction}"]
    if abs(rel_diff) < expect.min_rel_diff:
        return [f"{variant}: relative difference {rel_diff:+.2f} is smaller than {expect.min_rel_diff}"]
    return []
