"""update-liege-tribute-to-contracts (offer updated by update-liege-contracts-tier-goods): the contract state survives a harness save and a load.

Two runs make one round trip, because a run cannot load a save by itself:
  1. phase write (default): offer nine, fulfil one, save with save_game(keep=True).
     uv run python harness/run.py --scenario liege-contracts-roundtrip
  2. phase read: load the kept slot. The nine contracts, the tier counts and the done count come back, and no new offer is drawn.
     uv run python harness/run.py --scenario liege-contracts-roundtrip --save <SaveGames>/<slot>.sav --env CONTRACTS_PHASE=read
The kept slot stays in the user's save folder. Delete it after the check (the harness does not).
"""

import time

NAME = "liege-contracts-roundtrip"
DESCRIPTION = "Offer nine contracts, fulfil one, save, load the save in a second run and read the same offer and counts."
LIMIT_S = 300
PREFIX = "InvasionMod."
POLL_WAIT_S = 5.0


def contracts(ctx) -> dict:
    return ctx.mod.command(PREFIX + "liege_contracts_state")


OFFER = "s-17-50-g-146-30-0.s-171-70-g-145-25-0.s-32-30-g-27-20-0.m-320-24-g-6-15-0.m-323-20-g-28-20-0.m-172-36-g-149-10-0.l-2-3-k-0-10-0.l-1-1-l-0-1-0.l-3-3-p-0-5-0"


def write_phase(ctx) -> dict:
    ctx.mod.command(PREFIX + "liege_contracts_offer_now", ids=OFFER)
    ctx.actions.give_item(17, 55)
    ctx.mod.command(PREFIX + "liege_contract_fulfil", id="small-1")
    before = contracts(ctx)
    ctx.check("R1 one contract is done and the Small count is 1", before["done"] == 1 and before["tiers"]["small"]["used"] == 1, before["tiers"])
    ctx.check("R2 nine contracts are offered", len(before["offer"]) == 9, before["offer"])
    record = ctx.actions.save_game("liege contracts roundtrip", keep=True)
    ctx.log.info(f"CONTRACTS saved slot {record['slot']} offer={before['offer_text']} used={before['used_text']}")
    result = ctx.result()
    result["slot"] = record["slot"]
    return result


def read_phase(ctx) -> dict:
    ctx.run_until(lambda: len(contracts(ctx).get("offer", [])) > 0, 30, what="the loaded contract state")
    time.sleep(POLL_WAIT_S)
    state = contracts(ctx)
    ctx.log.info(f"CONTRACTS after load {state['offer_text']} {state['used_text']}")
    ctx.check("R3 the nine contracts came back with the same amounts", state["offer_text"] == OFFER.replace("s-17-50-g-146-30-0", "s-17-50-g-146-30-1"), state["offer_text"])
    ctx.check("R4 the tier counts and the done count came back", state["tiers"]["small"]["used"] == 1 and state["done"] == 1, state["tiers"])
    ctx.check("R5 no new offer was drawn after the load", len(state["offer"]) == 9, state["offer"])
    ctx.check("R6 the fulfilled card shows as fulfilled", any(c["id"] == "small-1" and c["done"] for c in state["contracts"]), state["contracts"][:1])
    return ctx.result()


def run(ctx) -> dict:
    phase = ctx.variant_option("CONTRACTS_PHASE", "write")
    if phase not in ("write", "read"):
        return ctx.fail("phase", f"CONTRACTS_PHASE must be write or read, got {phase}")
    return write_phase(ctx) if phase == "write" else read_phase(ctx)
