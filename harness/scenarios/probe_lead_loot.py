"""Probe for lead 1.1 (R3 real loot) of the change spike-community-mod-leads, issue #280.

Research tool, not in the regular suite. Run on the fixture manor-bailey (it has a built manor):
    uv run python harness\\run.py --scenario probe-lead-loot --fixture manor-bailey --slot auto
It spawns one bandit squad, reads GetEquippedID (slots 0..3) of its units, kills the squad, reads the gear again
and puts goods into the manor with manor_put (addToInventory). It never calls a save function.
"""

from runlib import battle
from runlib.leadprobe import Probe

NAME = "probe-lead-loot"
LIMIT_S = 300
HIDDEN = True
GOOD = 1
AMOUNT = 5


def numeric_slots(rows: list) -> tuple[int, int]:
    """(slots that gave a number, slots that gave anything else) over all units."""
    good = bad = 0
    for row in rows:
        gear = row["gear"]
        for entry in gear.values() if isinstance(gear, dict) else gear:
            if isinstance(entry, (int, float)):
                good += 1
            else:
                bad += 1
    return good, bad


def read_gear(probe: Probe, squad: int, label: str) -> None:
    gear = probe.attempt(f"gear {label}", lambda: probe.ctx.actions.lead_unit_gear(squad))
    if not gear:
        return
    good, bad = numeric_slots(gear["rows"])
    probe.metric(f"units_{label}", gear["units"])
    probe.metric(f"dead_{label}", gear["dead"])
    probe.metric(f"gear_numeric_{label}", good)
    probe.metric(f"gear_other_{label}", bad)


def move_goods(probe: Probe) -> None:
    actions = probe.ctx.actions
    before = probe.attempt("manor stock before", lambda: actions.manor_stock(GOOD))
    probe.attempt("manor_put", lambda: actions.manor_put(GOOD, AMOUNT))
    after = probe.attempt("manor stock after", lambda: actions.manor_stock(GOOD))
    probe.metric("manor_stock_before", before)
    probe.metric("manor_stock_after", after)
    if before is not None and after is not None:
        probe.metric("manor_stock_gain", after - before)


def run(ctx) -> dict:
    probe = Probe(ctx)
    spawned = probe.attempt("spawn bandits", lambda: ctx.actions.spawn_units("bandit", battle.SPEAR))
    if not spawned:
        return ctx.result()
    squad = spawned["answer"]["squads"][0]["id"]
    ctx.time.run_game_seconds(2, speed=1)
    read_gear(probe, squad, "alive")
    probe.attempt("kill", lambda: ctx.actions.bandit_kill_squads(squad))
    ctx.time.run_game_seconds(2, speed=1)
    read_gear(probe, squad, "dead")
    move_goods(probe)
    return ctx.result()
