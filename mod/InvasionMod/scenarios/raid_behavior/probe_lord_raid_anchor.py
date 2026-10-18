"""Probe for M03 iteration 02 (user decision 2026-10-18): lord army with a challenge whose battlefield is anchored at the player manor.

Questions: does the army march to and fight at the manor? Does the region change owner, and can the mod give it back?
Does declare_peace then remove the army? Research tool. It records every answer in `probe.jsonl`. It never saves the game.
"""

import json

NAME = "probe-lord-raid-anchor"
LIMIT_S = 1100
HIDDEN = True
LONG_REASON = "The army marches across the map: about 1000 game seconds."
TEMPLATE = "spearMilitia"
SQUADS = 3
START_DY = -50000
STEP_S = 60
STEPS = 14
PEACE_AFTER_WON = 2
SPEED = 3


def note(ctx, step: str, **data) -> None:
    entry = {"step": step, **data}
    ctx.log.info(f"PROBE {json.dumps(entry, default=str)[:1200]}")
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


def advance(ctx) -> None:
    try:
        ctx.time.run_game_seconds(STEP_S, speed=SPEED)
    except Exception as error:  # noqa: BLE001 - a spotted army drops the speed
        ctx.ensure_alive("advance")
        note(ctx, "advance failed", error=str(error)[:300])


def player_region(ctx) -> dict | None:
    for row in ctx.actions.regions_state().get("regions", []):
        if "MyPawn" in (row.get("owner") or ""):
            return row
    return None


def run(ctx) -> dict:
    actions = ctx.actions
    home = player_region(ctx)
    note(ctx, "home region", region=home and {k: home.get(k) for k in ("region", "name", "owner", "manor", "buildings")})
    made = attempt(ctx, "spawn lord", lambda: actions.spawn_ai_lord("Probe Raider", can_build=False))
    if not made:
        ctx.expect.equals("a lord was spawned", False, True)
        return ctx.result()
    lord = made["lord"]
    attempt(ctx, "relations", lambda: actions.lord_relations(lord))
    attempt(ctx, "start ai", lambda: actions.lord_start_ai(lord, speed=1, can_build=False))
    attempt(ctx, "declare war", lambda: actions.lord_declare_war(lord))
    attempt(ctx, "army", lambda: actions.lord_spawn_army(lord, TEMPLATE, SQUADS, 0, START_DY))
    attempt(ctx, "anchored challenge", lambda: actions.battlefield_anchor(lord=lord))
    lost_since = None
    peaced = False
    for step in range(1, STEPS + 1):
        advance(ctx)
        state = attempt(ctx, f"step {step}", lambda: actions.lords_state(log=3))
        mine = [row for row in (state or {}).get("lords", []) if row.get("name") == "Probe Raider"]
        squads = [(q["id"], q["alive"], q.get("distance_to_player")) for q in mine[0]["squads"]] if mine else None
        challenges = [(c["status"], c["center"], c["days_left"]) for c in (state or {}).get("challenges", [])]
        owner = (player_region(ctx) or {}).get("name")
        regions = {r["region"]: r.get("owner") for r in actions.regions_state().get("regions", []) if home and r["region"] == home["region"]}
        note(ctx, f"step {step} summary", squads=squads, challenges=challenges, home_owner=regions)
        if home and "MyPawn" not in str(regions.get(home["region"])) and lost_since is None:
            lost_since = step
            attempt(ctx, "give region back", lambda: ctx.mod.command("InvasionMod.raid_behavior_claim_back", region=home["region"]))
            note(ctx, "after give back", regions={r["region"]: r.get("owner") for r in actions.regions_state().get("regions", []) if r["region"] == home["region"]})
        if lost_since is not None and step >= lost_since + PEACE_AFTER_WON and not peaced:
            peaced = True
            attempt(ctx, "declare peace", lambda: actions.lord_declare_peace(lord))
    ctx.ensure_alive("lord raid anchor probe")
    ctx.expect.equals("the game stayed alive", True, True)
    return ctx.result()
