"""Probe for spec 10 spike S11 (baron model) rerun: lord_claim, lord_declare_peace and the "challenge lost" path with a spawned lord.

Research tool. It records every answer in `probe.jsonl` and never fails on a game answer. It never saves the game.
The lord is a new one (spawn_ai_lord), so the baron of the fixture is not changed.
"""

import json
import os

NAME = "probe-lord-diplomacy"
LIMIT_S = 600
HIDDEN = True
LONG_REASON = "The probe runs a short war and a battle: about 400 game seconds."
CLAIM_WATCH_S = 120
BATTLE_STEP_S = 60
BATTLE_STEPS = int(os.environ.get("LORD_DIPLOMACY_BATTLE_STEPS", "6"))
ENEMY_TEMPLATE = "spearMilitia"
DEFENDER_TEMPLATE = "retinue_tier3"
ENEMY_OFFSET = 6000
SPEED = 3


class Probe:
    def __init__(self, ctx):
        self.ctx = ctx

    def note(self, step: str, **data) -> None:
        entry = {"step": step, **data}
        self.ctx.log.info(f"PROBE {json.dumps(entry, default=str)[:1500]}")
        with (self.ctx.run_dir / "probe.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, default=str) + "\n")

    def attempt(self, step: str, work):
        try:
            result = work()
        except Exception as error:  # noqa: BLE001 - the probe records every answer
            self.ctx.ensure_alive(step)
            self.note(step, error=str(error)[:500])
            return None
        self.note(step, result=result)
        return result


def claim_test(probe, lord: int) -> None:
    actions = probe.ctx.actions
    probe.attempt("claim before", actions.lords_state)
    probe.attempt("lord_claim", lambda: actions.lord_claim(lord))
    probe.ctx.time.run_game_seconds(CLAIM_WATCH_S, speed=SPEED)
    probe.attempt("claim after watch", lambda: actions.lords_state(log=20))


def war_and_peace(probe, lord: int) -> None:
    actions = probe.ctx.actions
    probe.attempt("declare war", lambda: actions.lord_declare_war(lord))
    probe.attempt("declare peace", lambda: actions.lord_declare_peace(lord))
    probe.attempt("relations after peace", actions.lords_state)


def challenge_lost(probe, lord: int) -> None:
    actions = probe.ctx.actions
    probe.attempt("war again", lambda: actions.lord_declare_war(lord))
    probe.attempt("lord army", lambda: actions.lord_spawn_army(lord, ENEMY_TEMPLATE, 1, ENEMY_OFFSET, 0))
    probe.attempt("player defenders", lambda: actions.spawn_units("player", DEFENDER_TEMPLATE, 3, ENEMY_OFFSET - 500, 0))
    probe.attempt("challenge", lambda: actions.lord_challenge(lord))
    for step in range(1, BATTLE_STEPS + 1):
        probe.ctx.time.run_game_seconds(BATTLE_STEP_S, speed=SPEED)
        probe.attempt(f"battle step {step}", lambda: actions.lords_state(log=6))
        probe.attempt(f"battle units {step}", actions.battle_state)
    probe.attempt("regions at end", actions.regions_state)


def run(ctx) -> dict:
    probe = Probe(ctx)
    actions = ctx.actions
    lord = probe.attempt("spawn lord", lambda: actions.spawn_ai_lord("Probe Baron", can_build=False))
    if not lord:
        ctx.expect.equals("a lord was spawned", False, True)
        return ctx.result()
    number = lord["lord"]
    probe.attempt("relations", lambda: actions.lord_relations(number))
    probe.attempt("start ai", lambda: actions.lord_start_ai(number, speed=1, can_build=False))
    claim_test(probe, number)
    war_and_peace(probe, number)
    challenge_lost(probe, number)
    ctx.ensure_alive("lord diplomacy probe")
    ctx.expect.equals("the game stayed alive", True, True)
    return ctx.result()
