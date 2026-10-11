"""Casualties by unit type in controlled fights, as numbers for an A/B suite (spec 10, spike C1, criterion C1).

One run fights ROUNDS times: one player squad against one bandit squad, both of a chosen template, the bandit squad 2500 units away.
The run reports the mean loss rate of each side and the loss ratio as metrics. A suite compares variants (`harness/suites/counters-ab.json`).
The variant options are `run.py --env COUNTERS_PLAYER=<template> --env COUNTERS_BANDIT=<template> --env COUNTERS_ROUNDS=<n>`.
"""

from runlib import battle
from runlib.fights import START_GAP, run_fight

NAME = "counters-ab"
DESCRIPTION = "Fights of one player squad against one bandit squad of chosen unit templates; metrics: loss rate of each side and the loss ratio."
COVERS = ["C1"]  # horse units do not exist in the base game data: the method covers the templates that do (see spike-C1.md)
LIMIT_S = 300

DEFAULT_PLAYER = battle.SPEAR
DEFAULT_BANDIT = battle.SWORD
DEFAULT_ROUNDS = 3
MAX_ROUNDS = 5
MIN_SQUAD_UNITS = 10
MIN_CASUALTIES = 3   # both sides together; fewer means the squads did not meet


def options(ctx) -> tuple[str, str, int]:
    player = battle.check_name("COUNTERS_PLAYER", ctx.variant_option("COUNTERS_PLAYER", DEFAULT_PLAYER))
    bandit = battle.check_name("COUNTERS_BANDIT", ctx.variant_option("COUNTERS_BANDIT", DEFAULT_BANDIT))
    text = ctx.variant_option("COUNTERS_ROUNDS", str(DEFAULT_ROUNDS))
    if not text.isdigit() or not 1 <= int(text) <= MAX_ROUNDS:
        raise ValueError(f"COUNTERS_ROUNDS must be a whole number from 1 to {MAX_ROUNDS}, got {text!r}")
    return player, bandit, int(text)


def one_round(ctx, number: int, player: str, bandit: str) -> dict:
    expect = ctx.expect
    ctx.actions.clear_battle()
    ctx.actions.spawn_units("player", player)
    ctx.actions.spawn_units("bandit", bandit, dx=START_GAP)
    fight = run_fight(ctx)
    state = fight.state
    label = f"round {number}"
    expect.at_least(f"{label}: player units at the start", battle.initial(state, "player"), MIN_SQUAD_UNITS)
    expect.at_least(f"{label}: bandit units at the start", battle.initial(state, "bandit"), MIN_SQUAD_UNITS)
    expect.at_least(f"{label}: casualties of both sides", battle.casualties(state, "player") + battle.casualties(state, "bandit"), MIN_CASUALTIES)
    expect.record(f"{label}: the fight ended", fight.finished, fight.reason, "not a timeout")
    return {"player_loss_rate": battle.casualty_rate(state, "player"), "bandit_loss_rate": battle.casualty_rate(state, "bandit"),
            "loss_ratio": battle.casualty_ratio(state, "bandit", "player"), "wall_s": fight.wall_s,
            "player_casualties": battle.casualties(state, "player"), "bandit_casualties": battle.casualties(state, "bandit")}


def mean(rounds: list[dict], key: str) -> float:
    return sum(item[key] for item in rounds) / len(rounds)


def run(ctx) -> dict:
    player, bandit, rounds_wanted = options(ctx)
    ctx.log.info(f"fights: player {player} against bandit {bandit}, {rounds_wanted} rounds")
    rounds = [one_round(ctx, number, player, bandit) for number in range(1, rounds_wanted + 1)]
    ctx.actions.clear_battle()
    for key in ("player_loss_rate", "bandit_loss_rate", "loss_ratio", "player_casualties", "bandit_casualties"):
        ctx.metric(key, round(mean(rounds, key), 4))
    ctx.metric("fight_wall_s", round(mean(rounds, "wall_s"), 1))
    ctx.notes.append(f"{player} vs {bandit}: player loss rate {mean(rounds, 'player_loss_rate'):.2f}, bandit {mean(rounds, 'bandit_loss_rate'):.2f}")
    return ctx.result()
