"""Probe for spec 15 part 7 (homeless refugees): eject housed families and add new families, and watch approval.

Research tool. It records every answer in `probe.jsonl` and never fails on a game answer.
Choose a mode with HARNESS_PROBE: eject_suppress, eject_free (then accommodate), eject_wait (suppress false, no accommodate), eject_tent, add.
"""

import json
import os

NAME = "probe-refugees"
LIMIT_S = 280
HIDDEN = True
OBSERVE_DAYS = 5
EJECT_COUNT = 3


class Probe:
    def __init__(self, ctx):
        self.ctx = ctx
        self.path = ctx.run_dir / "probe.jsonl"

    def note(self, step: str, **data) -> None:
        entry = {"step": step, **data}
        self.ctx.log.info(f"PROBE {json.dumps(entry, default=str)[:1200]}")
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, default=str) + "\n")

    def attempt(self, step: str, work):
        try:
            result = work()
        except Exception as error:  # noqa: BLE001 - the probe records every answer
            self.ctx.ensure_alive(step)
            self.note(step, error=str(error)[:500])
            return None
        self.note(step, result=result)
        return result


def watch_days(probe, label: str, days: int) -> None:
    for day in range(1, days + 1):
        probe.ctx.time.run_game_days(1, speed=3)
        state = probe.ctx.actions.family_state()
        probe.note(f"{label} day {day}", region=state.get("region"), housed=len(state.get("housed_ids", [])))


def run(ctx) -> dict:
    probe = Probe(ctx)
    mode = os.environ.get("HARNESS_PROBE", "eject_suppress")
    actions = ctx.actions
    probe.attempt("start", actions.family_state)
    watch_days(probe, "baseline", 2)
    if mode == "eject_tent":
        probe.attempt("housing before", actions.housing_state)
        probe.attempt("eject 1 into the tent", lambda: actions.family_eject(1, True, "tent"))
        probe.attempt("housing after", actions.housing_state)
    elif mode.startswith("eject"):
        suppress = mode == "eject_suppress"
        probe.attempt(f"eject {EJECT_COUNT} suppress={suppress}", lambda: actions.family_eject(EJECT_COUNT, suppress))
        probe.attempt("after eject", actions.family_state)
        if mode == "eject_free":
            probe.attempt("accommodate", actions.accommodate_homeless)
            probe.attempt("after accommodate", actions.family_state)
    elif mode == "add":
        probe.attempt("add 2 families", lambda: actions.family_add(2))
        probe.attempt("after add", actions.family_state)
    watch_days(probe, mode, OBSERVE_DAYS)
    probe.attempt("end census", actions.housing_state)
    return ctx.result()
