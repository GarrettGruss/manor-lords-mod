"""Probe for issue #68 (spec 17): can plots or buildings be placed inside the manor bailey?

Research tool. Use fixture manor-bailey. It records every answer in `probe.jsonl` and never fails on a game answer.
Modes (HARNESS_PROBE): plots (commit plots inside the ring, then a control outside).
"""

import json
import os

from runlib import plotgeom

NAME = "probe-bailey"
LIMIT_S = 900
HIDDEN = True
LONG_REASON = "The probe watches builders for several game days."
TIMBER = 16
TIMBER_AMOUNT = 80
PLOT_COUNT = 2
OUTSIDE_OFFSET = 9000
BUILD_DAYS = 20
MODE = os.environ.get("HARNESS_PROBE", "plots")


class Probe:
    def __init__(self, ctx):
        self.ctx = ctx
        self.path = ctx.run_dir / "probe.jsonl"

    def note(self, step: str, **data) -> None:
        entry = {"step": step, **data}
        self.ctx.log.info(f"PROBE {json.dumps(entry, default=str)[:1800]}")
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


def centre_of(walls: dict | None) -> tuple[float, float, float] | None:
    middles = [wall["middle"] for wall in (walls or {}).get("walls", []) if wall.get("middle")]
    if not middles:
        return None
    count = len(middles)
    return (sum(m["x"] for m in middles) / count, sum(m["y"] for m in middles) / count, sum(m.get("z", 0) for m in middles) / count)


def place_row(probe, label: str, x: float, y: float, z: float) -> None:
    actions = probe.ctx.actions
    before = actions.burgage_count(False)
    plots = plotgeom.make_plots(x, y, z, 1, 0, PLOT_COUNT)
    probe.attempt(f"{label} open tool", actions.open_burgage_tool)
    probe.attempt(f"{label} place", lambda: actions.plot_field_place(plots))
    probe.attempt(f"{label} commit", actions.commit_plots)
    probe.ctx.time.run_game_seconds(2, speed=1)
    probe.note(f"{label} counts", before=before, after=actions.burgage_count(False))


def watch(probe, label: str) -> None:
    for day in range(1, BUILD_DAYS + 1):
        probe.ctx.time.run_game_days(1, speed=3)
        probe.attempt(f"{label} day {day}", lambda: {"all": probe.ctx.actions.burgage_count(False),
                                                      "built": probe.ctx.actions.burgage_count(True)})


def run(ctx) -> dict:
    probe = Probe(ctx)
    actions = ctx.actions
    probe.attempt("manor_state", actions.manor_state)
    walls = probe.attempt("wall_state", actions.wall_state)
    centre = centre_of(walls)
    probe.note("centre", centre=centre)
    probe.attempt("spots", actions.tent_find_spot)
    probe.attempt("give timber", lambda: actions.give_item(TIMBER, TIMBER_AMOUNT))
    for food in (171, 172, 230, 296):
        probe.attempt(f"give food {food}", lambda food=food: actions.give_item(food, 50))
    ctx.screenshot("start")
    if centre and MODE == "plots":
        place_row(probe, "inside", *centre)
        ctx.screenshot("inside_placed")
        place_row(probe, "outside", centre[0] + OUTSIDE_OFFSET, centre[1], centre[2])
        probe.attempt("sites", lambda: actions.building_sites(3))
        watch(probe, "build")
        ctx.screenshot("end")
    return ctx.result()
