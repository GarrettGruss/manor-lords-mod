"""Small statistics for A/B variants of stochastic runs (spec 10, U4). Standard library only.

The samples are small (3 to 30 runs per variant). The tests here are HEURISTICS for such samples:
they give a clear, repeatable rule, not a proof. See
openspec/changes/archive/2026-10-15-legacy-10-invasion-testability/implementation-notes/ab-statistics.md for the rules and their limits.
"""

from __future__ import annotations

import itertools
import math
import random
import statistics

MIN_RUNS_FOR_VERDICT = 3
DEFAULT_ALPHA = 0.1
MEDIUM_EFFECT = 0.5  # |Cohen's d| from which a difference counts as large enough to matter
EFFECT_CAP = 99.0  # the effect size when the pooled spread is zero but the means differ (JSON has no infinity)
EXACT_SPLIT_LIMIT = 20000  # enumerate all splits up to this count, else sample
RANDOM_PERMUTATIONS = 10000
PERMUTATION_SEED = 20261010  # fixed, so the same data always gives the same p-value
WILSON_Z = 1.96
FLOAT_TOLERANCE = 1e-9


def summarize(values: list[float]) -> dict:
    """n, min, median, max, mean and sample standard deviation. Empty input gives n = 0 only."""
    if not values:
        return {"n": 0}
    return {
        "n": len(values),
        "min": min(values),
        "median": statistics.median(values),
        "max": max(values),
        "mean": statistics.fmean(values),
        "stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
    }


def wilson_interval(passes: int, total: int, z: float = WILSON_Z) -> tuple[float, float]:
    """The Wilson score interval (95 percent by default) for a pass rate. Better than the plain rate for small n."""
    if total <= 0:
        return (0.0, 1.0)
    rate = passes / total
    denominator = 1 + z * z / total
    centre = (rate + z * z / (2 * total)) / denominator
    margin = z * math.sqrt(rate * (1 - rate) / total + z * z / (4 * total * total)) / denominator
    return (max(0.0, centre - margin), min(1.0, centre + margin))


def pass_rate(passes: int, total: int) -> dict:
    low, high = wilson_interval(passes, total)
    return {"passes": passes, "n": total, "rate": passes / total if total else None, "low": low, "high": high}


def cohens_d(a: list[float], b: list[float]) -> float | None:
    """(mean b - mean a) / pooled stdev. None if there are too few values.

    If both groups have no spread, the result is 0 for equal means and +-EFFECT_CAP otherwise.
    """
    if len(a) < 1 or len(b) < 1 or len(a) + len(b) < 3:
        return None
    degrees = len(a) + len(b) - 2
    pooled_variance = (
        (len(a) - 1) * (statistics.variance(a) if len(a) > 1 else 0.0)
        + (len(b) - 1) * (statistics.variance(b) if len(b) > 1 else 0.0)
    ) / degrees
    difference = statistics.fmean(b) - statistics.fmean(a)
    if pooled_variance <= 0.0:
        if abs(difference) <= FLOAT_TOLERANCE:
            return 0.0
        return math.copysign(EFFECT_CAP, difference)
    return max(-EFFECT_CAP, min(EFFECT_CAP, difference / math.sqrt(pooled_variance)))


def relative_difference(a: list[float], b: list[float]) -> float | None:
    """(median b - median a) / |median a|. None if the median of a is zero and the medians differ."""
    if not a or not b:
        return None
    median_a, median_b = statistics.median(a), statistics.median(b)
    if median_a == 0:
        return 0.0 if median_b == 0 else None
    return (median_b - median_a) / abs(median_a)


def ranges_overlap(a: list[float], b: list[float]) -> bool:
    """True if [min, max] of a and of b share a point. No overlap is strong evidence of a difference."""
    return bool(a) and bool(b) and max(min(a), min(b)) <= min(max(a), max(b))


def _mean_gap(first: list[float], second: list[float]) -> float:
    return abs(statistics.fmean(first) - statistics.fmean(second))


def _exact_count(pooled: list[float], size_a: int, observed: float) -> tuple[int, int]:
    count = total = 0
    indexes = range(len(pooled))
    for chosen in itertools.combinations(indexes, size_a):
        chosen_set = set(chosen)
        first = [pooled[i] for i in chosen]
        second = [pooled[i] for i in indexes if i not in chosen_set]
        total += 1
        count += _mean_gap(first, second) >= observed - FLOAT_TOLERANCE
    return count, total


def _sampled_count(pooled: list[float], size_a: int, observed: float, rounds: int) -> tuple[int, int]:
    generator = random.Random(PERMUTATION_SEED)
    count = 0
    for _ in range(rounds):
        shuffled = pooled[:]
        generator.shuffle(shuffled)
        count += _mean_gap(shuffled[:size_a], shuffled[size_a:]) >= observed - FLOAT_TOLERANCE
    return count + 1, rounds + 1  # the observed split counts as one of the permutations, so p is never 0


def permutation_p_value(a: list[float], b: list[float]) -> float | None:
    """Two-sided permutation test on the difference of means.

    Exact over all splits when there are at most EXACT_SPLIT_LIMIT of them, else RANDOM_PERMUTATIONS random
    shuffles with a fixed seed. A heuristic for small samples. None if a group is empty.
    """
    if not a or not b:
        return None
    pooled = list(a) + list(b)
    observed = _mean_gap(a, b)
    if math.comb(len(pooled), len(a)) <= EXACT_SPLIT_LIMIT:
        count, total = _exact_count(pooled, len(a), observed)
    else:
        count, total = _sampled_count(pooled, len(a), observed, RANDOM_PERMUTATIONS)
    return count / total


def decide_verdict(n_a: int, n_b: int, p_value: float | None, effect: float | None, alpha: float) -> str:
    """'different', 'same' or 'inconclusive'.

    - inconclusive if a variant has fewer than MIN_RUNS_FOR_VERDICT runs.
    - different if p <= alpha and |effect| >= MEDIUM_EFFECT.
    - same if p > alpha and |effect| < MEDIUM_EFFECT.
    - inconclusive otherwise: a large effect that is not significant (too few runs) or a significant but small effect.
    """
    if min(n_a, n_b) < MIN_RUNS_FOR_VERDICT or p_value is None or effect is None:
        return "inconclusive"
    significant = p_value <= alpha + FLOAT_TOLERANCE
    large = abs(effect) >= MEDIUM_EFFECT
    if significant and large:
        return "different"
    if not significant and not large:
        return "same"
    return "inconclusive"


def compare(a: list[float], b: list[float], alpha: float = DEFAULT_ALPHA) -> dict:
    """Compare the values of variant a (the reference) with variant b."""
    effect = cohens_d(a, b)
    p_value = permutation_p_value(a, b)
    return {
        "a_summary": summarize(a),
        "b_summary": summarize(b),
        "effect_size": effect,
        "rel_diff": relative_difference(a, b),
        "overlap": ranges_overlap(a, b),
        "p_value": p_value,
        "verdict": decide_verdict(len(a), len(b), p_value, effect, alpha),
    }
