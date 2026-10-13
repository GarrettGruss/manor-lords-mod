"""Probe for spec 18: can Lua add or remove a part of a built building master? Research tool, not a test.

Choose the building with HARNESS_PROBE_C: `plot` (a burgage plot, fixture burgage-start) or `tent` (settle_region, then a tent, fixture base).
Start the game with HARNESS_ALLOW_UNSAFE=1. Every answer goes to `probe.jsonl`. The probe never calls a save function.
"""

import json
import os

NAME = "probe-composite"
LIMIT_S = 240
HIDDEN = True
LONG_REASON = "The probe watches the master for a few game days after each part change."
WATCH_DAYS = 2
LIST_ROWS = 40


class Probe:
    def __init__(self, ctx):
        self.ctx = ctx
        self.path = ctx.run_dir / "probe.jsonl"

    def note(self, step: str, **data) -> None:
        entry = {"step": step, **data}
        self.ctx.log.info(f"PROBE {json.dumps(entry, default=str)[:1500]}")
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


def settle_a_tent(probe) -> None:
    actions = probe.ctx.actions
    state = actions.housing_state()
    name = state["region"]["name"]
    row = [r for r in actions.regions_state()["regions"] if r["name"] == name][0]
    spot = actions.tent_find_spot()["spots"][0]
    probe.attempt("settle", lambda: actions.settle_region(row["region"], 0, row.get("settlement_type") or 1, 0,
                                                          spot["x"], spot["y"], spot["z"]))
    probe.ctx.time.run_game_days(1, speed=3)
    probe.note("tents", tents=actions.housing_state()["tents"])


def watch(probe, label: str, kind: int) -> None:
    for day in range(1, WATCH_DAYS + 1):
        probe.ctx.time.run_game_days(1, speed=3)
        probe.attempt(f"{label} day {day}", lambda: probe.ctx.actions.master_parts(type_id=kind, limit=0))


def run(ctx) -> dict:
    probe = Probe(ctx)
    actions = ctx.actions
    which = os.environ.get("HARNESS_PROBE_C", "plot")
    kind = 87 if which == "tent" else 3
    if which == "tent":
        settle_a_tent(probe)
    first = probe.attempt("1 parts", lambda: actions.master_parts(type_id=kind, limit=LIST_ROWS))
    if not first or not first.get("ok"):
        return ctx.result()
    building = first["building"]
    ctx.screenshot("start")
    probe.attempt("2 add copy of part 1", lambda: actions.master_part_add(building, 1, dx=400))
    probe.attempt("3 parts after add", lambda: actions.master_parts(building=building, limit=0))
    ctx.screenshot("after_add")
    probe.attempt("4 hide part 2", lambda: actions.master_part_remove(building, 2, "hide"))
    probe.attempt("5 unlink part 3", lambda: actions.master_part_remove(building, 3, "unlink"))
    probe.attempt("6 destroy part 4", lambda: actions.master_part_remove(building, 4, "destroy"))
    probe.attempt("7 parts after remove", lambda: actions.master_parts(building=building, limit=8))
    ctx.screenshot("after_remove")
    watch(probe, "8 watch", kind)
    probe.attempt("9 parts at end", lambda: actions.master_parts(building=building, limit=8))
    ctx.screenshot("end")
    return ctx.result()
