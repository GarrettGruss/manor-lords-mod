"""Probe for spec 15 part 9 (immigration surge): call settleRegion on the player's own, already settled region.

Research tool. It records every answer in `probe.jsonl` and never fails on a game answer.
Reads the growth modifiers, calls settle_region at a free spot, then reads each game day.
HARNESS_SETTLE_CALLS (default 2) sets how many calls it makes, each at a new spot.
"""

import json
import os

NAME = "probe-immigration-surge"
LIMIT_S = 360
HIDDEN = True
LONG_REASON = "The probe watches several game days after each settle call."
SETTLE_CALLS = int(os.environ.get("HARNESS_SETTLE_CALLS", "2"))
WATCH_DAYS = 5


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

    def numbers(self, step: str, region_name: str | None) -> None:
        def read():
            family = self.ctx.actions.family_state()
            housing = self.ctx.actions.housing_state()
            rows = [r for r in self.ctx.actions.regions_state()["regions"] if r["name"] == region_name]
            return {"region": family["region"], "growth": family.get("growth"), "tents": housing["tents"],
                    "residential_total": housing["residential_total"], "row": rows[0] if rows else None}
        self.attempt(step, read)


def find_player_region(probe) -> dict | None:
    name = probe.ctx.actions.housing_state()["region"]["name"]
    rows = [r for r in probe.ctx.actions.regions_state()["regions"] if r["name"] == name]
    probe.note("player region", name=name, row=rows[0] if rows else None)
    return rows[0] if rows else None


def settle_once(probe, row: dict, index: int) -> None:
    actions = probe.ctx.actions
    spots = (probe.attempt(f"spots {index}", actions.tent_find_spot) or {}).get("spots") or []
    if len(spots) < index:
        probe.note("no spot", index=index)
        return
    spot = spots[index - 1]
    settlement_type = row.get("settlement_type") or 1
    probe.attempt(f"settle {index}", lambda: actions.settle_region(
        row["region"], 0, settlement_type, 0, spot["x"], spot["y"], spot["z"]))
    probe.numbers(f"settle {index} at once", row["name"])
    for day in range(1, WATCH_DAYS + 1):
        probe.ctx.time.run_game_days(1, speed=3)
        probe.numbers(f"settle {index} day {day}", row["name"])


def run(ctx) -> dict:
    probe = Probe(ctx)
    row = find_player_region(probe)
    if row is None:
        probe.note("stop", reason="player region not found")
        return ctx.result()
    probe.numbers("start", row["name"])
    probe.ctx.time.run_game_days(1, speed=3)
    probe.numbers("start day 1", row["name"])
    for index in range(1, SETTLE_CALLS + 1):
        settle_once(probe, row, index)
    ctx.screenshot("surge_end")
    return ctx.result()
