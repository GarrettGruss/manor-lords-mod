"""Probe for lead 1.2 (stances) of the change spike-community-mod-leads, issue #280.

Research tool, not in the regular suite:
    uv run python harness\\run.py --scenario probe-lead-stance --slot auto
A new AI lord with one army is at war with the player and starts a challenge. The probe reads the stance of one army squad,
calls SetBehaviourStance (aggressive, then defensive) and records the squad centre and the stance after each call.
It takes a screenshot after each call. It never calls a save function.
"""

from runlib.leadprobe import Probe, start_war

NAME = "probe-lead-stance"
LIMIT_S = 400
HIDDEN = True
LONG_REASON = "The army marches during about 60 game seconds."
WATCH_S = 15
STANCES = ("aggressive", "defensive")


def center_of(probe: Probe, squad: int):
    state = probe.attempt("steer_state", lambda: probe.ctx.actions.steer_state(squad))
    return (state or {}).get("center")


def moved(before, after):
    if not before or not after:
        return None
    return round(((after["x"] - before["x"]) ** 2 + (after["y"] - before["y"]) ** 2) ** 0.5)


def run(ctx) -> dict:
    probe = Probe(ctx)
    lord, squads = start_war(probe, "Lead Stance Baron")
    if not squads:
        return ctx.result()
    squad = squads[0]
    probe.attempt("challenge", lambda: ctx.actions.lord_challenge(lord))
    probe.wait(WATCH_S)
    probe.attempt("stance read", lambda: ctx.actions.lead_stance(squad))
    for index, stance in enumerate(STANCES, start=1):
        start = center_of(probe, squad)
        answer = probe.attempt(f"set {stance}", lambda stance=stance: ctx.actions.lead_stance(squad, stance))
        probe.metric(f"call_ok_{stance}", bool(answer and answer.get("ok")))
        probe.metric(f"stance_after_{stance}", (answer or {}).get("after"))
        probe.wait(WATCH_S)
        probe.metric(f"moved_{stance}", moved(start, center_of(probe, squad)))
        ctx.screenshot(f"stance-{index}-{stance}")
    return ctx.result()
