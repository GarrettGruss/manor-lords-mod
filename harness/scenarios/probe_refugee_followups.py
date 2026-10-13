"""Probe for the open questions of issue #61 (spec 15, refugee waves).

Research tool. It records every answer in `probe.jsonl` and never fails on a game answer.
Choose a mode with HARNESS_PROBE:
  surge_long   settle_region once, then 20 game days: families, homeless, approval, food per day (item 1, and item 2 census)
  surge_sites  settle_region at the woods (forest_spot), then with supply 1, each with a census (item 2)
  eject_census census, eject, census, wait, accommodate, census; then a 1-squad settle letter with a census (items 3 and 4)
  eject_tent   family_eject home=tent on a game with a house and a tent (item 5; fixture burgage-start or --new-game)
  add_adult    family_add with an adult member, then 4 game days (item 6)
  bad_plots    burgage plots on bad ground, one try each (item 7)
"""

import json
import os

from runlib import plotgeom

NAME = "probe-refugee-followups"
LIMIT_S = 600
HIDDEN = True
LONG_REASON = "The probe watches up to 20 game days; one run answers several questions."
SURGE_DAYS = 20
CENSUS_DAYS = (1, 5, 10, 20)
TIMBER = 16
TIMBER_AMOUNT = 60
PLOT_COUNT = 3
WATCH_SPEED = 3


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

    def numbers(self, step: str) -> dict | None:
        """One row: the region numbers and the food read of the game."""
        def read():
            region = self.ctx.actions.housing_state()["region"]
            row = {key: region[key] for key in ("families", "homeless", "residents", "vacant", "living", "approval", "public_order", "tents_built")}
            row["stock"] = self.ctx.actions.sack_census()["census"]["stock"]
            row["food"] = self.food()
            return row
        return self.attempt(step, read)

    def food(self):
        bridge = self.ctx.actions._bridge  # noqa: SLF001 - one read the actions do not wrap
        try:
            return bridge.read_property(bridge.player_region_path(), "supplies_food")
        except Exception as error:  # noqa: BLE001
            return f"unreadable: {str(error)[:120]}"

    def census(self, step: str) -> dict | None:
        """Full family census plus a short summary: families with and without a home, homes that list a family."""
        def read():
            data = self.ctx.actions.family_census()
            listed = sorted(id_ for row in data["buildings"] for id_ in row["occupants"])
            homed = [row["index"] for row in data["families"] if row["has_home"]]
            data["summary"] = {"families": len(data["families"]), "with_familyHome": len(homed), "listed_ids": listed,
                               "members": sum(row["living"] for row in data["families"])}
            return data
        return self.attempt(step, read)


def watch(probe, label: str, days: int, census_days: tuple = ()) -> None:
    for day in range(1, days + 1):
        probe.ctx.time.run_game_days(1, speed=WATCH_SPEED)
        probe.numbers(f"{label} day {day}")
        if day in census_days:
            probe.census(f"{label} census day {day}")


def first_spot(probe) -> dict | None:
    spots = (probe.attempt("tent spots", probe.ctx.actions.tent_find_spot) or {}).get("spots") or []
    return spots[0] if spots else None


def player_region_row(probe) -> dict | None:
    name = probe.ctx.actions.housing_state()["region"]["name"]
    rows = [r for r in probe.ctx.actions.regions_state()["regions"] if r["name"] == name]
    probe.note("player region", name=name, row=rows[0] if rows else None)
    return rows[0] if rows else None


def settle_at(probe, row: dict, step: str, spot: dict, supply: int = 0) -> None:
    actions = probe.ctx.actions
    settlement_type = row.get("settlement_type") or 1
    probe.attempt(step, lambda: actions.settle_region(row["region"], 0, settlement_type, supply, spot["x"], spot["y"], spot.get("z", 0)))
    probe.numbers(f"{step} at once")
    probe.census(f"{step} census")


def surge_long(probe) -> None:
    row, spot = player_region_row(probe), first_spot(probe)
    if row is None or spot is None:
        probe.note("stop", reason="no region row or no spot")
        return
    probe.numbers("start")
    probe.census("start census")
    watch(probe, "baseline", 1)
    settle_at(probe, row, "settle", spot)
    watch(probe, "surge", SURGE_DAYS, CENSUS_DAYS)
    probe.ctx.screenshot("surge_long_end")


def surge_sites(probe) -> None:
    row = player_region_row(probe)
    if row is None:
        probe.note("stop", reason="no region row")
        return
    probe.numbers("start")
    probe.census("start census")
    woods = (probe.attempt("forest spots", probe.ctx.actions.forest_spot) or {}).get("spots") or []
    if woods:
        settle_at(probe, row, "settle woods", woods[0])
        watch(probe, "woods", 3, (3,))
    spot = first_spot(probe)
    if spot:
        settle_at(probe, row, "settle supply 1", spot, supply=1)
        watch(probe, "supply1", 3, (3,))


def eject_census(probe) -> None:
    actions = probe.ctx.actions
    probe.numbers("start")
    probe.census("start census")
    probe.attempt("eject 3", lambda: actions.family_eject(3, True))
    probe.numbers("eject at once")
    probe.census("eject census")
    watch(probe, "after eject", 2, (2,))
    probe.attempt("accommodate", actions.accommodate_homeless)
    probe.numbers("accommodate at once")
    probe.census("accommodate census")
    letter_one_squad(probe)


def letter_one_squad(probe) -> None:
    actions = probe.ctx.actions
    probe.attempt("bandit state before", actions.bandit_state)
    probe.attempt("spawn 1 raid squad", lambda: actions.spawn_raid(squads=1))
    probe.attempt("bandit state spawned", actions.bandit_state)
    probe.attempt("tag attacking", lambda: actions.bandit_tag("attacking"))
    probe.attempt("settle letter", lambda: actions.bandit_settle_offer(20))
    for day in range(1, 4):
        probe.ctx.time.run_game_days(1, speed=WATCH_SPEED)
        probe.numbers(f"letter day {day}")
        probe.attempt(f"bandit state letter day {day}", actions.bandit_state)
    probe.census("letter census")


def eject_tent(probe) -> None:
    actions = probe.ctx.actions
    probe.numbers("start")
    probe.attempt("housing before", actions.housing_state)
    probe.census("start census")
    probe.attempt("eject 1 into the tent", lambda: actions.family_eject(1, True, "tent"))
    probe.numbers("eject at once")
    probe.census("eject census")
    watch(probe, "after eject", 3, (3,))


def add_adult(probe) -> None:
    actions = probe.ctx.actions
    probe.numbers("start")
    probe.census("start census")
    probe.attempt("family_add adult", lambda: actions.family_add(1, adult=True))
    probe.numbers("add at once")
    probe.census("add census")
    watch(probe, "after add", 4, (4,))


def try_plots(probe, label: str, x: float, y: float, z: float, away: tuple) -> None:
    actions = probe.ctx.actions
    plots = plotgeom.make_plots(x, y, z, away[0], away[1], PLOT_COUNT)
    before = probe.numbers(f"{label} before")
    probe.attempt(f"{label} open tool", actions.open_burgage_tool)
    probe.attempt(f"{label} place", lambda: actions.plot_field_place(plots))
    probe.attempt(f"{label} commit", actions.commit_plots)
    watch(probe, label, 2)
    probe.note(f"{label} burgage", built=actions.burgage_count(True), all=actions.burgage_count(False),
               before=before and before.get("vacant"))


def bad_plots(probe) -> None:
    actions = probe.ctx.actions
    probe.attempt("give timber", lambda: actions.give_item(TIMBER, TIMBER_AMOUNT))
    housing = actions.housing_state()
    spots = first_spot(probe)
    woods = (probe.attempt("forest spots", actions.forest_spot) or {}).get("spots") or []
    if woods:
        try_plots(probe, "forest no road", woods[0]["x"], woods[0]["y"], woods[0]["z"], (0, 1))
    if spots:
        try_plots(probe, "high slope", spots["x"], spots["y"], spots["z"] + 4000, (0, 1))
    house = next((b for b in housing["residential"] if b.get("x") is not None), None)
    probe.note("overlap target", house=house)
    centre = (probe.attempt("tent spots again", actions.tent_find_spot) or {}).get("centre")
    if centre:
        try_plots(probe, "overlap centre", centre["x"], centre["y"], spots["z"] if spots else 0, (0, 1))


MODES = {"surge_long": surge_long, "surge_sites": surge_sites, "eject_census": eject_census, "eject_tent": eject_tent,
         "add_adult": add_adult, "bad_plots": bad_plots}


def run(ctx) -> dict:
    probe = Probe(ctx)
    mode = os.environ.get("HARNESS_PROBE", "surge_long")
    if mode not in MODES:
        raise ValueError(f"HARNESS_PROBE must be one of {sorted(MODES)}")
    probe.note("mode", mode=mode)
    MODES[mode](probe)
    return ctx.result()
