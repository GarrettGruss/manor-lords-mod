"""Probe for lead 1.3 (unit growth with spawnCompleteUnit) of the change spike-community-mod-leads, issue #280.

Research tool, not in the regular suite:
    uv run python harness\\run.py --scenario probe-lead-growth --slot auto
A new AI lord with one army starts a challenge. The probe counts squads and units of the lord, calls spawnCompleteUnit three
times, waits, and counts again. The metrics give the army size before and after. It never calls a save function.
"""

from runlib.leadprobe import ENEMY_TEMPLATE, Probe, start_war, units_of

NAME = "probe-lead-growth"
LIMIT_S = 400
HIDDEN = True
LONG_REASON = "The army marches during about 40 game seconds."
CALLS = 3
WATCH_S = 10


def lord_squad_ids(probe: Probe, lord: int) -> list:
    state = probe.attempt("lords_state", lambda: probe.ctx.actions.lords_state(log=0))
    rows = (state or {}).get("lords", [])
    return [squad.get("id") for squad in rows[lord - 1].get("squads", [])] if len(rows) >= lord else []


def run(ctx) -> dict:
    probe = Probe(ctx)
    lord, squads = start_war(probe, "Lead Growth Baron", defenders=0)
    if not squads:
        return ctx.result()
    probe.attempt("challenge", lambda: ctx.actions.lord_challenge(lord))
    probe.wait(WATCH_S)
    ids_before = [i for i in lord_squad_ids(probe, lord) if i is not None]
    probe.metric("squads_before", len(ids_before))
    probe.metric("units_before", units_of(probe, ids_before))
    spawned = probe.attempt("spawnCompleteUnit", lambda: ctx.actions.lead_spawn_unit(lord, ENEMY_TEMPLATE, CALLS, 0, 0))
    probe.metric("spawn_calls_ok", len((spawned or {}).get("squads", [])))
    probe.wait(WATCH_S)
    ids_after = [i for i in lord_squad_ids(probe, lord) if i is not None]
    probe.metric("squads_after", len(ids_after))
    probe.metric("units_after", units_of(probe, ids_after))
    probe.metric("new_squads_seen", len(set(ids_after) - set(ids_before)))
    ctx.screenshot("growth-after")
    return ctx.result()
