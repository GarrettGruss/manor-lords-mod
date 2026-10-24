"""add-scenario-start-kit: a new game gets the start kit (10 people, 300 silver) once, when the player clicks "Begin the game".

Needs a new game and the pak: `run.py --scenario scenario-settings-start-kit --new-game --pak InvasionMod`. It saves nothing.
"""

NAME = "scenario-settings-start-kit"
DESCRIPTION = "New game: no kit before Begin; after Begin the village has 10 people and the player 300 silver; a second apply gives nothing. Needs --new-game --pak InvasionMod."
LIMIT_S = 300
PREFIX = "InvasionMod."


def kit(ctx) -> dict:
    return ctx.mod.command(PREFIX + "start_kit_state")


def run(ctx) -> dict:
    expect = ctx.expect
    ctx.run_until(lambda: ctx.mod.command(PREFIX + "scenario_settings_state")["open"], 150, what="the settings menu opens", poll_s=1.0)
    before = kit(ctx)
    ctx.log.info(f"before Begin: {before}")
    expect.equals("K1 the kit is not given before Begin", before["given"], False)
    expect.equals("K1 the village starts with 10 people", before["people"], 10)

    ctx.mod.command(PREFIX + "scenario_settings_click", action="begin")
    ctx.run_until(lambda: kit(ctx)["given"], 20, what="Begin gives the kit", poll_s=0.5)
    after = kit(ctx)
    ctx.log.info(f"after Begin: {after}")
    ctx.metric("people_after_begin", after["people"])
    ctx.metric("silver_after_begin", after["silver"])
    expect.equals("K2 the village has exactly 10 people", after["people"], 10)
    expect.equals("K2 the player has 300 silver", after["silver"], 300)

    ctx.actions.set_silver(41)
    ctx.mod.command(PREFIX + "scenario_settings_set", yearly=1)
    again = kit(ctx)
    expect.equals("K3 a second apply gives no second kit", again["silver"], 41)
    ctx.pause()
    return ctx.result()
