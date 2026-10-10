"""Phase runner. Each phase runs in a worker thread with a time limit."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable

from .runfolder import RunFolder
from .summary import PhaseResult, Summary, decide_verdict, write_summary


class PhaseFailed(Exception):
    """A phase ran and found a real failure (not a bug in the harness)."""


@dataclass
class Phase:
    name: str
    fn: Callable[["PhaseContext"], str | None]  # may return a detail string
    time_limit_s: float
    always_run: bool = False  # collect and teardown run even after a failure


def _new_state() -> dict:
    return {
        "boot": None,
        "scenario_result": None,
        "crash": None,
        "artifacts": {},
        "game_stop_requested": False,
    }


@dataclass
class PhaseContext:
    run: RunFolder
    config: dict
    state: dict = field(default_factory=_new_state)


def _run_with_limit(phase: Phase, ctx: PhaseContext) -> PhaseResult:
    outcome: dict = {}

    def work() -> None:
        try:
            outcome["detail"] = phase.fn(ctx)
            outcome["status"] = "ok"
        except PhaseFailed as failure:
            outcome.update(status="failed", detail=str(failure))
        except BaseException as error:  # noqa: BLE001 - every error must become a result
            outcome.update(status="error", detail=f"{type(error).__name__}: {error}")

    # A daemon thread cannot block the exit of the launcher.
    worker = threading.Thread(target=work, name=f"phase-{phase.name}", daemon=True)
    started = time.monotonic()
    worker.start()
    worker.join(phase.time_limit_s)
    seconds = round(time.monotonic() - started, 2)
    if worker.is_alive():
        # Python cannot kill a thread. The abandoned thread keeps running until its function returns.
        return PhaseResult(phase.name, "timeout", seconds, f"exceeded the time limit of {phase.time_limit_s} s")
    return PhaseResult(phase.name, outcome["status"], seconds, outcome.get("detail"))


def run_phases(phases: list[Phase], ctx: PhaseContext, results: list[PhaseResult] | None = None) -> list[PhaseResult]:
    """Run phases in order. After a failure, skip the rest except always_run phases.

    Results are appended to `results` as they happen, so a caller keeps them
    even if this function raises. A KeyboardInterrupt does not skip the always_run
    phases, because teardown must still stop the game. It is raised again at the end.
    """
    results = results if results is not None else []
    stopped = False
    interrupt: KeyboardInterrupt | None = None
    for phase in phases:
        if stopped and not phase.always_run:
            results.append(PhaseResult(phase.name, "skipped", 0.0, "an earlier phase did not succeed"))
            continue
        try:
            result = _run_with_limit(phase, ctx)
        except KeyboardInterrupt as error:
            interrupt = error
            result = PhaseResult(phase.name, "error", 0.0, "KeyboardInterrupt")
        results.append(result)
        if result.status != "ok":
            stopped = True
    if interrupt:
        raise interrupt
    return results


def _build_notes(config: dict, phases: list[PhaseResult], state: dict) -> list[str]:
    notes = list(config.get("start_notes", []))
    notes += [f"phase {phase.name} was skipped" for phase in phases if phase.status == "skipped"]
    if state["boot"] is None:
        notes.append("no boot result")
    if state["scenario_result"] is None:
        notes.append("no scenario result")
    if not state["artifacts"]:
        notes.append("no artifacts were recorded")
    return notes


def _build_summary(run: RunFolder, config: dict, results: list[PhaseResult], state: dict, started: datetime) -> Summary:
    verdict, reason = decide_verdict(results, state)
    duration = (datetime.now(timezone.utc) - started).total_seconds()
    return Summary(
        run_id=run.run_id,
        verdict=verdict,
        reason=reason,
        scenario=config.get("scenario"),
        started=started.strftime("%Y-%m-%dT%H:%M:%SZ"),
        duration_s=round(duration, 1),
        phases=results,
        boot=state["boot"],
        scenario_result=state["scenario_result"],
        crash=state["crash"],
        artifacts=state["artifacts"],
        environment=config.get("environment", {}),
        notes=_build_notes(config, results, state),
    )


def execute_run(run: RunFolder, config: dict, phases: list[Phase]) -> Summary:
    """Run all phases and write summary.json. The summary is written even if this raises.

    The caller holds the run lock and has bumped the iteration counter.
    """
    started = datetime.now(timezone.utc)
    ctx = PhaseContext(run=run, config=config)
    results: list[PhaseResult] = []
    try:
        run_phases(phases, ctx, results)
    except KeyboardInterrupt:
        raise  # run_phases already recorded it
    except BaseException as error:
        results.append(PhaseResult("runner", "error", 0.0, f"{type(error).__name__}: {error}"))
        raise
    finally:
        summary = _build_summary(run, config, results, ctx.state, started)
        write_summary(run.summary_path, summary)
    return summary
