"""Probe for spec 15 part 8 (refugee cycle): eject, immigrate by the settle letter, accommodate, build 5 burgage plots without the mouse.

Research tool. It records every answer in `probe.jsonl` and never fails on a game answer.
Each step writes numbers per game day: families, homeless, vacant slots, approval, burgage count.
"""

import json
import os

from runlib import plotgeom

NAME = "probe-refugee-cycle"
LIMIT_S = 480
HIDDEN = True
LONG_REASON = "The probe watches about 25 game days and a plot build; one run answers many questions."
EJECT_COUNT = 5
RAID_SQUADS = int(os.environ.get("HARNESS_RAID_SQUADS", "5"))
SETTLE_SILVER = 20
TIMBER = 16
TIMBER_AMOUNT = 30
PLOT_COUNT = 5
NATURAL_DAYS = 3
SETTLE_DAYS = 3
BUILD_DAYS = 14


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

    def numbers(self, step: str) -> dict | None:
        """One row of the numbers the user asked for."""
        def read():
            region = self.ctx.actions.housing_state()["region"]
            return {"families": region["families"], "homeless": region["homeless"], "residents": region["residents"],
                    "vacant": region["vacant"], "living": region["living"], "approval": region["approval"],
                    "burgage_built": self.ctx.actions.burgage_count(True), "burgage_all": self.ctx.actions.burgage_count(False),
                    "tents": region["tents_built"]}
        row = self.attempt(step, read)
        return row


def watch(probe, label: str, days: int) -> None:
    for day in range(1, days + 1):
        probe.ctx.time.run_game_days(1, speed=3)
        probe.numbers(f"{label} day {day}")


def settle_path(probe) -> None:
    actions = probe.ctx.actions
    probe.attempt("bandit state before", actions.bandit_state)
    probe.attempt("spawn raid", lambda: actions.spawn_raid(squads=RAID_SQUADS))
    probe.attempt("tag attacking", lambda: actions.bandit_tag("attacking"))
    probe.attempt("settle letter", lambda: actions.bandit_settle_offer(SETTLE_SILVER))
    watch(probe, "settle", SETTLE_DAYS)
    probe.attempt("bandit state after", actions.bandit_state)


def place_row(probe) -> None:
    actions = probe.ctx.actions
    spots = probe.attempt("find spot", actions.tent_find_spot)
    if not spots or not spots.get("spots"):
        probe.note("no spot")
        return
    spot, centre = spots["spots"][0], spots["centre"]
    away = (spot["x"] - centre["x"], spot["y"] - centre["y"])
    plots = plotgeom.make_plots(spot["x"], spot["y"], spot["z"], away[0], away[1], PLOT_COUNT)
    probe.note("plots", spot=spot, centre=centre, away=away, first=plots[0])
    probe.attempt("open burgage tool", actions.open_burgage_tool)
    probe.attempt("place plots", lambda: actions.plot_field_place(plots))
    probe.attempt("commit", actions.commit_plots)


def run(ctx) -> dict:
    probe = Probe(ctx)
    actions = ctx.actions
    probe.numbers("1 start")
    watch(probe, "1 baseline", 1)
    probe.attempt("2 eject", lambda: actions.family_eject(EJECT_COUNT, True))
    probe.numbers("2 after eject")
    watch(probe, "3 natural", NATURAL_DAYS)
    settle_path(probe)
    probe.numbers("3 after settle")
    probe.attempt("4 accommodate", actions.accommodate_homeless)
    probe.numbers("4 after accommodate")
    watch(probe, "4 watch", 1)
    state = probe.numbers("5 prep")
    if state and state["homeless"] < EJECT_COUNT:
        probe.attempt("5 eject again", lambda: actions.family_eject(EJECT_COUNT, True))
        probe.numbers("5 after second eject")
    probe.attempt("give timber", lambda: actions.give_item(TIMBER, TIMBER_AMOUNT))
    place_row(probe)
    probe.numbers("5 after commit")
    ctx.screenshot("plots_placed")
    watch(probe, "5 build", BUILD_DAYS)
    ctx.screenshot("plots_end")
    return ctx.result()
