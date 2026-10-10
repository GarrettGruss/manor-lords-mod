"""Baselines: ranges that a healthy run falls into (spec 08).

harness/baselines/<scenario>.json:
  {"scenario": "smoke", "metrics": {"duration_s": [40.0, 80.0]}, "strict": ["clock moves"]}
Only write_baseline changes a file, and only the --update-baseline option calls it.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .runresult import extract_metrics

BASELINES_DIR = Path(__file__).resolve().parent.parent / "baselines"
DEFAULT_MARGIN = 0.2  # of the observed spread
DEFAULT_FLOOR_FRACTION = 0.1  # of the largest absolute value, so a constant metric still gets room
ABSOLUTE_FLOOR = 0.001


class BaselineError(ValueError):
    """The baseline file or the data for a new baseline is wrong."""


@dataclass(frozen=True)
class Baseline:
    scenario: str
    metrics: dict[str, tuple[float, float]]
    strict: frozenset[str] = frozenset()


@dataclass(frozen=True)
class DriftFinding:
    metric: str
    value: float | None  # None: the run did not report this metric
    low: float
    high: float
    strict: bool

    @property
    def direction(self) -> str:
        if self.value is None:
            return "missing"
        return "below" if self.value < self.low else "above"

    def to_dict(self) -> dict:
        return {
            "metric": self.metric,
            "value": self.value,
            "range": [self.low, self.high],
            "direction": self.direction,
            "strict": self.strict,
        }


def baseline_path(scenario: str, baselines_dir: Path = BASELINES_DIR) -> Path:
    return Path(baselines_dir) / f"{scenario}.json"


def parse_baseline(data: dict, scenario: str) -> Baseline:
    try:
        metrics = {name: (float(pair[0]), float(pair[1])) for name, pair in data["metrics"].items()}
        strict = frozenset(data.get("strict", []))
    except (KeyError, TypeError, ValueError, IndexError, AttributeError) as error:
        raise BaselineError(f"Baseline for {scenario!r} is malformed ({error!r}). Expected metrics: {{name: [lo, hi]}}.") from error
    for name, (low, high) in metrics.items():
        if low > high:
            raise BaselineError(f"Baseline for {scenario!r}, metric {name!r}: lo {low} is above hi {high}.")
    unknown = sorted(strict - set(metrics))
    if unknown:
        raise BaselineError(f"Baseline for {scenario!r}: strict metric(s) {unknown} have no range.")
    return Baseline(scenario, metrics, strict)


def load_baseline(scenario: str, baselines_dir: Path = BASELINES_DIR) -> Baseline | None:
    """The baseline of a scenario, or None if there is no file."""
    path = baseline_path(scenario, baselines_dir)
    if not path.is_file():
        return None
    try:
        return parse_baseline(json.loads(path.read_text(encoding="utf-8")), scenario)
    except json.JSONDecodeError as error:
        raise BaselineError(f"Baseline file {path} is not valid JSON: {error}.") from error


def propose_baseline(
    summaries: list[dict],
    margin: float = DEFAULT_MARGIN,
    floor_fraction: float = DEFAULT_FLOOR_FRACTION,
    scenario: str = "",
) -> dict:
    """Ranges from passing summaries: min and max, widened by margin * spread (at least the floor)."""
    series: dict[str, list[float]] = {}
    for summary in summaries:
        for name, value in extract_metrics(summary).items():
            series.setdefault(name, []).append(value)
    if not series:
        raise BaselineError("No summary has a metric (duration_s or a numeric assertion value).")
    metrics = {name: list(_widen(values, margin, floor_fraction)) for name, values in sorted(series.items())}
    return {"scenario": scenario, "metrics": metrics, "strict": []}


def _widen(values: list[float], margin: float, floor_fraction: float) -> tuple[float, float]:
    low, high = min(values), max(values)
    floor = max(floor_fraction * max(abs(low), abs(high)), ABSOLUTE_FLOOR)
    padding = max(margin * (high - low), floor)
    return round(low - padding, 6), round(high + padding, 6)


def compare(baseline: Baseline, metrics: dict[str, float]) -> list[DriftFinding]:
    """Findings for every baseline metric that is outside its range or missing."""
    findings = []
    for name, (low, high) in baseline.metrics.items():
        value = metrics.get(name)
        if value is None or not low <= value <= high:
            findings.append(DriftFinding(name, value, low, high, strict=name in baseline.strict))
    return findings


def write_baseline(scenario: str, proposal: dict, baselines_dir: Path = BASELINES_DIR) -> Path:
    """Write the file for human review. Keep the strict flags of an older file."""
    old = load_baseline(scenario, baselines_dir)
    strict = sorted(old.strict & set(proposal["metrics"])) if old else []
    path = baseline_path(scenario, baselines_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {**proposal, "scenario": scenario, "strict": strict}
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return path
