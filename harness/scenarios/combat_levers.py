"""One fight with a lever applied, as numbers for an A/B suite (spec 25, issue #129).

One run is one fight: a player group against a bandit group. The lever comes from the variant options (`run.py --env KEY=VALUE`):
  LEVER_PLAYER, LEVER_BANDIT      unit template names (default spearMilitia, Brigands)
  LEVER_BANDIT2   a second bandit template (one squad), for group sizes such as 1.5 times
  LEVER_PLAYER_SQUADS, LEVER_BANDIT_SQUADS   number of squads (default 1 and 1)
  LEVER_SET_PLAYER, LEVER_SET_BANDIT   live stat writes after the spawn, "def=0,block=0"
  LEVER_ITEMS   item writes before the spawn, "164:def:50;271:block:30" (restored at the end)
  LEVER_HOOK    "1": count SMUnit:CombatHit calls during the fight (observe only)
Metrics: casualties and loss rates of both sides, player_won, fight_wall_s, hook_calls.
"""

from runlib import battle
from runlib.fights import START_GAP, run_fight

NAME = "combat-levers"
DESCRIPTION = "One fight with a combat lever applied (live stat write, item write or hook probe); metrics: casualties, winner, fight time."
COVERS = []
LIMIT_S = 240

MAX_SQUADS = 3


def parse_pairs(text: str) -> list[tuple[str, float]]:
    pairs = []
    for part in filter(None, (item.strip() for item in text.split(","))):
        name, _, value = part.partition("=")
        pairs.append((battle.check_name("stat", name), float(value)))
    return pairs


def parse_items(text: str) -> list[tuple[str, str, float]]:
    rows = []
    for part in filter(None, (item.strip() for item in text.split(";"))):
        row, field, value = part.split(":")
        rows.append((row, battle.check_name("field", field), float(value)))
    return rows


def squads_option(ctx, name: str, default: int) -> int:
    text = ctx.variant_option(name, str(default))
    if not text.isdigit() or not 1 <= int(text) <= MAX_SQUADS:
        raise ValueError(f"{name} must be a whole number from 1 to {MAX_SQUADS}, got {text!r}")
    return int(text)


def write_items(ctx, rows: list[tuple[str, str, float]]) -> list[tuple[str, str, float]]:
    original = []
    for row, field, value in rows:
        before = ctx.actions.datatable_read(row, field, table="items")
        original.append((row, field, before))
        ctx.actions.datatable_write(row, field, value, table="items")
        ctx.log.info(f"item {row} {field}: {before} -> {value}")
    return original


def apply_stats(ctx, side: str, text: str) -> None:
    for field, value in parse_pairs(text):
        ctx.actions.set_unit_stat(side, field, value)


def run(ctx) -> dict:
    player = battle.check_name("LEVER_PLAYER", ctx.variant_option("LEVER_PLAYER", battle.SPEAR))
    bandit = battle.check_name("LEVER_BANDIT", ctx.variant_option("LEVER_BANDIT", "Brigands"))
    bandit2 = ctx.variant_option("LEVER_BANDIT2", "")
    if bandit2:
        battle.check_name("LEVER_BANDIT2", bandit2)
    player_squads = squads_option(ctx, "LEVER_PLAYER_SQUADS", 1)
    bandit_squads = squads_option(ctx, "LEVER_BANDIT_SQUADS", 1)
    items = parse_items(ctx.variant_option("LEVER_ITEMS", ""))
    hook = ctx.variant_option("LEVER_HOOK", "0") == "1"
    expect = ctx.expect
    ctx.actions.clear_battle()
    original = write_items(ctx, items)
    try:
        ctx.actions.spawn_units("player", player, count=player_squads)
        ctx.actions.spawn_units("bandit", bandit, count=bandit_squads, dx=START_GAP)
        if bandit2:
            ctx.actions.spawn_units("bandit", bandit2, count=1, dx=START_GAP)
        before = ctx.actions.unit_stats()
        ctx.log.info(f"stats before: {before['squads']}")
        apply_stats(ctx, "player", ctx.variant_option("LEVER_SET_PLAYER", ""))
        apply_stats(ctx, "bandit", ctx.variant_option("LEVER_SET_BANDIT", ""))
        after = ctx.actions.unit_stats()
        ctx.log.info(f"stats after writes: {after['squads']}")
        if hook:
            ctx.actions.combat_hook("start")
        fight = run_fight(ctx)
        if hook:
            ctx.log.info(f"combat hook: {ctx.actions.combat_hook('read')}")
            ctx.actions.combat_hook("stop")
        late = ctx.actions.unit_stats()
        ctx.log.info(f"stats at the end: {late['squads']}")
    finally:
        for row, field, value in original:
            ctx.actions.datatable_write(row, field, value, table="items")
        ctx.actions.clear_battle()
    state = fight.state
    expect.at_least("player units at the start", battle.initial(state, "player"), 10)
    expect.at_least("bandit units at the start", battle.initial(state, "bandit"), 10)
    # Two runs of the first suite had 0 casualties: the groups never met. A run like that is not a result.
    expect.at_least("casualties of both sides", battle.casualties(state, "player") + battle.casualties(state, "bandit"), 3)
    expect.record("the fight ended", fight.finished, fight.reason, "not a timeout")
    player_alive, bandit_alive = battle.alive(state, "player"), battle.alive(state, "bandit")
    for key, value in {"player_casualties": battle.casualties(state, "player"), "bandit_casualties": battle.casualties(state, "bandit"),
                       "player_loss_rate": round(battle.casualty_rate(state, "player"), 4),
                       "bandit_loss_rate": round(battle.casualty_rate(state, "bandit"), 4),
                       "player_won": 1 if player_alive > bandit_alive else 0, "fight_wall_s": round(fight.wall_s, 1),
                       "player_start": battle.initial(state, "player"), "bandit_start": battle.initial(state, "bandit")}.items():
        ctx.metric(key, value)
    ctx.notes.append(f"{player} x{player_squads} vs {bandit} x{bandit_squads}: alive {player_alive} against {bandit_alive}, {fight.reason}")
    return ctx.result()
