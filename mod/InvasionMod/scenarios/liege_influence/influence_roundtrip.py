"""add-liege-influence: the influence value survives a harness save and a load.

Two runs make one round trip, because a run cannot load a save by itself (as mod-state-roundtrip):
  1. phase write (default): fulfil a contract (influence 1000), save with save_game(keep=True). The result holds the slot.
     uv run python harness/run.py --scenario liege-influence-roundtrip --new-game
  2. phase read: load the kept slot and read the influence.
     uv run python harness/run.py --scenario liege-influence-roundtrip --save <SaveGames>/<slot>.sav --env LIEGE_PHASE=read
The kept slot stays in the user's save folder. Delete it after the check (the harness does not).
"""

NAME = "liege-influence-roundtrip"
DESCRIPTION = "Fulfil a contract (1000 influence), save, load the save in a second run, and read 1000 influence."
LIMIT_S = 240
PREFIX = "InvasionMod."
EXPECTED = 1000.0


def liege(ctx) -> dict:
    return ctx.mod.command(PREFIX + "liege_state")


def write_phase(ctx) -> dict:
    ctx.mod.command(PREFIX + "liege_contracts_offer_now", ids="l-293-5-i-0-1000-0.l-273-9-t-0-1-0.l-320-18-t-0-1-0.s-17-50-g-146-30-0.s-145-30-g-17-25-0.s-171-70-g-17-25-0")
    ctx.actions.give_item(293, 5)
    ctx.mod.command(PREFIX + "liege_contract_fulfil", id="large-1")
    state = liege(ctx)
    ctx.check("the influence is 1000 before the save", abs(state["influence"] - EXPECTED) < 0.01, state)
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
