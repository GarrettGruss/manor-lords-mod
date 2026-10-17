"""M01 iteration 01, A1 and A2: ModState keeps three values (integer, boolean, string) over a harness save and a load.

Two runs make one round trip, because a run cannot load a save by itself:
  1. phase write (default): set the values, check A1, save with save_game(keep=True). The result holds the slot.
     uv run python harness/run.py --scenario mod-state-roundtrip
  2. phase read: load the kept slot and compare the values (A2).
     uv run python harness/run.py --scenario mod-state-roundtrip --save <SaveGames>/<slot>.sav --env MODSTATE_PHASE=read
The kept slot stays in the user's save folder. Delete it after the check (the harness does not).
"""

NAME = "mod-state-roundtrip"
LIMIT_S = 180
PREFIX = "invasion:"
EXPECTED = {"selftest_int": 4127, "selftest_flag": True, "selftest_text": "round_trip.A-1"}
DEFAULTS = {"selftest_int": 0, "selftest_flag": False, "selftest_text": "none"}


def text_of(value) -> str:
    return str(value).lower() if isinstance(value, bool) else str(value)


def entry_count(tags: list[str], key: str) -> int:
    return sum(1 for tag in tags if tag.startswith(f"{PREFIX}{key}="))


def set_value(ctx, key: str, value) -> None:
    ctx.mod.command("InvasionMod.mod_state_set", key=key, value=text_of(value))


def write_phase(ctx) -> dict:
    before = ctx.mod.command("InvasionMod.mod_state_dump")
    ctx.check("values are the defaults before the change", before["values"] == DEFAULTS, before["values"])
    set_value(ctx, "selftest_int", 1)  # a second change of the same key must not add a second entry
    for key, value in EXPECTED.items():
        set_value(ctx, key, value)
    after = ctx.mod.command("InvasionMod.mod_state_dump")
    ctx.check("A1 live values are the new values", after["values"] == EXPECTED, after["values"])
    ctx.check("A1 one Tag entry per key", all(entry_count(after["tags"], key) == 1 for key in EXPECTED), after["tags"])
    ctx.check("A1 the Tags hold the new values",
              all(f"{PREFIX}{key}={text_of(value)}" in after["tags"] for key, value in EXPECTED.items()), after["tags"])
    record = ctx.actions.save_game("modstate roundtrip", keep=True)
    ctx.log.info(f"ROUNDTRIP saved slot {record['slot']}")
    result = ctx.result()
    result["slot"] = record["slot"]
    return result


def read_phase(ctx) -> dict:
    dump = ctx.mod.command("InvasionMod.mod_state_dump")
    ctx.check("A2 the values came back after the load", dump["values"] == EXPECTED, dump["values"])
    ctx.check("A2 one Tag entry per key after the load", all(entry_count(dump["tags"], key) == 1 for key in EXPECTED), dump["tags"])
    ctx.check("the stored version came back", dump.get("stored_version") == dump["version"], dump.get("stored_version"))
    return ctx.result()


def run(ctx) -> dict:
    phase = ctx.variant_option("MODSTATE_PHASE", "write")
    if phase not in ("write", "read"):
        return ctx.fail("phase", f"MODSTATE_PHASE must be write or read, got {phase}")
    return write_phase(ctx) if phase == "write" else read_phase(ctx)
