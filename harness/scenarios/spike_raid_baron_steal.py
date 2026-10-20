"""Spike (change add-raid-storage-tiers, task 1.1): battle marker, unit distance and goods removal.

A baron lord marches an army to a challenge. Each game day the scenario reads the battle marker (challenge Center and the battlefield
actor), the squad centers (realPos) and the distance of each squad to the marker. It also removes goods from one store with the
guarded action sack_goods (consumeGoodNoCheck) and checks that the stock falls by the amount. It saves nothing.
"""

import json
import math

NAME = "spike-raid-baron-steal"
DESCRIPTION = "Read battle marker and unit distance of a baron army, and remove goods from a store (spike, no assert on the AI)."
HIDDEN = True
LIMIT_S = 400
LONG_REASON = "The baron army needs about 20 game seconds to reach the marker, then the scenario watches 6 game days."
SPEED = 3
DAYS = 6
STEAL = 10


def note(ctx, step: str, **data) -> None:
    ctx.log.info(f"PROBE {json.dumps({'step': step, **data}, default=str)[:1500]}")


def store_total(ctx, store_id: int) -> int | None:
    for store in ctx.actions.sack_census()["stores"]:
        if store["id"] == store_id:
            return store["goods"]
    return None


def run(ctx) -> dict:
    actions, expect = ctx.actions, ctx.expect
    lord = actions.spawn_ai_lord("Spike Baron", can_build=False)["lord"]
    actions.lord_relations(lord)
    actions.lord_start_ai(lord, speed=1, can_build=False)
    actions.lord_declare_war(lord)
    actions.lord_spawn_army(lord, "spearMilitia", 1, 6000, 0)
    challenge = actions.lord_challenge(lord)["challenges"][-1]
    center, field = challenge["center"], challenge["battlefield_at"]
    note(ctx, "marker", center=center, battlefield_at=field)
    expect.equals("marker: challenge center equals battlefield actor place", center, field)

    stores = [s for s in actions.sack_census()["stores"] if s["goods"] >= DAYS * STEAL]
    store = max(stores, key=lambda s: s["goods"])
    good = next(iter(store["by_good"]))
    note(ctx, "store", id=store["id"], type=store["type"], goods=store["goods"], good=good)

    distances = []
    for day in range(1, DAYS + 1):
        before = store_total(ctx, store["id"])
        actions.sack_goods(good=int(good), amount=STEAL, store=store["id"])
        after = store_total(ctx, store["id"])
        expect.equals(f"day {day}: the store lost {STEAL}", before - after, STEAL)
        ctx.time.run_game_seconds(40, speed=SPEED)
        for row in actions.lords_state(log=0)["lords"]:
            if row["lord"] != lord:
                continue
            for squad in row["squads"]:
                if squad.get("x") is None:
                    continue
                distance = round(math.hypot(squad["x"] - center["x"], squad["y"] - center["y"]))
                distances.append(distance)
                note(ctx, "squad", day=day, squad=squad["id"], alive=squad["alive"], x=squad["x"], y=squad["y"], d_marker=distance)
    expect.equals("the squad distance to the marker was read", len(distances) > 0, True)
    ctx.metric("min_distance", min(distances) if distances else -1)
    ctx.metric("max_distance", max(distances) if distances else -1)
    ctx.ensure_alive("spike raid baron steal")
    return ctx.result()
