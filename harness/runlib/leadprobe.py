"""Shared parts of the probes of the change spike-community-mod-leads (issue #280).

A probe records every game answer in `probe.jsonl` and in metrics. It never fails on a game answer and never saves the game.
"""

import json

ENEMY_TEMPLATE = "spearMilitia"
DEFENDER_TEMPLATE = "retinue_tier3"
ENEMY_OFFSET = 6000
SPEED = 3


class Probe:
    def __init__(self, ctx):
        self.ctx = ctx
        self.path = ctx.run_dir / "probe.jsonl"

    def note(self, step: str, **data) -> None:
        entry = {"step": step, **data}
        self.ctx.log.info(f"PROBE {json.dumps(entry, default=str)[:1800]}")
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, default=str) + "\n")

    def attempt(self, step: str, work):
        """Run `work`, note the answer or the error, and return the answer (None on an error)."""
        try:
            result = work()
        except Exception as error:  # noqa: BLE001 - the probe records every answer
            self.ctx.ensure_alive(step)
            self.note(step, error=str(error)[:600])
            return None
        self.note(step, result=result)
        return result

    def metric(self, name: str, value) -> None:
        """A metric only for a finite number. A missing answer is noted, not recorded."""
        if isinstance(value, bool):
            value = int(value)
        if isinstance(value, (int, float)):
            self.ctx.metric(name, value)
        else:
            self.note("metric missing", name=name, value=value)

    def wait(self, seconds: float) -> None:
        """Game time passes. A spotted army can drop the speed, so a failed wait is noted and the probe goes on."""
        try:
            self.ctx.time.run_game_seconds(seconds, speed=SPEED)
        except Exception as error:  # noqa: BLE001
            self.ctx.ensure_alive("wait")
            self.note("wait failed", error=str(error)[:300])


def start_war(probe: Probe, name: str, squads: int = 1, defenders: int = 3):
    """A new AI lord at war with the player and an army of `squads` squads next to the player village.

    Returns (lord number, squad ids of the army). The baron of the fixture is not touched.
    """
    actions = probe.ctx.actions
    lord = probe.attempt("spawn lord", lambda: actions.spawn_ai_lord(name, can_build=False))
    if not lord:
        return None, []
    number = lord["lord"]
    probe.attempt("lord relations", lambda: actions.lord_relations(number))
    probe.attempt("start ai", lambda: actions.lord_start_ai(number, speed=1, can_build=False))
    probe.attempt("declare war", lambda: actions.lord_declare_war(number))
    army = probe.attempt("lord army", lambda: actions.lord_spawn_army(number, ENEMY_TEMPLATE, squads, ENEMY_OFFSET, 0))
    if defenders:
        probe.attempt("defenders", lambda: actions.spawn_units("player", DEFENDER_TEMPLATE, defenders, ENEMY_OFFSET - 500, 0))
    return number, (army or {}).get("squads", [])


def units_of(probe: Probe, squads: list) -> int:
    """Living units in these squads (steer_state is read only)."""
    total = 0
    for squad in squads:
        state = probe.attempt(f"units of {squad}", lambda squad=squad: probe.ctx.actions.steer_state(squad))
        total += (state or {}).get("units") or 0
    return total
