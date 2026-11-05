"""add-laws-menu: the law state survives a harness save and a load.

Two runs make one round trip, because a run cannot load a save by itself:
  1. phase write (default): enact a law through the menu, unlock a law by contract, add a slot, save with save_game(keep=True).
     uv run python harness/run.py --scenario laws-menu-roundtrip --pak InvasionMod --slot 2
  2. phase read: load the kept slot. The law in force, the contract unlock with its text, the slot and the used enact action come back.
     uv run python harness/run.py --scenario laws-menu-roundtrip --pak InvasionMod --slot 2 --save <SaveGames>/<slot>.sav --env LAWS_PHASE=read
The kept slot stays in the user's save folder. Delete it after the check (the harness does not).
"""

import time

from _laws_menu import picture, PREFIX, SETTLE_S, card, check_texts_match_cards, menu, open_menu, prepare_laws, press, tech

NAME = "laws-menu-roundtrip"
DESCRIPTION = "Enact a law, unlock one by contract, add a slot, save, load the save in a second run and read the same laws state. Needs --pak InvasionMod."
LIMIT_S = 300
SOURCE = "Contract: Round Trip (100%)"


def write_phase(ctx) -> dict:
    prepare_laws(ctx)
    open_menu(ctx)
    press(ctx, "enact", id="trade_pacts")
    press(ctx, "confirm")
    ctx.mod.command(PREFIX + "laws_unlock", id="conscription", source=SOURCE)
    ctx.mod.command(PREFIX + "laws_add_slot")
    time.sleep(SETTLE_S)
    state = menu(ctx)
    ctx.check("R1 before the save: a law in force, 2 slots, the actions used", (tech(ctx)["laws"], state["header"]["slots_text"], state["header"]["enact_text"]) == (["trade_pacts"], "1 / 2", "0 / 1"), state["header"])
    ctx.mod.command(PREFIX + "laws_menu_close")
    record = ctx.actions.save_game("laws menu roundtrip", keep=True)
    ctx.log.info(f"LAWS saved slot {record['slot']}")
    result = ctx.result()
    result["slot"] = record["slot"]
    return result


def read_phase(ctx) -> dict:
    ctx.run_until(lambda: tech(ctx).get("laws") == ["trade_pacts"], 30, what="the loaded law state")
    state = open_menu(ctx)
    ctx.check("R2 the law in force came back", tech(ctx)["laws"] == ["trade_pacts"], tech(ctx)["laws"])
    ctx.check("R3 the contract unlock came back with its text", (card(state, "conscription")["status"], card(state, "conscription")["source"]) == ("Unlocked", "Unlocked by: " + SOURCE), card(state, "conscription"))
    ctx.check("R4 the extra slot came back", (state["slots"], state["header"]["slots_text"]) == (2, "1 / 2"), state["header"])
    ctx.check("R5 the used enact action came back (it is saved with the state)", state["header"]["enact_text"] == "0 / 1", state["header"])
    check_texts_match_cards(ctx, "R6", state)
    picture(ctx, "laws-menu-after-load")
    ctx.mod.command(PREFIX + "laws_menu_close")
    return ctx.result()


def run(ctx) -> dict:
    phase = ctx.variant_option("LAWS_PHASE", "write")
    if phase not in ("write", "read"):
        return ctx.fail("phase", f"LAWS_PHASE must be write or read, got {phase}")
    return write_phase(ctx) if phase == "write" else read_phase(ctx)
