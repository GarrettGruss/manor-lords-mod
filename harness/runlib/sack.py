"""Helpers for the village census that the mod HarnessActions returns (spec 10, spike S6). Pure functions, no game.

A village census is the dict that the command `sack_census` answers:
{"buildings": {"total", "standing", "rubble", "burning"}, "stock": {"total", "by_good"},
 "stores": [{"id", "type", "goods", "by_good"}], "people": {"families", "population"}, "region"}.
A store is a building that holds goods. Its id is the number at the end of the building name.
"""

from __future__ import annotations

METHODS = ("fire", "collapse")
MAX_PERCENT = 100
RUBBLE_TYPE = 75  # EBuildingType::Rubble: what a burned or collapsed building becomes


class SackError(ValueError):
    """A bad argument for a sack action."""


def share(total: int, percent: int) -> int:
    """Round half up, like the Lua side. A percent of a count is a whole number of things."""
    return int(total * percent / 100 + 0.5)


def check_percent(name: str, value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= MAX_PERCENT:
        raise SackError(f"{name} must be a whole number from 0 to {MAX_PERCENT}, got {value!r}")
    return value


def check_method(method: str) -> str:
    if method not in METHODS:
        raise SackError(f"method must be one of {METHODS}, got {method!r}")
    return method


def check_positive(name: str, value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise SackError(f"{name} must be a whole number of 1 or more, got {value!r}")
    return value


def standing(census: dict) -> int:
    return census["buildings"]["standing"]


def rubble(census: dict) -> int:
    return census["buildings"]["rubble"]


def burning(census: dict) -> int:
    return census["buildings"]["burning"]


def stock_total(census: dict) -> int:
    return census["stock"]["total"]


def families(census: dict) -> int:
    return census["people"]["families"]


def population(census: dict) -> int:
    return census["people"]["population"]


def store(census: dict, store_id: int) -> dict:
    for entry in census["stores"]:
        if entry["id"] == store_id:
            return entry
    raise KeyError(f"no store with id {store_id} in {[entry['id'] for entry in census['stores']]}")


def stores_by_size(census: dict) -> list[dict]:
    """The stores, the one with most goods first. A tie goes to the lower id."""
    return sorted(census["stores"], key=lambda entry: (-entry["goods"], entry["id"]))


def removed_share(before: int, after: int) -> float:
    """The part of `before` that is gone, as a percent. 0 when there was nothing."""
    return 0.0 if before == 0 else 100.0 * (before - after) / before
