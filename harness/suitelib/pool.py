"""Run a suite on several game slots at once (spec 11, step 4).

A job is one repeat of one entry and variant, with its retries. Jobs keep the order of the sequential runner
(entries in order, variants interleaved inside each repeat), so A and B runs spread over all slots alike.
"""

from __future__ import annotations

import time
from collections import deque
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from dataclasses import dataclass
from typing import Callable

from .runner import STOP_NO_SLOTS, EntryOutcome, RunOne, SuiteOutcome, _SuiteRun
from .runresult import RunResult
from .suitefile import DEFAULT_VARIANT_NAME, Suite, SuiteEntry, Variant


@dataclass(frozen=True)
class _Job:
    order: int
    entry_index: int
    entry: SuiteEntry
    variant: Variant | None

    @property
    def variant_name(self) -> str:
        return self.variant.name if self.variant else DEFAULT_VARIANT_NAME


def build_jobs(suite: Suite) -> list[_Job]:
    jobs: list[_Job] = []
    for entry_index, entry in enumerate(suite.entries):
        for _ in range(entry.repeat):
            for variant in entry.run_variants:
                jobs.append(_Job(len(jobs), entry_index, entry, variant))
    return jobs


class _Pool:
    def __init__(self, state: _SuiteRun, launchers: dict[int, RunOne], is_exclusive: Callable[[str], bool]):
        self.state, self.launchers, self.is_exclusive = state, launchers, is_exclusive
        self.free = sorted(launchers)
        self.bad_slots: dict[int, str] = {}
        self.running: dict[Future, tuple[_Job, int]] = {}
        self.results: list[tuple[_Job, list[RunResult]]] = []
        self.skipped: dict[int, str] = {}  # entry index -> note

    def may_start(self, job: _Job) -> bool:
        if any(self.is_exclusive(running.entry.scenario) for running, _ in self.running.values()):
            return False
        # An exclusive scenario waits until no other game runs.
        return not (self.is_exclusive(job.entry.scenario) and self.running)

    def start_jobs(self, pending: deque[_Job], executor: ThreadPoolExecutor) -> None:
        while pending and self.free and not self.state.stop_reason and self.state.budget_left():
            job = pending[0]
            if job.entry_index in self.skipped:
                pending.popleft()
                continue
            if not self.may_start(job):
                return
            pending.popleft()
            slot = self.free.pop(0)
            future = executor.submit(self.state.run_repeat, job.entry, job.variant, self.launchers[slot])
            self.running[future] = (job, slot)

    def finish(self, future: Future, pending: deque[_Job]) -> None:
        job, slot = self.running.pop(future)
        attempts = future.result()  # run_repeat guards each run, so it does not raise
        failed_start = next((a for a in attempts if a.start_failed), None)
        if failed_start:
            # The slot is broken, not the scenario: the job goes back to the front for another slot.
            self.bad_slots[slot] = failed_start.reason or "the run did not start"
            pending.appendleft(job)
            return
        self.free.append(slot)
        self.free.sort()
        if not attempts:
            pending.appendleft(job)  # the budget or the cap ended it before a run: it counts as not run
            return
        if job.entry.optional and attempts[0].unknown_scenario:
            self.skipped[job.entry_index] = f"optional scenario {job.entry.scenario!r} does not exist yet. Skipped."
            return
        self.results.append((job, attempts))


def run_suite_parallel(
    suite: Suite,
    launchers: dict[int, RunOne],
    suite_id: str,
    max_seconds: float | None = None,
    clock: Callable[[], float] = time.monotonic,
    is_exclusive: Callable[[str], bool] = lambda scenario: False,
) -> SuiteOutcome:
    """Like run_suite, but with one launcher per game slot. A slot whose run does not start is not used again."""
    if not launchers:
        raise ValueError("run_suite_parallel needs at least one game slot.")
    budget_s = min(suite.time_budget_s, max_seconds) if max_seconds is not None else suite.time_budget_s
    state = _SuiteRun(suite, next(iter(launchers.values())), suite_id, budget_s, clock)
    pool = _Pool(state, launchers, is_exclusive)
    pending = deque(build_jobs(suite))
    with ThreadPoolExecutor(max_workers=len(launchers)) as executor:
        while True:
            pool.start_jobs(pending, executor)
            if not pool.running:
                break
            done, _ = wait(pool.running, return_when=FIRST_COMPLETED)
            for future in done:
                pool.finish(future, pending)
    stop_reason = state.stop_reason
    if pending and not stop_reason and not pool.free and not pool.running:
        stop_reason = STOP_NO_SLOTS
    elif pending and not stop_reason:
        state.budget_left()  # sets the time budget reason when that ended the loop
        stop_reason = state.stop_reason
    return _outcome(suite, suite_id, budget_s, clock() - state.started, stop_reason, pool)


def _outcome(suite: Suite, suite_id: str, budget_s: float, elapsed_s: float, stop_reason: str | None, pool: _Pool) -> SuiteOutcome:
    outcomes: list[EntryOutcome] = []
    not_run: list[str] = []
    for entry_index, entry in enumerate(suite.entries):
        outcome = EntryOutcome(entry, skipped_note=pool.skipped.get(entry_index))
        if not outcome.skipped_note:
            for job, attempts in sorted((r for r in pool.results if r[0].entry_index == entry_index), key=lambda r: r[0].order):
                outcome.repeats.append(attempts)
                outcome.variant_names.append(job.variant_name)
        if outcome.repeats or outcome.skipped_note:
            outcomes.append(outcome)
        else:
            not_run.append(entry.scenario)
    return SuiteOutcome(suite=suite, suite_id=suite_id, entries=outcomes, budget_s=budget_s, elapsed_s=elapsed_s,
                        stop_reason=stop_reason, not_run=not_run, bad_slots=dict(pool.bad_slots))
