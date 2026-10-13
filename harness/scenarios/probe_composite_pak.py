"""Probe for spec 18, steps 3 and 4: does a pak change the part list of a composite building (the tent)? Research tool, not a test.

Run with a pak that adds buildingStats rows cloned from the tent (123, 124) or that points row 87 at another BM_* class:
  run.py --scenario probe-composite-pak --fixture base --pak comp123
The probe reads the rows, makes a tent with settle_region (mouse-free) and lists its parts. It uses no unsafe command and no save function.
"""

import json

NAME = "probe-composite-pak"
LIMIT_S = 240
HIDDEN = True
LONG_REASON = "The probe settles a region and waits one game day."
STAT_TYPES = (87, 123, 124)
NEW_TYPES = (123, 124)
PART_ROWS = 40


def note(ctx, step: str, **data) -> None:
    entry = {"step": step, **data}
    ctx.log.info(f"PROBE {json.dumps(entry, default=str)[:1500]}")
    with (ctx.run_dir / "probe.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, default=str) + "\n")


def attempt(ctx, step: str, work):
    try:
        result = work()
    except Exception as error:  # noqa: BLE001 - the probe records every answer
        ctx.ensure_alive(step)
        note(ctx, step, error=str(error)[:500])
        return None
    note(ctx, step, result=result)
    return result


def settle_a_tent(ctx) -> None:
    actions = ctx.actions
    name = actions.housing_state()["region"]["name"]
    row = [r for r in actions.regions_state()["regions"] if r["name"] == name][0]
    spot = actions.tent_find_spot()["spots"][0]
    attempt(ctx, "settle", lambda: actions.settle_region(row["region"], 0, row.get("settlement_type") or 1, 0,
                                                         spot["x"], spot["y"], spot["z"]))
    ctx.time.run_game_days(1, speed=3)


def run(ctx) -> dict:
    actions = ctx.actions
    for type_id in STAT_TYPES:
        attempt(ctx, f"stat {type_id}", lambda t=type_id: actions.building_stat(t))
    settle_a_tent(ctx)
    attempt(ctx, "housing", actions.housing_state)
    attempt(ctx, "parts of type 87", lambda: actions.master_parts(type_id=87, limit=PART_ROWS))
    for type_id in NEW_TYPES:
        attempt(ctx, f"parts of type {type_id}", lambda t=type_id: actions.master_parts(type_id=t, limit=PART_ROWS))
    ctx.screenshot("tent")
    return ctx.result()
