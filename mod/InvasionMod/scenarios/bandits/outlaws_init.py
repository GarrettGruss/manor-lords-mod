"""Change update-banditry-rebellion-raid, task 2.4: ensure_outlaw_pawn() makes the Outlaws pawn and removes its camp.

Run on the fixture `playtest-noai` (bandit camps 0: no Outlaws pawn at the start):
  uv run python harness/run.py --scenario bandits-outlaws-init --fixture playtest-noai --max-runs 1000
The init runs by itself a few seconds after the start. The test checks that the pawn exists, the camp building and its 18 Brigands
are gone, and that a second call does nothing. It watches 3 game days: the game must not make a new camp. It saves nothing.
"""

NAME = "bandits-outlaws-init"
DESCRIPTION = "ensure_outlaw_pawn: pawn made, camp and brigands removed, second call does nothing."
LIMIT_S = 400
LONG_REASON = "Three game days at speed 3 after the init."
SPEED = 3


def state(ctx) -> dict:
    return ctx.mod.command("InvasionMod.bandits_state")


def bandit_units(ctx) -> int:
    return ctx.actions.units_census().get("by_side", {}).get("bandit", 0)


def camps(ctx) -> int:
    return len(ctx.actions.encampment_sites().get("sites", []))


def run(ctx) -> dict:
    ctx.run_until(lambda: state(ctx)["outlaws"]["ready"], 90, what="the Outlaws init")
    s = state(ctx)
    ctx.check("the init made the pawn", s["bandit_pawn"] is True and s["outlaws"]["last"]["created"] is True, s["outlaws"])
    ctx.check("the init saw the 18 camp Brigands", s["outlaws"]["last"]["camp_units"] == 18, s["outlaws"])
    # A camp is built by its Brigands. The mod kills them and demolishes the camp once the camp is built (runs rb-init-4 and 5: killing them
    # at once leaves the camp unbuilt, and demolish(true) then does nothing).
    waited = 0
    while (camps(ctx) > 0 or state(ctx)["outlaws"]["camp_cleanup"]) and waited < 300:
        try:
            ctx.time.run_game_seconds(20, speed=SPEED)
            waited += 20
        except Exception as error:  # the clock holds for a while after a load
            ctx.log.info(f"clock: {error}")
            ctx.popups()
            waited += 5
    ctx.metric("camp_gone_after_game_s", waited)
    ctx.check("the cleanup is done", state(ctx)["outlaws"]["camp_cleanup"] is False, state(ctx)["outlaws"])
    ctx.check("no camp building is left", camps(ctx) == 0, camps(ctx))
    ctx.check("no living bandit unit is left", bandit_units(ctx) == 0, ctx.actions.units_census().get("by_side"))
    again = ctx.mod.command("InvasionMod.bandits_ensure_outlaws")
    ctx.check("a second call does nothing", again["ok"] is True and again["info"]["created"] is False and again["bandit_pawn"] is True, again)
    ctx.check("a second call made no camp", camps(ctx) == 0 and bandit_units(ctx) == 0, [camps(ctx), bandit_units(ctx)])
    ctx.time.run_game_days(3, speed=SPEED)
    ctx.check("the game made no new camp in 3 game days", camps(ctx) == 0 and bandit_units(ctx) == 0, [camps(ctx), bandit_units(ctx)])
    return ctx.result()
