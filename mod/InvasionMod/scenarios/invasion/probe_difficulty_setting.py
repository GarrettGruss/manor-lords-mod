"""Spike for spike-new-game-difficulty-setting tasks 1.1 and 1.4: read the game setup fields about raids,
write one, and set the mod difficulty several times (also after a raid spawned). It saves nothing.
"""

import json

NAME = "probe-difficulty-setting"
LIMIT_S = 240


def note(ctx, key, value) -> None:
    ctx.notes.append(key + ": " + json.dumps(value, default=str))


def run(ctx) -> dict:
    ctx.run_until(lambda: ctx.mod.command("InvasionMod.invasion_state")["raid_day"] > 0, 30, what="the raid plan")
    setup = ctx.actions.game_setup_state()
    note(ctx, "game_setup_loaded", setup)
    ctx.check("game setup state is readable", setup.get("ok") is True, setup)
    for field, value in (("raidingFrequency", 1), ("yearsUntilFirstRaid", 3)):
        written = ctx.actions.game_setup_set_byte(field, value)
        note(ctx, "write_" + field, written)
        ctx.check("write " + field + " reads back", written.get("ok") is True, written)
    note(ctx, "difficulty_state_start", ctx.mod.command("InvasionMod.invasion_difficulty_state"))
    for value in (3, 1, 2):
        state = ctx.mod.command("InvasionMod.invasion_set_difficulty", value=value)
        ctx.check(f"set difficulty {value} at any time", state["difficulty"] == value, [state["difficulty"], state["squads"]])
    ctx.mod.command("InvasionMod.invasion_pick_difficulty", value=3)
    again = ctx.mod.refusal("InvasionMod.invasion_pick_difficulty", value=1)
    ctx.check("pick is refused a second time", again is not None, again)
    after_pick = ctx.mod.command("InvasionMod.invasion_set_difficulty", value=1)
    ctx.check("set works after the pick", after_pick["difficulty"] == 1, after_pick["difficulty"])
    ctx.mod.command("InvasionMod.invasion_force_next")
    ctx.run_until(lambda: ctx.mod.command("InvasionMod.invasion_state")["raids_spawned"] > 0, 30, what="the raid to spawn")
    before = ctx.mod.command("InvasionMod.invasion_state")
    after = ctx.mod.command("InvasionMod.invasion_set_difficulty", value=3)
    ctx.check("set works after the raid spawned", after["difficulty"] == 3, after["difficulty"])
    note(ctx, "after_spawn", {"squads_before": before["squads"], "squads_after": after["squads"], "raids_spawned": after["raids_spawned"]})
    note(ctx, "setup_end", ctx.actions.game_setup_state())
    return ctx.result()
