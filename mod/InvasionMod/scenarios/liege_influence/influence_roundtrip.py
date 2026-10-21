"""add-liege-influence: the influence value survives a harness save and a load.

Two runs make one round trip, because a run cannot load a save by itself (as mod-state-roundtrip):
  1. phase write (default): send a tribute, save with save_game(keep=True). The result holds the slot.
     uv run python harness/run.py --scenario liege-influence-roundtrip --new-game
  2. phase read: load the kept slot and read the influence.
     uv run python harness/run.py --scenario liege-influence-roundtrip --save <SaveGames>/<slot>.sav --env LIEGE_PHASE=read
The kept slot stays in the user's save folder. Delete it after the check (the harness does not).
"""

NAME = "liege-influence-roundtrip"
DESCRIPTION = "Send 300 silver of tribute (30 influence), save, load the save in a second run, and read 30 influence."
LIMIT_S = 240
PREFIX = "InvasionMod."
AMOUNT = 300
EXPECTED = 30.0


def liege(ctx) -> dict:
    return ctx.mod.command(PREFIX + "liege_state")


def write_phase(ctx) -> dict:
    ctx.actions.set_silver(1000)
    ctx.mod.command(PREFIX + "liege_send_tribute", amount=AMOUNT)
    state = liege(ctx)
    ctx.check("the influence is 30 before the save", abs(state["influence"] - EXPECTED) < 0.01, state)
    record = ctx.actions.save_game("liege influence roundtrip", keep=True)
    ctx.log.info(f"ROUNDTRIP saved slot {record['slot']}")
    result = ctx.result()
    result["slot"] = record["slot"]
    return result


def read_phase(ctx) -> dict:
    state = liege(ctx)
    ctx.log.info(f"after load {state}")
    ctx.check("the influence came back after the load", abs(state["influence"] - EXPECTED) < 0.01, state)
    return ctx.result()


def run(ctx) -> dict:
    phase = ctx.variant_option("LIEGE_PHASE", "write")
    if phase not in ("write", "read"):
        return ctx.fail("phase", f"LIEGE_PHASE must be write or read, got {phase}")
    return write_phase(ctx) if phase == "write" else read_phase(ctx)
