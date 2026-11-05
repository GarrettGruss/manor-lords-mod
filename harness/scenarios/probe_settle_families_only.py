"""Probe for change spike-settle-families-only: what does a settleRegion call (or another way) add to a new game?

Research tool. HARNESS_VARIANT: settle (HARNESS_SETTLE_TYPE, HARNESS_SUPPLY, HARNESS_SUPPLY_MULT), at_camp, grow, none.
Records census numbers before and after in probe.jsonl. Never fails on a game answer.
"""

import json
import os

NAME = "probe-settle-families-only"
LIMIT_S = 400
HIDDEN = True
LONG_REASON = "The probe watches game days after the call."
VARIANT = os.environ.get("HARNESS_VARIANT", "settle")
CLASSES = ["SMUnit", "SMBuildingMaster", "SMAnimal", "SMLivestock", "Ox", "Cattle"]


class Probe:
    def __init__(self, ctx):
        self.ctx = ctx
        self.path = ctx.run_dir / "probe.jsonl"

    def note(self, step, **data):
        entry = {"step": step, **data}
        self.ctx.log.info(f"PROBE {json.dumps(entry, default=str)[:1800]}")
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, default=str) + "\n")

    def attempt(self, step, work):
        try:
            result = work()
        except Exception as error:  # noqa: BLE001
            self.ctx.ensure_alive(step)
            self.note(step, error=str(error)[:500])
            return None
        self.note(step, result=result)
        return result

    def snap(self, label):
        ctx = self.ctx
        census = self.attempt(f"{label} sack_census", ctx.actions.sack_census) or {}
        stock = census.get("stock") or {}
        self.note(f"{label} summary", buildings=census.get("buildings"), stock_total=stock.get("total"), by_good=stock.get("by_good"),
                  people=census.get("people"))
        housing = self.attempt(f"{label} housing", ctx.actions.housing_state) or {}
        self.note(f"{label} tents", region=housing.get("region"), tents=housing.get("tents"), world_tents=housing.get("world_tents"))
        units = self.attempt(f"{label} units", ctx.actions.units_census) or {}
        self.note(f"{label} units summary", by_side=units.get("by_side"), by_role=units.get("by_role"), units=units.get("units"))
        counts = {}
        for name in CLASSES:
            try:
                counts[name] = ctx.bridge.count_objects(name)
            except Exception as error:  # noqa: BLE001
                counts[name] = str(error)[:60]
        self.note(f"{label} class counts", counts=counts)


def run(ctx) -> dict:
    probe = Probe(ctx)
    ctx.time.run_game_days(1, speed=3)
    probe.snap("start")
    region_path = probe.attempt("region path", ctx.bridge.player_region_path)
    if region_path:
        probe.attempt("region props", lambda: ctx.bridge._result("props", ref=region_path, pattern="ivestock|[Oo]x|nimal|omeless|upply|amil"))  # noqa: SLF001
        funcs = probe.attempt("region funcs", lambda: [f["name"] for f in ctx.bridge._result("funcs", ref=region_path) if f["owner"] == "Region"])  # noqa: SLF001
        probe.note("funcs count", n=len(funcs or []))
    ctx.screenshot("start")
    housing = ctx.actions.housing_state()
    name = housing["region"]["name"]
    row = [r for r in ctx.actions.regions_state()["regions"] if r["name"] == name][0]
    if VARIANT == "at_camp":
        tent = (housing.get("tents") or [None])[0]
        world = [t for t in housing.get("world_tents") or [] if t.get("id") == (tent or {}).get("id")]
        at = world[0] if world else None
        probe.note("existing camp", tent=tent, at=at)
        spots = (probe.attempt("spots", ctx.actions.tent_find_spot) or {}).get("spots") or []
        if at and spots:
            probe.attempt("settle at camp", lambda: ctx.actions.settle_region(
                row["region"], 0, row.get("settlement_type") or 1, 0, at["x"], at["y"], spots[0]["z"]))
    if VARIANT == "settle":
        mult = os.environ.get("HARNESS_SUPPLY_MULT")
        if mult is not None:
            probe.attempt("set mult", lambda: ctx.actions.game_setup_set_byte("startingSuppliesMultiplier", int(mult)))
            probe.attempt("read mult", lambda: ctx.actions.game_setup_state())
        spots = (probe.attempt("spots", ctx.actions.tent_find_spot) or {}).get("spots") or []
        spot = spots[0] if spots else None
        settle_type = int(os.environ.get("HARNESS_SETTLE_TYPE") or row.get("settlement_type") or 1)
        supply = int(os.environ.get("HARNESS_SUPPLY") or 0)
        probe.note("row", row=row, settle_type=settle_type, supply=supply)
        args = (row["region"], 0, settle_type, supply)
        if spot:
            args += (spot["x"], spot["y"], spot["z"])
        probe.attempt("settle", lambda: ctx.actions.settle_region(*args))
    if VARIANT == "grow" and region_path:
        for index in range(5):
            probe.attempt(f"growPopulation {index}", lambda: ctx.bridge.call_function(region_path, "growPopulation"))
            probe.note(f"families after grow {index}", row=ctx.actions.housing_state()["region"])
    probe.snap("after-call")
    ctx.time.run_game_days(2, speed=3)
    probe.snap("after-2-days")
    ctx.screenshot("after")
    return ctx.result()
