"""M01 iteration 01, A4, A5 and A6: a save from before the mod gives default values and no error. Other Tags stay as they are.

Runs on the default fixture `base` (a save made without the mod). It saves nothing.
"""

NAME = "mod-state-default-load"
LIMIT_S = 120
PREFIX = "invasion:"
FOREIGN = ["mstest_first", "mstest_second"]
DEFAULTS = {"selftest_int": 0, "selftest_flag": False, "selftest_text": "none"}
LOG_TAGS = ("InvasionMod", "ModState")


def foreign_tags(tags: list[str]) -> list[str]:
    return [tag for tag in tags if not tag.startswith(PREFIX)]


def error_lines(ctx) -> list[str]:
    log = ctx.run_dir / "mod.log"
    if not log.exists():
        return ["mod.log is missing"]
    return [line for line in log.read_text(encoding="utf-8", errors="replace").splitlines()
            if " ERROR " in line and any(tag in line for tag in LOG_TAGS)]


def run(ctx) -> dict:
    dump = ctx.mod.command("InvasionMod.mod_state_dump")
    ctx.check("A4 the state is loaded", dump["loaded"] is True, dump["loaded"])
    ctx.check("A4 all values are the defaults", dump["values"] == DEFAULTS, dump["values"])
    ctx.check("A4 the save has no mod entry", not [tag for tag in dump["tags"] if tag.startswith(PREFIX)], dump["tags"])
    ctx.check("A4 no stored version", dump.get("stored_version") is None, dump.get("stored_version"))
    ctx.check("A4 no error in the log", not error_lines(ctx), error_lines(ctx))

    for tag in FOREIGN:
        ctx.mod.command("InvasionMod.mod_state_add_foreign_tag", tag=tag)
    before = foreign_tags(ctx.mod.command("InvasionMod.mod_state_dump")["tags"])
    ctx.check("the foreign Tags were added", before[-len(FOREIGN):] == FOREIGN, before)

    ctx.mod.command("InvasionMod.mod_state_set", key="selftest_int", value="7")
    ctx.mod.command("InvasionMod.mod_state_set", key="selftest_text", value="changed")
    ctx.mod.command("InvasionMod.mod_state_set", key="selftest_int", value="8")
    after = ctx.mod.command("InvasionMod.mod_state_dump")
    ctx.check("A6 Tags without the prefix are the same after the flushes", foreign_tags(after["tags"]) == before, foreign_tags(after["tags"]))
    once = sum(tag.startswith(f"{PREFIX}selftest_int=") for tag in after["tags"]) == 1
    ctx.check("A1 the changes are in the Tags once", f"{PREFIX}selftest_int=8" in after["tags"] and once, after["tags"])

    message = ctx.mod.refusal("InvasionMod.mod_state_set", key="selftest_itn", value="1")
    ctx.check("A5 a key that is not registered is refused with a clear message", message is not None and "not registered" in message, message)
    ctx.check("A5 the refused set changed nothing", ctx.mod.command("InvasionMod.mod_state_dump")["tags"] == after["tags"])
    ctx.check("A4 no unexpected error in the log at the end", not error_lines(ctx), error_lines(ctx))
    return ctx.result()
