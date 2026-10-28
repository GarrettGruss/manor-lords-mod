"""Change update-banditry-rebellion-raid: low order ends in an armed rebellion and an Outlaws raid.

Run it on the fixture `playtest-noai` (AI opponents 0, five housed families, no Outlaws pawn at the start, unarmed homes):
  uv run python harness/run.py --scenario bandits-rebellion-raid --fixture playtest-noai --max-runs 1000
Steps:
  1. The Outlaws init made the pawn at the start (no camp units left).
  2. Unarmed village: the timer expires and the rebellion is blocked (`rebellion_blocked`), nothing is removed.
  3. Homes get weapons (also with too few armed homes the rebellion stays blocked). A new tick retries.
  4. The rebellion: the families leave (the village keeps 1), their goods are taken from their homes only, one squad of 18
     Brigands spawns near a removed home, and the goods become loot overrides.
  5. The native AI raids: a building burns and "enough looted" shows within 400 game seconds. The game runs 10 more game days.
It saves nothing. The fixture has 5 families, so 4 leave (the village keeps one). With 7 or more armed families, 6 leave.
"""

import math

NAME = "bandits-rebellion-raid"
DESCRIPTION = "Banditry timer expires: blocked while unarmed, then the armed families leave and an Outlaws squad raids the village."
LIMIT_S = 2400
SPEED = 3
LONG_REASON = "The raid needs about 300 game seconds to burn and leave, and then 10 game days."
WATCH_S = 420
STEP_S = 10
SPEAR, SHIELD = 133, 271
LOOTED = "enough looted"


def state(ctx) -> dict:
    return ctx.mod.command("InvasionMod.bandits_state")


def homes(ctx) -> dict:
    return ctx.mod.command("InvasionMod.bandits_homes")


def goods_in_homes(info: dict) -> int:
    """Goods in the homes. Two families can share a home (seen in this fixture), so each building counts once."""
    seen: set = set()
    total = 0
    for home in info["homes"]:
        key = home.get("key")
        if key is not None and key in seen:
            continue
        seen.add(key)
        total += sum(row["amount"] for row in home["inventory"])
    return total


def run_game_seconds(ctx, seconds: float) -> None:
    """Game time with one retry after a pop-up (a pop-up holds the pause)."""
    ctx.popups()
    try:
        ctx.time.run_game_seconds(seconds, speed=SPEED)
    except Exception as error:  # TimeControlError: the clock did not move
        ctx.log.info(f"game time failed ({error}); closing pop-ups and trying again")
        ctx.popups()
        ctx.time.run_game_seconds(seconds, speed=SPEED)


def outlaws(lords: dict):
    return next((lord for lord in lords["lords"] if lord.get("bandit")), None)


def squad_distance(lords: dict, at: dict):
    out = outlaws(lords)
    squads = [s for s in (out or {}).get("squads", []) if s.get("alive") and s.get("x") is not None]
    if not squads or not at:
        return None
    return min(math.hypot(s["x"] - at["x"], s["y"] - at["y"]) for s in squads)


def warm_up(ctx) -> None:
    """The clock stands still for a while after a load (intro). Run a few game seconds, with retries, as the probe scenarios do."""
    for attempt in range(4):
        try:
            ctx.time.run_game_seconds(2, speed=SPEED)
            return
        except Exception as error:  # TimeControlError
            ctx.log.info(f"warm-up {attempt} failed: {error}")
            ctx.popups()
    raise RuntimeError("the game clock did not start")


def expire_timer(ctx, key: str) -> dict:
    """Order 20 and an expired timer. The game stays paused, so goods that the test put into the homes are still there when the mod looks
    (the game takes unused weapons out of homes after about a game day). `key` is the counter that must rise: blocks or leaves."""
    before = state(ctx)[key]
    ctx.mod.command("InvasionMod.bandits_set_order", value=20)
    ctx.mod.command("InvasionMod.bandits_set_timer_days_left", days=0)
    ctx.run_until(lambda: state(ctx)[key] > before, 30, what=f"the counter {key}")
    return state(ctx)


def run(ctx) -> dict:
    a = ctx.actions
    warm_up(ctx)
    ctx.run_until(lambda: state(ctx)["outlaws"]["ready"], 90, what="ensure_outlaw_pawn at the start")
    for _ in range(12):  # the camp cleanup needs game time (camp built, brigands killed, camp demolished)
        if not state(ctx)["outlaws"]["camp_cleanup"]:
            break
        run_game_seconds(ctx, 20)
    s0 = state(ctx)
    ctx.check("the Outlaws pawn exists after the start", s0["bandit_pawn"] is True, s0["outlaws"])
    ctx.check("the camp Brigands are gone", ctx.actions.units_census().get("by_side", {}).get("bandit", 0) == 0, ctx.actions.units_census().get("by_side"))
    h0 = homes(ctx)
    ctx.check("no home holds weapons in this fixture", h0["valid"] == 0, h0["valid"])
    families0 = s0["families"]
    wanted = min(6, families0 - 1)
    ctx.metric("families_start", families0)

    # 2. Blocked: nobody is armed.
    blocked = expire_timer(ctx, "blocks")
    ctx.check("the unarmed village is blocked", blocked["blocks"] >= 1 and blocked["blocked"] is not None, blocked["blocked"])
    ctx.check("blocked: no family left", blocked["families"] == families0 and blocked["converted_families"] == 0, [blocked["families"], blocked["converted_families"]])
    ctx.check("blocked: the timer stays expired", blocked["timer"]["active"] is True and blocked["timer"]["days_left"] <= 0, blocked["timer"])
    ctx.check("blocked: the order did not rise", blocked["mod_order"] <= 25, blocked["mod_order"])

    # 3. Too few armed homes: still blocked after a new tick.
    ctx.mod.command("InvasionMod.bandits_stock_homes", good=SPEAR, amount=2, homes=max(1, wanted - 2))
    ctx.mod.command("InvasionMod.bandits_tick_now")
    partial = expire_timer(ctx, "blocks")
    ctx.check("too few armed homes: still blocked", partial["converted_families"] == 0 and partial["blocks"] >= 2, [partial["converted_families"], partial["blocks"]])

    # Arm every home, then a new tick retries.
    ctx.mod.command("InvasionMod.bandits_stock_homes", good=SPEAR, amount=2, homes=families0)
    ctx.mod.command("InvasionMod.bandits_stock_homes", good=SHIELD, amount=1, homes=families0)
    armed = homes(ctx)
    goods_before = goods_in_homes(armed)
    ctx.check("all homes are armed now", armed["valid"] == families0, armed["valid"])
    stock_before = a.sack_census()["stock"]["total"]
    ctx.mod.command("InvasionMod.bandits_tick_now")
    clock0 = ctx.bridge.read_clock_value()
    after = expire_timer(ctx, "leaves")
    leave = after["last_leave"]
    lords = a.lords_state(log=60)

    # 4. The rebellion.
    ctx.check("the rebellion happened", after["converted_families"] == wanted, [after["converted_families"], wanted])
    ctx.check("the village keeps at least one family", after["families"] >= 1, after["families"])
    ctx.check("one Brigands squad of 18 spawned", leave["spawned"] is True and leave["squads"] == 1 and leave["bandit_units"] == 18, leave)
    ctx.check("the order rose by 25 (a tick may add 10)", 45 <= after["mod_order"] <= 55, after["mod_order"])
    ctx.check("the banner and the log say the families left", leave["removed"] == wanted, leave)
    h1 = homes(ctx)
    taken = leave["taken"]
    ctx.check("the goods of the chosen homes were taken (3 or more per home)", taken >= 3 * wanted, [taken, wanted])
    ctx.check("the other homes keep their goods (the chosen homes are gone from the list)", goods_in_homes(h1) == goods_before - taken, [goods_in_homes(h1), goods_before, taken])
    ctx.check("no item failed to be taken", leave.get("returned", 0) == 0, leave)
    overrides = ctx.mod.command("InvasionMod.raid_behavior_override_state")
    in_overrides = sum(len(entry["goods"]) for entry in overrides["entries"])
    ctx.check("all taken goods are loot overrides of the brigands", in_overrides == taken and overrides["count"] >= 1, [in_overrides, taken, overrides["count"]])
    near = squad_distance(lords, leave.get("camp_at"))
    ctx.metric("squad_distance_to_home", near if near is not None else -1)
    ctx.check("the squad spawned within 500 units of a removed home", near is not None and near <= 500, near)
    ctx.screenshot("rebels_spawned")

    # 5. The raid.
    burned_at = looted_at = None
    elapsed = 0.0
    seen = set()
    while elapsed < WATCH_S and (burned_at is None or looted_at is None):
        run_game_seconds(ctx, STEP_S)
        elapsed += STEP_S
        census = a.sack_census()["buildings"]
        if burned_at is None and census["burning"] + census["rubble"] > 0:
            burned_at = elapsed
            ctx.screenshot("raid_burning")
        for name, lines in (a.lords_state(log=60).get("logs") or {}).items():
            for line in lines:
                if LOOTED in line and (name, line) not in seen:
                    seen.add((name, line))
                    looted_at = looted_at or elapsed
    ctx.metric("first_burn_s", burned_at if burned_at is not None else -1)
    ctx.metric("enough_looted_s", looted_at if looted_at is not None else -1)
    ctx.check("a building burns within 400 game seconds", burned_at is not None and burned_at <= 400, burned_at)
    ctx.check("the AI logs enough looted within 400 game seconds", looted_at is not None and looted_at <= 400, looted_at)
    stock_after = a.sack_census()["stock"]["total"]
    ctx.metric("stock_change", stock_after - stock_before)
    ctx.notes.append(f"plunder: stock {stock_before} -> {stock_after} (burning also destroys goods)")

    # Removal at the map edge: wait for the squads to leave, then record what is left.
    run_game_seconds(ctx, 180)
    mid = ctx.actions.units_census().get("by_side", {}).get("bandit", 0)
    ctx.metric("bandit_units_after_leave", mid)
    ctx.metric("override_entries_after_leave", ctx.mod.command("InvasionMod.raid_behavior_override_state")["count"])
    day0 = state(ctx)["day"]
    ctx.popups()
    ctx.time.run_game_days(10, speed=SPEED)
    final = state(ctx)
    ctx.check("the game runs 10 more game days", final["day"] >= day0 + 10, [day0, final["day"]])
    ctx.metric("bandit_units_end", ctx.actions.units_census().get("by_side", {}).get("bandit", 0))
    ctx.metric("elapsed_since_leave_game_s", ctx.bridge.read_clock_value() - clock0)
    return ctx.result()
