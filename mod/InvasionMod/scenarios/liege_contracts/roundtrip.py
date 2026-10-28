"""update-liege-tribute-to-contracts: the contract state survives a harness save and a load.

Two runs make one round trip, because a run cannot load a save by itself:
  1. phase write (default): complete one contract (influence 20), offer three, pick one with progress 7, save with save_game(keep=True).
     uv run python harness/run.py --scenario liege-contracts-roundtrip
  2. phase read: load the kept slot. The active contract, the counters and the influence come back, and no new offer is drawn.
     uv run python harness/run.py --scenario liege-contracts-roundtrip --save <SaveGames>/<slot>.sav --env CONTRACTS_PHASE=read
The kept slot stays in the user's save folder. Delete it after the check (the harness does not).
"""

import time

NAME = "liege-contracts-roundtrip"
DESCRIPTION = "Pick a contract with progress, save, load the save in a second run and read the same contract, counters and influence."
LIMIT_S = 300
PREFIX = "InvasionMod."
POLL_WAIT_S = 5.0


def contracts(ctx) -> dict:
    return ctx.mod.command(PREFIX + "liege_contracts_state")


def write_phase(ctx) -> dict:
    ctx.mod.command(PREFIX + "liege_contracts_offer_now", ids="raise_the_levy.clear_the_roads.keep_the_peace")
    ctx.mod.command(PREFIX + "liege_contract_pick", id="raise_the_levy")
    ctx.mod.command(PREFIX + "liege_contracts_test_progress", index=1, value=2)
    ctx.mod.command(PREFIX + "liege_contract_complete")
    state = contracts(ctx)
    ctx.check("R1 one contract is done with 20 influence", state["done"] == 1 and abs(state["influence"] - 20) < 0.01, state)
    ctx.mod.command(PREFIX + "liege_contracts_offer_now", ids="clear_the_roads.keep_the_peace.feed_the_city")
    ctx.mod.command(PREFIX + "liege_contract_pick", id="clear_the_roads")
    ctx.mod.command(PREFIX + "liege_contracts_test_progress", index=1, value=7)
    before = contracts(ctx)
    ctx.check("R2 the progress is 7", before["active"]["objectives"][0]["progress"] == 7, before["active"])
    record = ctx.actions.save_game("liege contracts roundtrip", keep=True)
    ctx.log.info(f"CONTRACTS saved slot {record['slot']} state={before}")
    result = ctx.result()
    result["slot"] = record["slot"]
    return result


def read_phase(ctx) -> dict:
    ctx.run_until(lambda: contracts(ctx).get("active") is not None, 30, what="the loaded contract state")
    time.sleep(POLL_WAIT_S)
    state = contracts(ctx)
    ctx.log.info(f"CONTRACTS after load {state}")
    ctx.check("R3 the active contract came back", state["active"]["id"] == "clear_the_roads", state.get("active"))
    ctx.check("R4 the objective target came back", state["active"]["objectives"][0]["target"] == 15, state["active"])
    ctx.check("R5 the counters and the influence came back", state["done"] == 1 and abs(state["influence"] - 20) < 0.01, state)
    ctx.check("R6 no offer was drawn after the load", state["offer"] == [], state["offer"])
    ctx.check("R7 the start day came back", state["active"]["start_day"] > 0, state["active"])
    return ctx.result()


def run(ctx) -> dict:
    phase = ctx.variant_option("CONTRACTS_PHASE", "write")
    if phase not in ("write", "read"):
        return ctx.fail("phase", f"CONTRACTS_PHASE must be write or read, got {phase}")
    return write_phase(ctx) if phase == "write" else read_phase(ctx)
