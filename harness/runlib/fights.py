"""Run a fight between spawned squads until it is over (spec 10, spikes C1 and C2).

A fight is over when one side has no living units, or when no squad lost a unit for `calm_polls` polls in a row
(the survivors stopped fighting: one side broke and ran, or both stand apart), or when the wall time is up.
The game runs at speed 3 (8 game seconds for each wall second) during the fight and is paused again afterwards.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import battle
from .waiting import WaitTimeout

FIGHT_SPEED = 3
POLL_S = 2.5
CALM_POLLS = 4          # 10 wall seconds without a casualty
TIMEOUT_S = 90.0
STALL_S = 20.0
# Distance in game units between the two groups at the start. 2500 made the groups meet in about 5 wall seconds at speed 3 (spike C1).
START_GAP = 2500


@dataclass
class FightResult:
    state: dict
    wall_s: float
    reason: str          # "one side gone", "calm" or "timeout"

    @property
    def finished(self) -> bool:
        return self.reason != "timeout"


class _FightWatch:
    """The predicate of the wait. It remembers the last casualty signature."""

    def __init__(self, ctx, side_a: str, side_b: str, calm_polls: int):
        self._ctx = ctx
        self._sides = (side_a, side_b)
        self._calm_polls = calm_polls
        self._signature = None
        self._calm = 0
        self.state: dict = {}
        self.reason = ""

    def __call__(self) -> bool:
        self.state = self._ctx.actions.battle_state()
        if battle.fight_is_over(self.state, *self._sides):
            self.reason = "one side gone"
            return True
        signature = battle.alive_signature(self.state)
        self._calm = self._calm + 1 if signature == self._signature else 0
        self._signature = signature
        if self._calm >= self._calm_polls:
            self.reason = "calm"
            return True
        return False


def run_fight(ctx, side_a: str = "player", side_b: str = "bandit", timeout_s: float = TIMEOUT_S, calm_polls: int = CALM_POLLS) -> FightResult:
    """Let the spawned squads fight. The game must be paused at the start. It is paused again at the end, also after a timeout."""
    watch = _FightWatch(ctx, side_a, side_b, calm_polls)
    ctx.time.set_speed(FIGHT_SPEED)
    try:
        waited = ctx.run_until(watch, timeout_s, what="the fight to end", poll_s=POLL_S, stall_s=STALL_S, on_stall=ctx.popups)
        wall_s, reason = waited.wall_s, watch.reason
    except WaitTimeout:
        wall_s, reason = timeout_s, "timeout"
    finally:
        ctx.time.pause()
    final = ctx.actions.battle_state(detail=True)
    ctx.log.info(f"fight over: {reason}, {wall_s:.0f} wall s, by_side {final['by_side']}")
    return FightResult(final, wall_s, reason)
