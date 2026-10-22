"""Probe for lead 1.4 (Squad.camp and campLocation) of the change spike-community-mod-leads, issue #280.

Research tool, not in the regular suite:
    uv run python harness\\run.py --scenario probe-lead-camp --slot auto
A new AI lord with one army is at war with the player. The army waits at its waypoint. The probe reads camp, campLocation and
rallyingStatus of every squad of the lord three times while the army waits, then starts a challenge and reads two more times.
It never calls a save function.
"""

from runlib.leadprobe import Probe, start_war, lord_squad_row

NAME = "probe-lead-camp"
LIMIT_S = 400
HIDDEN = True
LONG_REASON = "The army waits and then marches during about 75 game seconds."
WAIT_READS = 3
MARCH_READS = 2
STEP_S = 15


def read_camp(probe: Probe, lord: int, label: str) -> None:
    answer = probe.attempt(f"camp {label}", lambda: probe.ctx.actions.lead_squad_camp(lord))
    rows = (answer or {}).get("rows", [])
    probe.metric(f"rows_{label}", len(rows))
    probe.metric(f"camp_set_{label}", sum(1 for row in rows if row.get("camp") not in (None, False, 0)))
    probe.metric(f"camp_location_set_{label}", sum(1 for row in rows if isinstance(row.get("camp_location"), dict)))
    centers = [center_of(probe, lord, row["squad"]) for row in rows if row.get("squad")]
    probe.note(f"centers {label}", centers=centers)


def center_of(probe: Probe, lord: int, squad: int):
    row = lord_squad_row(probe, lord, squad)
    return {"x": row["x"], "y": row["y"], "alive": row["alive"], "target": [row["target_x"], row["target_y"]]} if row else None


def run(ctx) -> dict:
    probe = Probe(ctx)
    lord, squads = start_war(probe, "Lead Camp Baron", defenders=0)
    if not squads:
        return ctx.result()
    for index in range(1, WAIT_READS + 1):
        probe.wait(STEP_S)
        read_camp(probe, lord, f"wait{index}")
    probe.attempt("challenge", lambda: ctx.actions.lord_challenge(lord))
    for index in range(1, MARCH_READS + 1):
        probe.wait(STEP_S)
        read_camp(probe, lord, f"march{index}")
    return ctx.result()
