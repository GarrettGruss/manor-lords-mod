"""M01 iteration 01, A3: two saves of the same game keep two different sets of values (no mixing).

  1. phase write (default): set values A, save (keep); set values B, save (keep). The result holds both slots.
  2. phase read: load one slot and compare with the set that MODSTATE_EXPECT names (A or B). Run it once for each slot.
     uv run python harness/run.py --scenario mod-state-two-saves --save <SaveGames>/<slot>.sav --env MODSTATE_PHASE=read --env MODSTATE_EXPECT=A
The kept slots stay in the user's save folder. Delete them after the check.
"""

NAME = "mod-state-two-saves"
LIMIT_S = 240
SETS = {
    "A": {"selftest_int": 111, "selftest_flag": True, "selftest_text": "save_a"},
    "B": {"selftest_int": 222, "selftest_flag": False, "selftest_text": "save_b"},
}


def text_of(value) -> str:
    return str(value).lower() if isinstance(value, bool) else str(value)


def apply_set(ctx, values: dict) -> None:
    for key, value in values.items():
        ctx.mod.command("InvasionMod.mod_state_set", key=key, value=text_of(value))


def write_phase(ctx) -> dict:
    slots = {}
    for name, values in SETS.items():
        apply_set(ctx, values)
        dump = ctx.mod.command("InvasionMod.mod_state_dump")
        ctx.check(f"values {name} are set before the save", dump["values"] == values, dump["values"])
        slots[name] = ctx.actions.save_game(f"modstate two saves {name}", keep=True)["slot"]
        ctx.log.info(f"TWO_SAVES saved {name} -> {slots[name]}")
    ctx.check("the two slots differ", slots["A"] != slots["B"], slots)
    result = ctx.result()
    result["slots"] = slots
    return result


def read_phase(ctx) -> dict:
    wanted = ctx.variant_option("MODSTATE_EXPECT", "")
    if wanted not in SETS:
        return ctx.fail("expect", f"MODSTATE_EXPECT must be A or B, got {wanted!r}")
    dump = ctx.mod.command("InvasionMod.mod_state_dump")
    other = SETS["B" if wanted == "A" else "A"]
    ctx.check(f"A3 the loaded slot holds the values {wanted}", dump["values"] == SETS[wanted], dump["values"])
    ctx.check("A3 the loaded slot does not hold the other values", dump["values"] != other, dump["values"])
    return ctx.result()


def run(ctx) -> dict:
    phase = ctx.variant_option("MODSTATE_PHASE", "write")
    if phase not in ("write", "read"):
        return ctx.fail("phase", f"MODSTATE_PHASE must be write or read, got {phase}")
    return write_phase(ctx) if phase == "write" else read_phase(ctx)
