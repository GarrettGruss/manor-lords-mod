"""Probe for lead 1.3 (unit growth with spawnCompleteUnit) of the change spike-community-mod-leads, issue #280.

Research tool, not in the regular suite:
    uv run python harness\\run.py --scenario probe-lead-growth --slot auto
A new AI lord with one army starts a challenge. The probe counts squads and units of the lord, calls spawnCompleteUnit three
times, waits, and counts again. The metrics give the army size before and after. It never calls a save function.
"""

from runlib.leadprobe import ENEMY_TEMPLATE, Probe, start_war

NAME = "probe-lead-growth"
LIMIT_S = 400
HIDDEN = True
LONG_REASON = "The army marches during about 40 game seconds."
CALLS = 3
WATCH_S = 10


def lord_squads(probe: Probe, lord: int) -> list:
    state = probe.attempt("lords_state", lambda: probe.ctx.actions.lords_state(log=0))
    rows = (state or {}).get("lords", [])
    return rows[lord - 1].get("squads", []) if len(rows) >= lord else []


def run(ctx) -> dict:
    probe = Probe(ctx)
    lord, squads = start_war(probe, "Lead Growth Baron", defenders=0)
    if not squads:
        return ctx.result()
    probe.attempt("challenge", lambda: ctx.actions.lord_challenge(lord))
    probe.wait(WATCH_S)
    rows_before = lord_squads(probe, lord)
    ids_before = [row["id"] for row in rows_before]
    probe.metric("squads_before", len(ids_before))
    probe.metric("units_before", sum(row["alive"] for row in rows_before))
    spawned = probe.attempt("spawnCompleteUnit", lambda: ctx.actions.lead_spawn_unit(lord, ENEMY_TEMPLATE, CALLS, 0, 0))
    probe.metric("spawn_calls_ok", len((spawned or {}).get("squads", [])))
    probe.wait(WATCH_S)
    rows_after = lord_squads(probe, lord)
    ids_after = [row["id"] for row in rows_after]
    probe.metric("squads_after", len(ids_after))
    probe.metric("units_after", sum(row["alive"] for row in rows_after))
    probe.metric("new_squads_seen", len(set(ids_after) - set(ids_before)))
    ctx.screenshot("growth-after")
    return ctx.result()
