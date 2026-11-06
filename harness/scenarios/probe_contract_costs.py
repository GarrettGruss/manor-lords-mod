"""Probe for change update-liege-contracts-tier-goods (spikes 1.1, 1.2, 1.4, 1.5): King's Favour, family removal, animals, timber.

Research tool. HARNESS_VARIANT: favour, families, herd, timber. Run, for example:
    uv run python harness\\run.py --scenario probe-contract-costs --fixture playtest-noai --slot 1
It records every answer in probe.jsonl and never fails on a game answer. It never calls a save function.
"""

import json
import os

NAME = "probe-contract-costs"
LIMIT_S = 400
HIDDEN = True
LONG_REASON = "The probe waits game days after a change."
VARIANT = os.environ.get("HARNESS_VARIANT", "favour")
ANIMALS = [72, 222, 321, 347, 234, 98]
TIMBER = [16, 17, 13, 216, 15]


class Probe:
    def __init__(self, ctx):
        self.ctx = ctx
        self.path = ctx.run_dir / "probe.jsonl"

    def note(self, step, **data):
        entry = {"step": step, **data}
        self.ctx.log.info(f"PROBE {json.dumps(entry, default=str)[:1800]}")
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, default=str) + "\n")

    def attempt(self, step, work):
        try:
            result = work()
        except Exception as error:  # noqa: BLE001
            self.ctx.ensure_alive(step)
            self.note(step, error=str(error)[:500])
            return None
        self.note(step, result=result)
        return result

    def cmd(self, step, **fields):
        return self.attempt(step, lambda: self.ctx.actions._command("loan_probe", **fields))  # noqa: SLF001


def favour(probe, ctx):
    bridge = ctx.bridge
    player = bridge.player_path()

    def read(name):
        return bridge.read_property(player, name)

    probe.note("start", kingsFavour=read("kingsFavour"), influence=read("influence"))
    probe.attempt("days left function", lambda: bridge.call_function(player, "getKingsFavour_daysLeft", []))
    probe.attempt("add_kings_favour 10", lambda: ctx.actions.add_kings_favour(10))
    probe.note("after +10", kingsFavour=read("kingsFavour"))
    ctx.time.run_game_seconds(6, speed=1)
    probe.note("after 6 s", kingsFavour=read("kingsFavour"))
    probe.attempt("days left after", lambda: bridge.call_function(player, "getKingsFavour_daysLeft", []))
    ctx.time.run_game_seconds(40, speed=3)
    probe.note("after one game day", kingsFavour=read("kingsFavour"))
    probe.attempt("days left later", lambda: bridge.call_function(player, "getKingsFavour_daysLeft", []))
    ctx.screenshot("favour")


def families(probe, ctx):
    ctx.time.run_game_seconds(5, speed=3)
    probe.attempt("sack_census before", lambda: ctx.actions.sack_census()["people"])
    probe.cmd("count before", mode="famcount")
    probe.cmd("remove 3", mode="famremove", count=3)
    ctx.time.run_game_seconds(3, speed=1)
    probe.cmd("count after 3 s", mode="famcount")
    probe.attempt("sack_census after", lambda: ctx.actions.sack_census()["people"])
    for day in range(3):
        ctx.time.run_game_seconds(40, speed=3)
        probe.cmd(f"count after day {day + 1}", mode="famcount")
    ctx.screenshot("families")


def herd(probe, ctx):
    ctx.time.run_game_seconds(5, speed=3)
    probe.cmd("herd scan", mode="herdscan")
    for good in ANIMALS:
        probe.cmd(f"stock {good}", mode="stock", good=good)
    probe.cmd("animal class", mode="herdkill", kill=0)
    if os.environ.get("HARNESS_KILL") == "1":
        probe.cmd("just_die on one animal", mode="herdkill", kill=1)
        ctx.time.run_game_seconds(6, speed=1)
        probe.cmd("animal after kill", mode="herdkill", kill=0)
    probe.cmd("take 1 ox", mode="herdtake", good=234, amount=1)
    ctx.time.run_game_seconds(6, speed=1)
    probe.cmd("ox stock after 6 s", mode="stock", good=234)
    ctx.screenshot("after_take")
    ctx.time.run_game_seconds(40, speed=3)
    probe.cmd("ox stock after a day", mode="stock", good=234)
    probe.cmd("herd scan after", mode="herdscan")


def timber(probe, ctx):
    ctx.time.run_game_seconds(5, speed=3)
    for good in TIMBER:
        probe.cmd(f"stock {good}", mode="stock", good=good)


def run(ctx) -> dict:
    probe = Probe(ctx)
    probe.note("variant", variant=VARIANT)
    ctx.time.run_game_seconds(5, speed=3)
    {"favour": favour, "families": families, "herd": herd, "timber": timber}[VARIANT](probe, ctx)
    return ctx.result()
