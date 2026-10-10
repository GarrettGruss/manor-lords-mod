"""Helpers for the suitelib tests: a fake run_one and summary builders."""

import runlib_path  # noqa: F401
from suitelib.runresult import RunResult
from suitelib.suitefile import Suite, SuiteEntry


def make_suite(entries, budget=1000.0, retries=1, name="t"):
    return Suite(name=name, entries=list(entries), time_budget_s=budget, flake_retries=retries)


def entry(scenario, repeat=1, optional=False, fixture=None):
    return SuiteEntry(scenario, repeat, fixture, optional)


def result(run_id, verdict="pass", duration=10.0, metrics=None, failed=None, **extra):
    return RunResult(run_id, verdict, duration, metrics=metrics or {}, failed_asserts=failed or [], **extra)


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


class FakeRunOne:
    """Plays a script per scenario. The last item repeats.

    An item is a verdict string, a RunResult or an exception to raise.
    Each call moves the fake clock by cost_s.
    """

    def __init__(self, script, clock=None, cost_s=0.0):
        self.script = {name: list(items) for name, items in script.items()}
        self.calls = []
        self.clock = clock
        self.cost_s = cost_s

    def __call__(self, scenario, run_id, fixture):
        self.calls.append((scenario, run_id, fixture))
        if self.clock:
            self.clock.now += self.cost_s
        items = self.script.get(scenario, ["pass"])
        item = items.pop(0) if len(items) > 1 else items[0]
        if isinstance(item, Exception):
            raise item
        if isinstance(item, RunResult):
            return item
        return result(run_id, item)


def summary(verdict="pass", scenario="smoke", duration=60.0, asserts=None, started="2026-01-01T00:00:00Z"):
    return {
        "run_id": "x",
        "verdict": verdict,
        "reason": None if verdict == "pass" else "bad",
        "scenario": scenario,
        "started": started,
        "duration_s": duration,
        "phases": [],
        "scenario_result": {"asserts": asserts if asserts is not None else []},
    }
