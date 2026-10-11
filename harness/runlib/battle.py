"""Helpers for typed units, battles and mercenaries (spec 10, spikes S7, P5, C1, C2). Pure functions, no game.

A battle state is the dict that the command `battle_state` answers:
{"squads": [{"id", "side", "template", "initial", "alive", "xp_mean", "xp_max", "units"?}],
 "by_side": {side: {"initial", "alive"}}, "by_template": {"<side>:<template>": {"initial", "alive"}}, "ms"}.
`initial` is the unit count when the squad was spawned or hired. A dead unit leaves the game's unit list at once,
so casualties = initial - alive. Only squads that the mod HarnessActions spawned or hired are in the state.
"""

from __future__ import annotations

import re

SIDES = ("player", "bandit")
NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,63}$")
MAX_GROUPS = 6
MAX_OFFSET = 20000
MAX_EXPERIENCE = 1000
# Measured in the real game (spike S7): the number of units of a squad is the row field maxSize of the template,
# up to a limit of the squad shape. Templates with maxSize 32 gave 32 units, templates with maxSize 60 gave 36 (18 for Brigands).
# The scenarios therefore read the start size from the state and never assume it.

# Template rows of DT_UnitTemplates that the scenarios use (spike S7 and C1). Other rows work too: the mod checks the row exists.
SPEAR = "spearMilitia"
SWORD = "militiaFoot"
POLE = "militiaPole"
BOW = "bowMilitia"
HEAVY = "retinue_tier3"


class BattleError(ValueError):
    """A bad argument for a battle action."""


def check_name(what: str, value: str) -> str:
    if not isinstance(value, str) or not NAME_PATTERN.match(value):
        raise BattleError(f"{what} must be letters, digits and underscore (start with a letter), got {value!r}")
    return value


def check_side(side: str) -> str:
    if side not in SIDES:
        raise BattleError(f"side must be one of {SIDES}, got {side!r}")
    return side


def check_count(count: int) -> int:
    if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= MAX_GROUPS:
        raise BattleError(f"count must be a whole number from 1 to {MAX_GROUPS}, got {count!r}")
    return count


def check_offset(name: str, value: int | float) -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or abs(value) > MAX_OFFSET:
        raise BattleError(f"{name} must be a number within +-{MAX_OFFSET}, got {value!r}")
    return value


def check_experience(value: int | float) -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= MAX_EXPERIENCE:
        raise BattleError(f"value must be a number from 0 to {MAX_EXPERIENCE}, got {value!r}")
    return value


def _as_map(value) -> dict:
    """The Lua JSON encoder writes an empty table as []. A map with no entries therefore arrives as an empty list."""
    if isinstance(value, dict):
        return value
    if value == []:
        return {}
    raise BattleError(f"expected a map, got {value!r}")


def _group(state: dict, side: str, template: str | None) -> dict:
    empty = {"initial": 0, "alive": 0}
    if template is None:
        return _as_map(state["by_side"]).get(side, empty)
    return _as_map(state["by_template"]).get(f"{side}:{template}", empty)


def initial(state: dict, side: str, template: str | None = None) -> int:
    return _group(state, side, template)["initial"]


def alive(state: dict, side: str, template: str | None = None) -> int:
    return _group(state, side, template)["alive"]


def casualties(state: dict, side: str, template: str | None = None) -> int:
    group = _group(state, side, template)
    return group["initial"] - group["alive"]


def casualty_rate(state: dict, side: str, template: str | None = None) -> float:
    """Casualties as a share of the start size, 0.0 to 1.0. Zero when the group never existed."""
    group = _group(state, side, template)
    if group["initial"] == 0:
        return 0.0
    return (group["initial"] - group["alive"]) / group["initial"]


def casualty_ratio(state: dict, loser: str, winner: str, loser_template: str | None = None, winner_template: str | None = None) -> float:
    """Casualties of `loser` divided by casualties of `winner`. The winner has at least 1 casualty counted, so the ratio is defined."""
    return casualties(state, loser, loser_template) / max(1, casualties(state, winner, winner_template))


def squads_of(state: dict, side: str, template: str | None = None) -> list[dict]:
    return [squad for squad in state["squads"] if squad["side"] == side and (template is None or squad["template"] == template)]


def mean_experience(state: dict, side: str, template: str | None = None) -> float:
    """The mean combatExperience of the living units of the matching squads, weighted by the living units."""
    squads = squads_of(state, side, template)
    living = sum(squad["alive"] for squad in squads)
    if living == 0:
        return 0.0
    return sum(squad["xp_mean"] * squad["alive"] for squad in squads) / living


def unit_experience(state: dict) -> dict[int, float]:
    """Unit id -> combatExperience, from a state read with detail=True. Raises when the state has no unit rows."""
    result: dict[int, float] = {}
    for squad in state["squads"]:
        if "units" not in squad:
            raise BattleError("the state has no unit rows: read it with detail=True")
        for unit in squad["units"]:
            result[unit["uid"]] = unit["xp"]
    return result


def fight_is_over(state: dict, side_a: str, side_b: str) -> bool:
    """One side has no living units left."""
    return alive(state, side_a) == 0 or alive(state, side_b) == 0


def alive_signature(state: dict) -> tuple:
    """A value that changes when any squad loses a unit. Used to see that a fight has stopped."""
    return tuple((squad["id"], squad["alive"]) for squad in state["squads"])


# ---- mercenaries ----

def offer_names(offers: list[dict]) -> list[str]:
    return [offer["name"] for offer in offers]


def find_offer(offers: list[dict], company: str) -> dict:
    for offer in offers:
        if offer["name"] == company:
            return offer
    raise BattleError(f"company {company!r} is not on offer. Offered: {offer_names(offers)}")


# ---- unit data ----

def row_values(rows: list[dict], name: str) -> dict:
    """The number fields of one row of a `datatable_rows` answer."""
    for row in rows:
        if row["row"] == name:
            return row["values"]
    raise BattleError(f"no row named {name!r} in {[row['row'] for row in rows][:6]}...")
