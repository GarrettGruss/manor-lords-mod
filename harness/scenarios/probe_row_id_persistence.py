"""Spike #284 (tasks 1.1 and 1.2): do buildings with new buildingStats ids and a new DT_Upgrades row survive a harness save and a load?

Needs the pak `rowid` (rows 126, 486, 1000, 2000, 32767, 65536 cloned from the hitching post; upgrades 117: 486 -> 126, 118: 2000 -> 1000).
It uses the real OS mouse (place_building), so it is hidden and exclusive. Two runs make one round trip:
  1. phase write (default): place and build the new ids, use upgrade 117 on a building of id 486, save with save_game(keep=True).
     uv run python harness/run.py --scenario probe-row-id-persistence --pak rowid --slot 2
  2. phase read: load the kept slot and count the buildings of each id again.
     uv run python harness/run.py --scenario probe-row-id-persistence --pak rowid --slot 2 --save <SaveGames>/<slot>.sav --env ROWID_PHASE=read
The kept slot stays in the user's save folder. Delete it after the check (the harness does not).
"""

import json

NAME = "probe-row-id-persistence"
LIMIT_S = 1200
LONG_REASON = "Places four buildings with the real mouse, builds them and runs an upgrade (up to 60 game days at speed 3)."
HIDDEN = True
EXCLUSIVE = True
PLACED_IDS = [65536, 32767, 126, 486]
UPGRADE = 117
UPGRADE_INTO = 126
SPEED = 3
MAX_DAYS = 20
SPOTS = [(0.35, 0.3), (0.3, 0.35), (0.3, 0.25), (0.45, 0.3), (0.4, 0.4), (0.25, 0.3), (0.35, 0.4), (0.45, 0.4)]


def note(ctx, step: str, **data) -> None:
    entry = {"step": step, **data}
    ctx.log.info(f"PROBE {json.dumps(entry, default=str)[:1500]}")
    with (ctx.run_dir / "probe.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, default=str) + "\n")


def counts(ctx, type_id: int) -> dict:
    return ctx.actions.building_sites(type_id)["counts"]


def place_one(ctx, type_id: int, spots: list) -> None:
    for fx, fy in list(spots):
        spots.remove((fx, fy))
        record = ctx.actions.place_building(type_id, fx, fy)  # a blocked spot places nothing and the record is not ok
        note(ctx, "place", type=type_id, fx=fx, fy=fy, ok=record.get("ok"))
        if record.get("ok"):
            return
    raise RuntimeError(f"no free spot for type {type_id}")


def wait_built(ctx, type_id: int) -> bool:
    for _ in range(MAX_DAYS):
        ctx.popups()
        if counts(ctx, type_id)["built"] >= 1:
            return True
        ctx.time.run_game_days(1, speed=SPEED)
    return counts(ctx, type_id)["built"] >= 1


def write_phase(ctx) -> dict:
    spots = list(SPOTS)
    for type_id in PLACED_IDS:
        place_one(ctx, type_id, spots)
    ctx.screenshot("placed")
    for type_id in PLACED_IDS:
        ctx.check(f"1.1 type {type_id} is built", wait_built(ctx, type_id), counts(ctx, type_id))
    note(ctx, "stat 486", stat=ctx.actions.building_stat(486))
    before = counts(ctx, UPGRADE_INTO)
    note(ctx, "before upgrade", into=before, source=counts(ctx, 486))
    note(ctx, "upgrade row", row=ctx.actions._command("upgrade_stat", type=UPGRADE), vanilla_2=ctx.actions._command("upgrade_stat", type=2))
    for good in ("planks", "timber", "stone", "clay"):  # the clone of upgrade 2 may ask goods: give stock so cost is no blocker
        try:
            ctx.actions.give_item(good, 100)
        except Exception as error:
            note(ctx, "give failed", good=good, error=str(error)[:150])
    request = ctx.actions.plot_upgrade(UPGRADE, type_id=486)
    note(ctx, "upgrade request", result=request)
    ctx.check("1.2 the upgrade request of the new row was accepted", request.get("ok", True) is not False, request)
    for _ in range(MAX_DAYS):
        ctx.popups()
        ctx.time.run_game_days(1, speed=SPEED)
        note(ctx, "upgrade day", source=ctx.actions.building_sites(486), into=counts(ctx, UPGRADE_INTO))
        if counts(ctx, 486)["built"] == 0 or counts(ctx, UPGRADE_INTO)["built"] > before["built"]:
            break
    after_into, after_source = counts(ctx, UPGRADE_INTO), counts(ctx, 486)
    note(ctx, "after upgrade", into=after_into, source=after_source,
         sites=ctx.actions.building_sites()["buildings"])
    ctx.check("1.2 the upgrade changed the building into the new type", after_into["built"] > before["built"] and after_source["built"] == 0,
              {"into": after_into, "source": after_source})
    ctx.screenshot("upgraded")
    snapshot = {str(t): counts(ctx, t) for t in PLACED_IDS}
    note(ctx, "before save", counts=snapshot)
    record = ctx.actions.save_game("rowid persistence", keep=True)
    ctx.log.info(f"ROWID saved slot {record['slot']}")
    result = ctx.result()
    result["slot"] = record["slot"]
    return result


def read_phase(ctx) -> dict:
    snapshot = {str(t): counts(ctx, t) for t in PLACED_IDS}
    note(ctx, "after load", counts=snapshot, sites=ctx.actions.building_sites()["buildings"])
    ctx.check("1.1 type 32767 is built after the load", snapshot["32767"]["built"] >= 1, snapshot["32767"])
    ctx.check("1.1 type 65536 is built after the load", snapshot["65536"]["built"] >= 1, snapshot["65536"])
    ctx.check("1.1 type 126 is built after the load", snapshot["126"]["built"] >= 1, snapshot["126"])
    ctx.check("1.1 type 486 is still there after the load (upgrade pending or done)", snapshot["486"]["built"] + snapshot["126"]["built"] >= 2, snapshot)
    note(ctx, "stat 126", stat=ctx.actions.building_stat(126))
    ctx.screenshot("loaded")
    note(ctx, "upgrade source after load", source=ctx.actions.building_sites(486))
    ctx.actions.give_item("planks", 100)
    ctx.actions.give_item("timber", 100)
    for _ in range(MAX_DAYS + 20):  # 1.2: does the pending upgrade of the new row finish? (a result, not a pass condition)
        ctx.popups()
        ctx.time.run_game_days(1, speed=SPEED)
        source, into = ctx.actions.building_sites(486), counts(ctx, UPGRADE_INTO)
        note(ctx, "watch upgrade", source=source["buildings"], into=into)
        if into["built"] >= 2 or not source["buildings"]:
            break
    ctx.metric("type_126_built_end", counts(ctx, UPGRADE_INTO)["built"])
    ctx.metric("type_486_built_end", counts(ctx, 486)["built"])
    ctx.ensure_alive("watch upgrade")
    ctx.screenshot("upgrade_end")
    return ctx.result()


def run(ctx) -> dict:
    phase = ctx.variant_option("ROWID_PHASE", "write")
    if phase not in ("write", "read"):
        return ctx.fail("phase", f"ROWID_PHASE must be write or read, got {phase}")
    return write_phase(ctx) if phase == "write" else read_phase(ctx)
