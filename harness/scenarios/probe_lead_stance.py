"""Probe for lead 1.2 (stances) of the change spike-community-mod-leads, issue #280.

Research tool, not in the regular suite:
    uv run python harness\run.py --scenario probe-lead-stance --slot 0
A new AI lord with three army squads is at war with the player and starts a challenge. At the same time the probe calls
SetBehaviourStance: squad 1 aggressive, squad 2 defensive, squad 3 untouched (control). It never reads the Squad struct
(a read of a Squad struct ends the game). It records alive units and position of each squad (lords_state) over time and
takes screenshots. It never calls a save function.
"""

from runlib.leadprobe import Probe, lord_squad_row, start_war

NAME = "probe-lead-stance"
LIMIT_S = 400
HIDDEN = True
LONG_REASON = "The army marches and fights during about 60 game seconds."
WATCH_S = 10
READS = 4
STANCES = ("aggressive", "defensive", None)


def state_of(probe: Probe, lord: int, squad: int):
    row = lord_squad_row(probe, lord, squad)
    return {"x": row["x"], "y": row["y"], "alive": row["alive"]} if row else None


def run(ctx) -> dict:
    probe = Probe(ctx)
    lord, squads = start_war(probe, "Lead Stance Baron", squads=3, defenders=2)
    if len(squads) < 3:
        return ctx.result()
    probe.attempt("challenge", lambda: ctx.actions.lord_challenge(lord))
    probe.wait(WATCH_S)
    ctx.screenshot("stance-0-before")
    for squad, stance in zip(squads, STANCES):
        if stance:
            answer = probe.attempt(f"set {stance}", lambda s=squad, st=stance: ctx.actions.lead_stance(s, st))
            probe.metric(f"call_ok_{stance}", bool(answer and answer.get("ok")))
    for turn in range(1, READS + 1):
        probe.wait(WATCH_S)
        for label, squad in zip(("aggressive", "defensive", "control"), squads):
            state = state_of(probe, lord, squad)
            probe.note(f"state {label} {turn}", squad=squad, state=state)
            probe.metric(f"alive_{label}_{turn}", (state or {}).get("alive", 0))
        if turn == 1:
            ctx.screenshot("stance-1-after")
    ctx.screenshot("stance-2-end")
    return ctx.result()
