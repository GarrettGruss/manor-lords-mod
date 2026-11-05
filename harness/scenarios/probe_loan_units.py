"""Probe for change spike-loan-units: can a script take player squads or villagers away for some days and give them back?

Research tool. HARNESS_VARIANT: squad_plain, squad_tick, squad_far, remove, respawn, families_plain, families_tick.
Run, for example:
    uv run python harness\\run.py --scenario probe-loan-units --fixture playtest-noai --slot 1
It records numbers in probe.jsonl and never fails on a game answer. It never calls a save function.
"""

import json
import os

NAME = "probe-loan-units"
LIMIT_S = 500
HIDDEN = True
LONG_REASON = "The probe watches game days after a hide."
VARIANT = os.environ.get("HARNESS_VARIANT", "squad_plain")
TEMPLATE = os.environ.get("HARNESS_TEMPLATE", "spearMilitia")
DAYS = int(os.environ.get("HARNESS_DAYS", "2"))


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

    def loan(self, step, **fields):
        return self.attempt(step, lambda: self.ctx.actions._command("loan_probe", **fields))  # noqa: SLF001

    def census(self, label):
        units = self.attempt(f"{label} census", self.ctx.actions.units_census) or {}
        self.note(f"{label} census summary", by_side=units.get("by_side"), by_state=units.get("by_state"), units=units.get("units"))
        battle = self.attempt(f"{label} battle_state", self.ctx.actions.battle_state) or {}
        self.note(f"{label} battle summary", by_side=battle.get("by_side"), squads=[(s["id"], s["template"], s["initial"], s["alive"]) for s in battle.get("squads", [])])
        return units, battle

    def spawn(self, template):
        record = self.attempt(f"spawn {template}", lambda: self.ctx.actions.spawn_units("player", template, 1))
        squads = ((record or {}).get("answer") or {}).get("squads") or []
        return squads[0]["id"] if squads else None


def squad_variant(probe, ctx):
    source = VARIANT.split("_", 1)[1]
    squad = probe.spawn(TEMPLATE)
    if squad is None:
        return
    ctx.time.run_game_seconds(3, speed=1)
    probe.census("before")
    probe.loan("state before", mode="state", squad=squad)
    probe.loan("hide", mode="hide", squad=squad, source=source)
    ctx.screenshot("hidden")
    for step in range(DAYS):
        ctx.time.run_game_seconds(40, speed=3)
        probe.loan(f"state after day {step + 1}", mode="state", squad=squad)
        probe.census(f"after day {step + 1}")
    probe.loan("show", mode="show")
    ctx.time.run_game_seconds(3, speed=1)
    probe.loan("state after show", mode="state", squad=squad)
    probe.census("after show")
    ctx.screenshot("shown")
    ctx.time.run_game_seconds(40, speed=3)
    probe.loan("state 1 day after show", mode="state", squad=squad)


def remove_variant(probe, ctx):
    squad = probe.spawn(TEMPLATE)
    if squad is None:
        return
    ctx.time.run_game_seconds(3, speed=1)
    probe.loan("state before", mode="state", squad=squad)
    probe.loan("remove request", mode="removereq", squad=squad)
    ctx.time.run_game_seconds(10, speed=1)
    probe.loan("state after", mode="state", squad=squad)
    probe.census("after remove")


def funcs(probe, ctx):
    player = ctx.bridge.player_path()
    found = probe.attempt("pawn squad funcs", lambda: sorted({f["name"] for f in ctx.bridge._result("funcs", ref=player)  # noqa: SLF001
                                                              if any(k in f["name"] for k in ("quad", "ransfer", "wner", "ecruit", "etinue", "isband"))}))
    probe.note("pawn squad funcs count", n=len(found or []))


def respawn_variant(probe, ctx):
    funcs(probe, ctx)
    squad = probe.spawn(TEMPLATE)
    if squad is None:
        return
    ctx.time.run_game_seconds(3, speed=1)
    probe.census("before")
    probe.attempt("set xp", lambda: ctx.actions.set_squad_experience(squad, 5))
    probe.attempt("detail before", lambda: [(s["id"], s["alive"], s.get("xp_mean")) for s in ctx.actions.battle_state(detail=True)["squads"]])
    probe.loan("remove request", mode="removereq", squad=squad)
    ctx.time.run_game_seconds(3, speed=1)
    probe.loan("state of old squad", mode="state", squad=squad)
    probe.census("after remove")
    ctx.time.run_game_seconds(40 * DAYS, speed=3)
    probe.census("after days")
    again = probe.spawn(TEMPLATE)
    ctx.time.run_game_seconds(3, speed=1)
    probe.attempt("set xp new", lambda: ctx.actions.set_squad_experience(again, 5))
    probe.census("after respawn")
    probe.loan("state new squad", mode="state", squad=again)
    ctx.screenshot("respawned")
    ctx.time.run_game_seconds(40, speed=3)
    probe.loan("state new squad 1 day later", mode="state", squad=again)


def lose_variant(probe, ctx):
    squad = probe.spawn(TEMPLATE)
    if squad is None:
        return
    ctx.time.run_game_seconds(3, speed=1)
    probe.census("before")
    probe.attempt("clear (just_die)", lambda: ctx.actions.clear_battle("player"))
    ctx.time.run_game_seconds(3, speed=1)
    probe.loan("state of old squad", mode="state", squad=squad)
    probe.census("after kill")
    ctx.time.run_game_seconds(40 * DAYS, speed=3)
    probe.loan("state of old squad later", mode="state", squad=squad)
    probe.census("after days")
    ctx.screenshot("after_days")

def families_variant(probe, ctx):
    source = VARIANT.split("_", 1)[1]
    ctx.time.run_game_seconds(5, speed=3)
    probe.attempt("sack_census before", lambda: ctx.actions.sack_census()["people"])
    probe.loan("family state before", mode="familystate", count=2)
    probe.loan("family hide", mode="familyhide", count=2, source=source)
    ctx.screenshot("hidden")
    for step in range(DAYS):
        ctx.time.run_game_seconds(40, speed=3)
        probe.loan(f"family state after day {step + 1}", mode="familystate", count=2)
        probe.attempt(f"sack_census day {step + 1}", lambda: ctx.actions.sack_census()["people"])
    probe.loan("show", mode="show")
    ctx.time.run_game_seconds(3, speed=1)
    probe.loan("family state after show", mode="familystate", count=2)
    probe.attempt("sack_census after show", lambda: ctx.actions.sack_census()["people"])
    ctx.time.run_game_seconds(40, speed=3)
    probe.loan("family state 1 day after show", mode="familystate", count=2)


def run(ctx) -> dict:
    probe = Probe(ctx)
    probe.note("variant", variant=VARIANT, template=TEMPLATE, days=DAYS)
    ctx.time.run_game_seconds(5, speed=3)
    ctx.actions.set_silver(100000)
    if VARIANT.startswith("squad"):
        squad_variant(probe, ctx)
    elif VARIANT == "remove":
        remove_variant(probe, ctx)
    elif VARIANT == "lose":
        lose_variant(probe, ctx)
    elif VARIANT == "respawn":
        respawn_variant(probe, ctx)
    elif VARIANT.startswith("families"):
        families_variant(probe, ctx)
    return ctx.result()
