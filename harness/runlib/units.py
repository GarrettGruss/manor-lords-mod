"""Helpers for the unit census that the mod HarnessActions returns (spec 10, spike S3). Pure functions, no game.

A census is the dict that the command `units_census` answers:
{"units", "by_side", "by_role", "by_squad_type", "by_state", "by_region", "loot", "squads", "sample", "ms"}.
Sides: player, ai, bandit, civil. Raiders and bandits are both "bandit".
"""

from __future__ import annotations

# Measured in the real game (spec 10, spike S2): one bandit squad or one raider squad is 18 units.
SQUAD_UNITS = 18
# spawnEliteRaiders added 54 units (3 squads) in the probe.
ELITE_RAID_UNITS = 54


def side_count(census: dict, side: str) -> int:
    return census["by_side"].get(side, 0)


def dead_count(census: dict) -> int:
    return census["by_state"].get("dead", 0)


def loot_total(census: dict) -> int:
    return census["loot"]["total"]


def loot_max(census: dict) -> int:
    """The most goods one living unit carries. Use it for the per-raider cap check (criterion R2)."""
    return census["loot"]["max"]


def squads_of_side(census: dict, side: str) -> list[dict]:
    return [squad for squad in census["squads"] if squad["side"] == side]


def squad_regions(census: dict, side: str) -> list[str]:
    """The region of each squad of one side (a squad without living units has no region)."""
    return [squad["region"] for squad in squads_of_side(census, side) if squad.get("region")]
