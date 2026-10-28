"""Change update-tech-tree-yearly-picks: the start pick, the spring pick and the pick state over a save and a load.

Two runs make one round trip, because a run cannot load a save by itself:
  1. phase write (default): check the start pick, jump to summer (no pick) and to spring (one pick), unlock Night Watch,
     save with save_game(keep=True). The result holds the slot. The step also checks the spring value of the calendar.
     uv run python harness/run.py --scenario tech-tree-picks-roundtrip
  2. phase read: load the kept slot. The picks, the unlocked tech and the spring counter come back, and the same spring
     gives no second pick.
     uv run python harness/run.py --scenario tech-tree-picks-roundtrip --save <SaveGames>/<slot>.sav --env TECH_PHASE=read
The kept slot stays in the user's save folder. Delete it after the check (the harness does not).
"""

import time

NAME = "tech-tree-picks-roundtrip"
DESCRIPTION = "One start pick, one pick at each start of spring, and the pick state survives a harness save and a load."
LIMIT_S = 240
PREFIX = "InvasionMod."
POLL_WAIT_S = 6.0   # the tech tree looks at the season every poll_ms (2 s of real time)
SPRING = 1          # config tech_tree.spring_season; the calendar enum is winter 0, spring 1, summer 2, autumn 3


def tree(ctx) -> dict:
    return ctx.mod.command(PREFIX + "tech_tree_state")


def season(ctx) -> int:
    return ctx.mod.command(PREFIX + "invasion_yearly_state")["season"]


def write_phase(ctx) -> dict:
    ctx.run_until(lambda: tree(ctx)["picks_earned"] >= 1, 30, what="the start pick")
    state = tree(ctx)
    ctx.check("P1 one pick at the start", state["picks_earned"] == 1 and state["free_picks"] == 1, state)
    ctx.actions.set_season("summer")
    ctx.run_until(lambda: season(ctx) == 2, 30, what="summer in the calendar")
    time.sleep(POLL_WAIT_S)
    ctx.check("P2 summer gives no pick", tree(ctx)["picks_earned"] == 1, tree(ctx))
    ctx.actions.set_season("spring")
    ctx.run_until(lambda: season(ctx) == SPRING, 30, what="spring in the calendar")
    ctx.metric("spring_value", season(ctx))
    ctx.check("P3 the spring value of the calendar is the configured one", season(ctx) == SPRING, season(ctx))
    ctx.run_until(lambda: tree(ctx)["picks_earned"] == 2, 30, what="the spring pick")
    time.sleep(POLL_WAIT_S)
    ctx.check("P4 the same spring gives one pick only", tree(ctx)["picks_earned"] == 2, tree(ctx))
    answer = ctx.mod.command(PREFIX + "tech_tree_unlock", node="night_watch")
    ctx.check("P5 a common tech is unlocked with no path", "night_watch" in answer["unlocked"] and answer["free_picks"] == 1, answer)
    before = tree(ctx)
    record = ctx.actions.save_game("tech tree picks roundtrip", keep=True)
    ctx.log.info(f"TECH_PICKS saved slot {record['slot']} spring_no={before['spring_no']}")
    result = ctx.result()
    result["slot"] = record["slot"]
    return result


def read_phase(ctx) -> dict:
    ctx.run_until(lambda: tree(ctx)["unlocked"] != [] or tree(ctx)["picks_earned"] > 0, 30, what="the loaded state")
    time.sleep(POLL_WAIT_S)
    state = tree(ctx)
    ctx.check("P6 the picks came back", state["picks_earned"] == 2 and state["free_picks"] == 1, state)
    ctx.check("P7 the unlocked tech came back", state["unlocked"] == ["night_watch"], state["unlocked"])
    ctx.check("P8 the spring counter came back", state["spring_no"] >= 0, state["spring_no"])
    ctx.check("P9 the same spring gives no second pick after the load", season(ctx) == SPRING and state["picks_earned"] == 2, [season(ctx), state])
    return ctx.result()


def run(ctx) -> dict:
    phase = ctx.variant_option("TECH_PHASE", "write")
    if phase not in ("write", "read"):
        return ctx.fail("phase", f"TECH_PHASE must be write or read, got {phase}")
    return write_phase(ctx) if phase == "write" else read_phase(ctx)
