"""Run the entries of a suite through an injectable run_one function (spec 08)."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable

from .runresult import RunResult, worst_verdict
from .suitefile import Suite, SuiteEntry

# run_one(scenario, run_id, fixture) -> RunResult. It must not raise, but the runner guards against it.
RunOne = Callable[[str, str, "str | None"], RunResult]

# A harness_error is not retried: the same setup would fail the same way.
RETRY_VERDICTS = ("fail", "crash", "timeout")

STOP_TIME_BUDGET = "time_budget"
STOP_ITERATION_CAP = "iteration_cap"


@dataclass
class EntryOutcome:
    entry: SuiteEntry
    # One list of attempts for each repeat. The last attempt of a list decides that repeat.
    repeats: list[list[RunResult]] = field(default_factory=list)
    skipped_note: str | None = None

    @property
    def attempts(self) -> list[RunResult]:
        return [attempt for repeat in self.repeats for attempt in repeat]

    @property
    def verdict(self) -> str:
        if self.skipped_note:
            return "skipped"
        return worst_verdict([repeat[-1].verdict for repeat in self.repeats])

    @property
    def flaky(self) -> bool:
        """The same scenario both passed and failed in this suite run."""
        verdicts = {attempt.verdict for attempt in self.attempts if attempt.verdict != "harness_error"}
        return "pass" in verdicts and len(verdicts) > 1


@dataclass
class SuiteOutcome:
    suite: Suite
    suite_id: str
    entries: list[EntryOutcome]
    budget_s: float
    elapsed_s: float
    stop_reason: str | None = None
    not_run: list[str] = field(default_factory=list)  # scenarios that never started


def _guarded(run_one: RunOne, scenario: str, run_id: str, fixture: str | None) -> RunResult:
    # One broken run must never stop the suite.
    started = time.monotonic()
    try:
        return run_one(scenario, run_id, fixture)
    except Exception as error:  # noqa: BLE001 - any failure of one run becomes a result
        return RunResult(run_id, "harness_error", time.monotonic() - started, reason=f"run_one raised {error!r}")


class _SuiteRun:
    def __init__(self, suite: Suite, run_one: RunOne, suite_id: str, budget_s: float, clock: Callable[[], float]):
        self.suite, self.run_one, self.suite_id = suite, run_one, suite_id
        self.budget_s, self.clock = budget_s, clock
        self.started = clock()
        self.stop_reason: str | None = None
        self.run_count = 0

    def budget_left(self) -> bool:
        if self.clock() - self.started >= self.budget_s:
            self.stop_reason = self.stop_reason or STOP_TIME_BUDGET
            return False
        return True

    def next_run_id(self, scenario: str, retry: int) -> str:
        self.run_count += 1
        suffix = f"-r{retry}" if retry else ""
        return f"{self.suite_id}-{self.run_count:03d}-{scenario}{suffix}"

    def run_attempt(self, entry: SuiteEntry, retry: int) -> RunResult:
        result = _guarded(self.run_one, entry.scenario, self.next_run_id(entry.scenario, retry), entry.fixture)
        if result.iteration_cap:
            self.stop_reason = STOP_ITERATION_CAP
        return result

    def run_repeat(self, entry: SuiteEntry) -> list[RunResult]:
        attempts: list[RunResult] = []
        for retry in range(self.suite.flake_retries + 1):
            if not self.budget_left():
                break
            result = self.run_attempt(entry, retry)
            if self.stop_reason == STOP_ITERATION_CAP:
                break  # the cap refused the run. It says nothing about the scenario.
            attempts.append(result)
            if result.verdict not in RETRY_VERDICTS:
                break
        return attempts

    def run_entry(self, entry: SuiteEntry) -> EntryOutcome:
        outcome = EntryOutcome(entry)
        for _ in range(entry.repeat):
            attempts = self.run_repeat(entry)
            if attempts:
                outcome.repeats.append(attempts)
            if self.stop_reason:
                break
            if self._is_unknown_optional(entry, attempts):
                outcome.repeats.clear()
                outcome.skipped_note = f"optional scenario {entry.scenario!r} does not exist yet. Skipped."
                break
        return outcome

    @staticmethod
    def _is_unknown_optional(entry: SuiteEntry, attempts: list[RunResult]) -> bool:
        return entry.optional and bool(attempts) and attempts[0].unknown_scenario


def run_suite(
    suite: Suite,
    run_one: RunOne,
    suite_id: str,
    max_seconds: float | None = None,
    clock: Callable[[], float] = time.monotonic,
) -> SuiteOutcome:
    """Run all entries in order. Stop at the time budget or the iteration cap, and say why."""
    budget_s = min(suite.time_budget_s, max_seconds) if max_seconds is not None else suite.time_budget_s
    state = _SuiteRun(suite, run_one, suite_id, budget_s, clock)
    outcomes: list[EntryOutcome] = []
    not_run: list[str] = []
    for entry in suite.entries:
        if state.stop_reason or not state.budget_left():
            not_run.append(entry.scenario)
            continue
        outcome = state.run_entry(entry)
        if outcome.repeats or outcome.skipped_note:
            outcomes.append(outcome)
        else:
            not_run.append(entry.scenario)  # the cap or the budget ended the suite before this entry ran
    return SuiteOutcome(
        suite=suite,
        suite_id=suite_id,
        entries=outcomes,
        budget_s=budget_s,
        elapsed_s=clock() - state.started,
        stop_reason=state.stop_reason,
        not_run=not_run,
    )
