"""Spike 283 (tasks 1.1 and 1.2): how many Tags survive a save and a load, and do lord and building Tags survive.

Research tool. Phase write (default): write spike entries into the Tags of the pawn, one AI lord and one building, read them back,
make a guarded `save_game` (kept). Phase read: start from that save (`--save <slot>.sav --env TAGS_PHASE=read`) and read them back.
It never calls a save function itself.
"""

import json
import time

NAME = "spike-tags-limits"
LIMIT_S = 280
HIDDEN = True
GROUPS = [("ten", 10, 40), ("hun", 100, 40), ("tho", 1000, 40), ("lng", 1, 4000)]
MARKER = ("mrk", 1, 40)


def note(ctx, step: str, **data) -> None:
    ctx.log.info(f"SPIKE {json.dumps({'step': step, **data}, default=str)[:1500]}")
    with (ctx.run_dir / "spike.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"step": step, **data}, default=str) + "\n")


def write(ctx, target: str, name: str, count: int, size: int, index: int = 1) -> dict:
    result = ctx.mod.command("InvasionMod.spike_tags_write", target=target, label=name, count=count, size=size, index=index)
    note(ctx, "write", target=target, label=name, count=count, size=size, result=result)
    return result


def read(ctx, target: str, name: str, index: int = 1):
    try:
        result = ctx.mod.command("InvasionMod.spike_tags_read", target=target, label=name, index=index)
    except Exception as error:  # a missing target ends a scan
        note(ctx, "read_error", target=target, label=name, index=index, error=str(error))
        return None
    note(ctx, "read", target=target, label=name, index=index, result=result)
    return result


def scan_marker(ctx, target: str) -> list:
    hits, index = [], 1
    while index <= 60:
        result = read(ctx, target, MARKER[0], index)
        if result is None:
            break
        if result["spike_count"]:
            hits.append((index, result))
        index += 1
    return hits


def write_phase(ctx) -> dict:
    for name, count, size in GROUPS:
        write(ctx, "pawn", name, count, size)
    write(ctx, "lord", *MARKER[:1], MARKER[1], MARKER[2])
    write(ctx, "building", MARKER[0], MARKER[1], MARKER[2])
    for name, count, size in GROUPS:
        got = read(ctx, "pawn", name)
        ctx.check(f"before save: {name} entries", got is not None and got["spike_count"] == count, got)
    started = time.monotonic()
    saved = ctx.actions.save_game("spike tags limits", keep=True)
    note(ctx, "saved", slot=saved["slot"], seconds=round(time.monotonic() - started, 2), files=saved["files"])
    result = ctx.result()
    result["slot"] = saved["slot"]
    return result


def read_phase(ctx) -> dict:
    for name, count, size in GROUPS:
        got = read(ctx, "pawn", name)
        ctx.check(f"after load: {name} entries", got is not None and got["spike_count"] == count, got)
    lords = scan_marker(ctx, "lord")
    buildings = scan_marker(ctx, "building")
    ctx.check("after load: lord marker found", len(lords) == 1, lords)
    ctx.check("after load: building marker found", len(buildings) == 1, buildings)
    return ctx.result()


def run(ctx) -> dict:
    phase = ctx.variant_option("TAGS_PHASE", "write")
    return write_phase(ctx) if phase == "write" else read_phase(ctx)
