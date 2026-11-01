"""Spike (change spike-vassals-without-ai-opponents): do vassals work with AI opponents 0?

Run it on the fixture playtest-noai. The scenario claims and settles up to two regions one after the other, watches 20 game days, reads the
`vassals` guard value, the vassal registry, the tribute and a policy change. It saves nothing. Most results are metrics and log lines (observation).
"""

NAME = "vassals-spike-noai"
DESCRIPTION = "Spike: two vassals with AI opponents 0 (handover, building, peace, tribute, guard value)."
LIMIT_S = 1000
SPEED = 2
STEP_DAYS = 5
WATCH_DAYS = 20
LONG_REASON = "Two claims and handovers plus 20 game days at speed 2 and two season jumps."
INFLUENCE = 1000
SEASONS = ["spring", "summer", "autumn", "winter"]


def vassals(ctx) -> dict:
    return ctx.mod.command("InvasionMod.vassals_state")


def regions(ctx) -> list:
    return ctx.actions.regions_state()["regions"]


def region_row(ctx, name: str) -> dict:
    return next(r for r in regions(ctx) if r["region"] == name)


def free_regions(ctx) -> list:
    return [r["region"] for r in regions(ctx) if not r.get("owner") and not r.get("settled")]


def make_vassal(ctx, count_after: int) -> str:
    region = free_regions(ctx)[0]
    ctx.actions.set_influence(INFLUENCE)
    ctx.actions.claim_region(region, target=0, finalize=True)
    ctx.run_until(lambda: vassals(ctx)["count"] == count_after, 30, what="the claim in the registry")
    ctx.actions.settle_region(region, target=0, settlement_type=1, supply=2)
    ctx.run_until(lambda: vassals(ctx)["vassals"][count_after - 1]["lord"] != "none", 60, what="the handover")
    return region


def run(ctx) -> dict:
    ctx.run_until(lambda: vassals(ctx)["home_region"] != "none", 30, what="the home region")
    guard = ctx.mod.command("InvasionMod.scenario_settings_state")
    ctx.log.info(f"SPIKE guard vassals={guard.get('vassals')} warning={guard.get('warning')} kind={guard.get('kind')}")
    ctx.metric("guard_vassals", guard.get("vassals"))
    ctx.log.info(f"SPIKE free regions at start: {free_regions(ctx)}")
    first = make_vassal(ctx, 1)
    state = vassals(ctx)
    owner = region_row(ctx, first)
    ctx.log.info(f"SPIKE handover 1: {state['vassals']} owner={owner}")
    ctx.check("the first region is handed to a lord", state["vassals"][0]["lord"] != "none" and "AI" in str(owner.get("owner")), [state["vassals"], owner])
    start1 = owner.get("buildings") or 0
    second = None
    start2 = 0
    if len(free_regions(ctx)) > 0:
        try:
            second = make_vassal(ctx, 2)
            start2 = region_row(ctx, second).get("buildings") or 0
            ctx.log.info(f"SPIKE handover 2: {vassals(ctx)['vassals']} owner={region_row(ctx, second)}")
        except Exception as error:
            ctx.log.info(f"SPIKE second vassal failed: {error}")
    ctx.metric("second_vassal", int(second is not None))
    ctx.metric("vassal_count", vassals(ctx)["count"])
    war_seen = False
    for step in range(STEP_DAYS, WATCH_DAYS + 1, STEP_DAYS):
        ctx.time.run_game_days(STEP_DAYS, speed=SPEED)
        cur = vassals(ctx)
        wars = [w for w in (cur.get("wars") or {}).values() if w and (w["enemy_of_player"] or "at_war" in w["tags"])]
        war_seen = war_seen or bool(wars)
        ctx.log.info(f"SPIKE step {step}: b1={region_row(ctx, first).get('buildings')} b2={region_row(ctx, second).get('buildings') if second else None} wars={cur.get('wars')} stalled={[v['stalled'] for v in cur['vassals']]}")
    ctx.metric("buildings1_start", start1)
    ctx.metric("buildings1_end", region_row(ctx, first).get("buildings") or 0)
    ctx.metric("buildings2_start", start2)
    ctx.metric("buildings2_end", (region_row(ctx, second).get("buildings") or 0) if second else 0)
    ctx.metric("war_seen", int(war_seen))
    final = vassals(ctx)
    ctx.metric("stalled_flags", sum(1 for v in final["vassals"] if v["stalled"]))
    ctx.metric("peace_calls", sum((final.get("peace_calls") or {}).values()))
    ctx.log.info(f"SPIKE final registry: {final['vassals']}")
    tribute = ctx.mod.command("InvasionMod.tribute_state")
    before = tribute["ticks"]
    ctx.mod.command("InvasionMod.vassals_set_policy", slot=1, policy="heavy")
    ctx.actions.set_season(SEASONS[(tribute["last_season"] + 1) % 4])
    ctx.run_until(lambda: ctx.mod.command("InvasionMod.tribute_state")["ticks"] > before, 30, what="the tribute tick")
    payments = ctx.mod.command("InvasionMod.tribute_state")["history"][-1]["payments"]
    ctx.log.info(f"SPIKE tribute payments: {payments}")
    ctx.metric("tribute_payments", len(payments))
    ctx.check("the tribute pays the heavy share for slot 1", bool(payments) and payments[0]["policy"] == "heavy", payments)
    guard_end = ctx.mod.command("InvasionMod.scenario_settings_state")
    ctx.metric("guard_vassals_end", guard_end.get("vassals"))
    return ctx.result()
