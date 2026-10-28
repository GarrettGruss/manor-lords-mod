"""Change update-banditry-rebellion-raid, tasks 2.8 to 2.10: loot overrides and the Outlaws pawn over a save and a load.

Two runs make one round trip (a run cannot load a save by itself), as in `mod-state-roundtrip`:
  1. write (default): start a rebellion, wait a few game seconds, save with the guarded `save_game(keep=True)`. The result holds the slot.
     uv run python harness/run.py --scenario bandits-rebellion-loot-roundtrip --fixture playtest-noai --slot 1 --max-runs 1000
  2. read: load the kept slot and check the entries, the pawn and the units.
     uv run python harness/run.py --scenario bandits-rebellion-loot-roundtrip --save <SaveGames>/<slot>.sav --env LOOT_PHASE=read --slot 1 --max-runs 1000
Fixture `playtest-noai` has no bandit camp: it also tests that the Outlaws pawn survives the load (2.10).
The kept slot stays in the user's save folder: remove it with harness/tools/fixtures.py uninstall after the check.
The write run records the entries in its notes; the read run compares them with the linked entries (2.8: stable key by squad and unit index).
"""

NAME = "bandits-rebellion-loot-roundtrip"
DESCRIPTION = "Rebellion loot overrides and the Outlaws pawn over a harness save and a load (write run, read run)."
LIMIT_S = 400
LONG_REASON = "Boot, cleanup of the camp, a rebellion and a save, or a load and checks."
SPEED = 3
EXPECT_FILE = "roundtrip_expect.json"


def state(ctx) -> dict:
    return ctx.mod.command("InvasionMod.bandits_state")


def overrides(ctx) -> dict:
    return ctx.mod.command("InvasionMod.raid_behavior_override_state")


def warm_up(ctx) -> None:
    for attempt in range(4):
        try:
            ctx.time.run_game_seconds(2, speed=SPEED)
            return
        except Exception as error:  # the clock holds for a while after a load
            ctx.log.info(f"warm-up {attempt} failed: {error}")
            ctx.popups()
    raise RuntimeError("the game clock did not start")


def write_phase(ctx) -> dict:
    warm_up(ctx)
    ctx.run_until(lambda: state(ctx)["outlaws"]["ready"] or state(ctx)["bandit_pawn"], 90, what="the Outlaws pawn")
    for _ in range(12):  # the camp cleanup needs game time
        if not state(ctx)["outlaws"]["camp_cleanup"]:
            break
        ctx.time.run_game_seconds(20, speed=SPEED)
    ctx.check("the Outlaws pawn exists before the save", state(ctx)["bandit_pawn"] is True, state(ctx)["outlaws"])
    homes = ctx.mod.command("InvasionMod.bandits_homes")
    if homes["valid"] < 4:
        ctx.mod.command("InvasionMod.bandits_stock_homes", good=133, amount=2, homes=homes["families"])
        ctx.mod.command("InvasionMod.bandits_stock_homes", good=271, amount=1, homes=homes["families"])
    count = min(6, state(ctx)["families"] - 1)
    ctx.mod.command("InvasionMod.bandits_leave_now", count=count)
    leave = state(ctx)["last_leave"]
    ctx.check("the rebellion spawned a squad", leave["spawned"] is True and leave["bandit_units"] == 18, leave)
    ctx.time.run_game_seconds(20, speed=SPEED)  # the squad is alive and raids; no entry is dropped yet
    before = overrides(ctx)
    ctx.check("entries exist before the save", before["count"] >= 1, before["count"])
    ctx.notes.append("ENTRIES " + repr([(e["squad"], e["index"], e["goods"]) for e in before["entries"]]))
    ctx.metric("entries_saved", before["count"])
    ctx.metric("pawn_before_save", 1)
    record = ctx.actions.save_game("rebellion loot roundtrip", keep=True)
    ctx.log.info(f"ROUNDTRIP saved slot {record['slot']}")
    result = ctx.result()
    result["slot"] = record["slot"]
    result["entries"] = [(e["squad"], e["index"], e["goods"]) for e in before["entries"]]
    (ctx.run_dir / EXPECT_FILE).write_text(repr(result["entries"]), encoding="utf-8")
    return result


def read_phase(ctx) -> dict:
    warm_up(ctx)
    ctx.run_until(lambda: state(ctx)["outlaws"]["ready"] or state(ctx)["bandit_pawn"], 90, what="the Outlaws pawn after the load")
    ctx.run_until(lambda: overrides(ctx)["relinking"] is False, 60, what="the relink to end")
    after = overrides(ctx)
    s = state(ctx)
    ctx.metric("entries_after_load", after["count"])
    ctx.metric("units_alive_after_load", after["units_alive"])
    ctx.metric("units_dead_after_load", after["units_dead"])
    ctx.metric("pawn_survived_or_made", 1 if s["bandit_pawn"] else 0)
    ctx.notes.append("ENTRIES AFTER " + repr([(e["squad"], e["index"], e["goods"], e["linked"]) for e in after["entries"]]))
    ctx.notes.append(f"outlaws after load: {s['outlaws']}")
    ctx.check("the Outlaws pawn exists after the load", s["bandit_pawn"] is True, s["outlaws"])
    ctx.check("entries came back from the save", after["count"] >= 1, after["count"])
    linked = sum(1 for e in after["entries"] if e["linked"])
    ctx.check("every entry is linked to a unit", linked == after["count"], [linked, after["count"]])
    ctx.check("the linked units exist", after["units_missing"] == 0 and after["units_alive"] + after["units_dead"] == after["count"], after)
    killed = ctx.mod.command("InvasionMod.raid_behavior_test_kill_override_units", count=1)
    ctx.check("a linked unit can be killed", killed["killed"] == 1, killed)
    ctx.run_until(lambda: any(e.get("dead_day") is not None for e in overrides(ctx)["entries"]), 30, what="the dead entry marked")
    ctx.check("its entry is marked dead and kept for the pit", any(e.get("dead_day") is not None for e in overrides(ctx)["entries"]), overrides(ctx)["entries"])
    return ctx.result()


def run(ctx) -> dict:
    phase = ctx.variant_option("LOOT_PHASE", "write")
    if phase not in ("write", "read"):
        return ctx.fail("phase", f"LOOT_PHASE must be write or read, got {phase}")
    return write_phase(ctx) if phase == "write" else read_phase(ctx)
