"""Experience (combatExperience) grows in a fight, stays after a second fight and a game day, and can be written (spec 10, spike C2, criterion C2)."""

from runlib import battle
from runlib.fights import START_GAP, run_fight

NAME = "veterancy"
DESCRIPTION = "Two player squads fight a bandit squad, then a second one. Survivors (tracked by unit id) keep or raise their experience, also after a game day."
COVERS = ["C2"]
LIMIT_S = 280

DEFENDERS = battle.SPEAR
ATTACKERS = battle.SWORD
DEFENDER_SQUADS = 3     # 96 units against 24, so enough of them live through two fights (a fight is a coin toss: 32 against 32 wiped out one side)
ATTACKER_SIZE = 24      # written to the maxSize of the attacker template (criterion C3 gives the way) and restored at the end
MIN_SURVIVORS = 5
EXPERIENCE_TOLERANCE = 0.01
WRITTEN_EXPERIENCE = 25.0
DAY_SPEED = 3


def spawn_round(ctx, squads: int) -> None:
    if squads:
        ctx.actions.spawn_units("player", DEFENDERS, count=squads)
    ctx.actions.spawn_units("bandit", ATTACKERS, count=1, dx=START_GAP)


def common_units(first: dict, second: dict) -> list[int]:
    return sorted(set(battle.unit_experience(first)) & set(battle.unit_experience(second)))


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def check_fresh_units(ctx) -> None:
    state = ctx.actions.battle_state(detail=True)
    ctx.expect.equals("fresh units have no experience", battle.mean_experience(state, "player"), 0.0)
    ctx.expect.equals("fresh units: the template field does not set it", state["squads"][0]["xp_max"], 0.0)


def check_first_fight(ctx, fight) -> dict:
    expect = ctx.expect
    state = fight.state
    expect.record("the first fight ended", fight.finished, fight.reason, "not a timeout")
    expect.at_least("player casualties in fight 1", battle.casualties(state, "player"), 1)
    expect.at_least("bandit casualties in fight 1", battle.casualties(state, "bandit"), 1)
    expect.at_least("player survivors", battle.alive(state, "player"), MIN_SURVIVORS)
    expect.at_least("survivor experience after fight 1 (mean)", battle.mean_experience(state, "player"), 0.1)
    expect.at_least("survivor experience after fight 1 (most)", max(squad["xp_max"] for squad in battle.squads_of(state, "player")), 1.0)
    return state


def check_second_fight(ctx, first: dict, second: dict) -> list[int]:
    expect = ctx.expect
    common = common_units(first, second)
    expect.at_least("the same units are in both reads", len(common), MIN_SURVIVORS)
    xp1, xp2 = battle.unit_experience(first), battle.unit_experience(second)
    lost = [uid for uid in common if xp2[uid] < xp1[uid] - EXPERIENCE_TOLERANCE]
    expect.equals("no survivor lost experience in fight 2", len(lost), 0)
    before, after = mean([xp1[uid] for uid in common]), mean([xp2[uid] for uid in common])
    expect.at_least("mean experience of the same units after fight 2", after, before - EXPERIENCE_TOLERANCE)
    ctx.metric("experience_after_fight_1", before)
    ctx.metric("experience_after_fight_2", after)
    return common


def check_after_a_day(ctx, second: dict, common: list[int]) -> dict:
    # The bandits that are left would keep fighting during the day. Remove them, so a loss of experience cannot be a death.
    ctx.actions.clear_battle(side="bandit")
    ctx.time.run_game_days(1, speed=DAY_SPEED)
    later = ctx.actions.battle_state(detail=True)
    xp2, xp3 = battle.unit_experience(second), battle.unit_experience(later)
    kept = [uid for uid in common if uid in xp3]
    ctx.expect.at_least("units still alive after a game day", len(kept), MIN_SURVIVORS)
    lost = [uid for uid in kept if xp3[uid] < xp2[uid] - EXPERIENCE_TOLERANCE]
    ctx.expect.equals("no unit lost experience in a game day", len(lost), 0)
    return later


def squad_row(state: dict, squad_id: int) -> dict:
    return next(row for row in state["squads"] if row["id"] == squad_id)


def check_written_experience(ctx, state: dict) -> None:
    squad = next(squad for squad in state["squads"] if squad["side"] == "player" and squad["alive"] > 0)
    ctx.actions.set_squad_experience(squad["id"], WRITTEN_EXPERIENCE)
    written = squad_row(ctx.actions.battle_state(), squad["id"])
    ctx.expect.in_range("written experience read back", written["xp_mean"], WRITTEN_EXPERIENCE - 0.5, WRITTEN_EXPERIENCE + 0.5)
    ctx.time.run_game_seconds(10, speed=DAY_SPEED)
    row = squad_row(ctx.actions.battle_state(), squad["id"])
    ctx.expect.in_range("written experience after 10 game seconds", row["xp_mean"], WRITTEN_EXPERIENCE - 0.5, WRITTEN_EXPERIENCE + 5)


def two_fights(ctx) -> dict:
    spawn_round(ctx, DEFENDER_SQUADS)
    check_fresh_units(ctx)
    first = check_first_fight(ctx, run_fight(ctx))

    spawn_round(ctx, 0)
    second_fight = run_fight(ctx)
    ctx.expect.record("the second fight ended", second_fight.finished, second_fight.reason, "not a timeout")
    common = check_second_fight(ctx, first, second_fight.state)
    later = check_after_a_day(ctx, second_fight.state, common)
    check_written_experience(ctx, later)
    return later


def run(ctx) -> dict:
    original_size = ctx.actions.datatable_read(ATTACKERS, "maxSize", table="units")
    ctx.actions.datatable_write(ATTACKERS, "maxSize", ATTACKER_SIZE, table="units")
    try:
        two_fights(ctx)
    finally:
        ctx.actions.datatable_write(ATTACKERS, "maxSize", original_size, table="units")
        ctx.actions.clear_battle()
    return ctx.result()
