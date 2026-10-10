"""summary.json: data classes, verdict rules and the size-limited atomic write."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .runfolder import atomic_write_text

PHASE_STATUSES = ("ok", "failed", "timeout", "skipped", "error")
EXIT_CODES = {"pass": 0, "fail": 1, "crash": 2, "timeout": 3, "harness_error": 4}
MAX_SUMMARY_BYTES = 4096


@dataclass
class PhaseResult:
    name: str
    status: str  # one of PHASE_STATUSES
    seconds: float = 0.0
    detail: str | None = None

    def __post_init__(self) -> None:
        if self.status not in PHASE_STATUSES:
            raise ValueError(f"Unknown phase status {self.status!r}. Use one of {PHASE_STATUSES}.")


@dataclass
class Summary:
    run_id: str
    verdict: str
    reason: str | None
    scenario: str | None
    started: str  # UTC, ISO 8601
    duration_s: float
    phases: list[PhaseResult]
    boot: dict | None = None
    scenario_result: dict | None = None
    crash: dict | None = None
    artifacts: dict = field(default_factory=dict)
    environment: dict = field(default_factory=dict)
    # Anything skipped, unknown or cut. The agent must read this before it trusts the verdict.
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def scenario_passed(scenario_result: dict | None) -> bool | None:
    """True or False if the result says so. None if the result is missing or unclear."""
    if not scenario_result:
        return None
    if "passed" in scenario_result:
        return bool(scenario_result["passed"])
    asserts = scenario_result.get("asserts")
    if asserts:
        return all(item.get("ok") for item in asserts)
    return None


def _first_phase(phases: list[PhaseResult], status: str) -> PhaseResult | None:
    return next((phase for phase in phases if phase.status == status), None)


def _describe(phase: PhaseResult) -> str:
    text = f"phase {phase.name} {phase.status}"
    return f"{text}: {phase.detail}" if phase.detail else text


def decide_verdict(phases: list[PhaseResult], state: dict) -> tuple[str, str | None]:
    """Return (verdict, reason).

    Precedence, first match wins:
      1. crash: the game died. This is a result with logs, and it explains
         the errors and timeouts that follow it.
      2. timeout: a phase hit its time limit.
      3. fail: the scenario failed its assertions, or HarnessBoot ended in FAILED.
         This comes before harness_error because a failed scenario is a real result,
         and the cleanup phases that follow may also report problems.
      4. harness_error: any other failed or error phase, or a skipped phase.
      5. harness_error: the scenario result is missing or unclear.
      6. pass: everything ran, and the scenario passed.
    """
    crash = state.get("crash")
    if crash:
        return "crash", str(crash.get("reason") or "the game ended without a stop request")

    timed_out = _first_phase(phases, "timeout")
    if timed_out:
        return "timeout", _describe(timed_out)

    boot = state.get("boot") or {}
    if boot.get("state") == "FAILED":
        return "fail", f"HarnessBoot ended in FAILED: {boot.get('reason', 'no reason given')}"
    passed = scenario_passed(state.get("scenario_result"))
    if passed is False:
        return "fail", "the scenario failed its assertions"

    for status in ("error", "failed", "skipped"):
        bad_phase = _first_phase(phases, status)
        if bad_phase:
            return "harness_error", _describe(bad_phase)

    if not phases:
        return "harness_error", "no phase ran"
    if passed is None:
        return "harness_error", "the scenario result is missing"
    return "pass", None


def _json_size(data: dict) -> int:
    return len(json.dumps(data, indent=2).encode("utf-8"))


def _cut(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[:limit] + "...[cut]"


def _shrink_details(data: dict, limit: int) -> None:
    # The reason can repeat a phase detail, so it is cut too.
    if data["reason"]:
        data["reason"] = _cut(data["reason"], limit)
    for phase in data["phases"]:
        if phase.get("detail"):
            phase["detail"] = _cut(phase["detail"], limit)


def _fit_to_limit(data: dict) -> dict:
    """Cut long detail strings until the JSON is under the size limit."""
    if _json_size(data) <= MAX_SUMMARY_BYTES:
        return data
    data["notes"].append(f"WARNING: summary was over {MAX_SUMMARY_BYTES} bytes. Long detail strings were cut.")
    for limit in (300, 100, 30, 0):
        _shrink_details(data, limit)
        if _json_size(data) <= MAX_SUMMARY_BYTES:
            return data
    data["notes"].append("WARNING: summary is still over the limit after all details were cut.")
    return data


def write_summary(path: Path, summary: Summary) -> None:
    atomic_write_text(Path(path), json.dumps(_fit_to_limit(summary.to_dict()), indent=2))
