"""Load and check a suite file: harness/suites/<name>.json (spec 08)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

SUITES_DIR = Path(__file__).resolve().parent.parent / "suites"
ENTRY_KEYS = {"scenario", "repeat", "fixture", "optional"}
SUITE_KEYS = {"name", "scenarios", "time_budget_s", "flake_retries"}


class SuiteFileError(ValueError):
    """The suite file is missing or wrong. The message says what to fix."""


@dataclass(frozen=True)
class SuiteEntry:
    scenario: str
    repeat: int = 1
    fixture: str | None = None
    # An optional entry is skipped, not failed, when its scenario does not exist yet.
    optional: bool = False


@dataclass(frozen=True)
class Suite:
    name: str
    entries: list[SuiteEntry]
    time_budget_s: float
    flake_retries: int


def _check_unknown_keys(data: dict, allowed: set[str], where: str) -> None:
    unknown = sorted(set(data) - allowed)
    if unknown:
        raise SuiteFileError(f"{where}: unknown key(s) {unknown}. Allowed keys: {sorted(allowed)}.")


def _integer(value, where: str, minimum: int) -> int:
    # bool is a subclass of int, so it is refused by name.
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise SuiteFileError(f"{where}: must be an integer >= {minimum}, got {value!r}.")
    return value


def parse_entry(data, index: int, suite_name: str) -> SuiteEntry:
    where = f"suite {suite_name!r}, scenarios[{index}]"
    if not isinstance(data, dict):
        raise SuiteFileError(f"{where}: must be an object.")
    _check_unknown_keys(data, ENTRY_KEYS, where)
    scenario = data.get("scenario")
    if not isinstance(scenario, str) or not scenario:
        raise SuiteFileError(f"{where}: 'scenario' must be a non-empty string.")
    fixture = data.get("fixture")
    if fixture is not None and (not isinstance(fixture, str) or not fixture):
        raise SuiteFileError(f"{where}: 'fixture' must be a non-empty string when present.")
    optional = data.get("optional", False)
    if not isinstance(optional, bool):
        raise SuiteFileError(f"{where}: 'optional' must be true or false.")
    repeat = _integer(data.get("repeat", 1), f"{where}, 'repeat'", 1)
    return SuiteEntry(scenario=scenario, repeat=repeat, fixture=fixture, optional=optional)


def parse_suite(data, expected_name: str | None = None) -> Suite:
    if not isinstance(data, dict):
        raise SuiteFileError("The suite file must hold one JSON object.")
    _check_unknown_keys(data, SUITE_KEYS, "suite file")
    name = data.get("name")
    if not isinstance(name, str) or not name:
        raise SuiteFileError("suite file: 'name' must be a non-empty string.")
    if expected_name is not None and name != expected_name:
        raise SuiteFileError(f"suite file: 'name' is {name!r} but the file is called {expected_name!r}.")
    scenarios = data.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        raise SuiteFileError(f"suite {name!r}: 'scenarios' must be a non-empty list.")
    budget = data.get("time_budget_s")
    if isinstance(budget, bool) or not isinstance(budget, (int, float)) or budget <= 0:
        raise SuiteFileError(f"suite {name!r}: 'time_budget_s' must be a number > 0, got {budget!r}.")
    retries = _integer(data.get("flake_retries", 0), f"suite {name!r}, 'flake_retries'", 0)
    entries = [parse_entry(item, index, name) for index, item in enumerate(scenarios)]
    return Suite(name=name, entries=entries, time_budget_s=float(budget), flake_retries=retries)


def load_suite(name: str, suites_dir: Path = SUITES_DIR) -> Suite:
    path = Path(suites_dir) / f"{name}.json"
    if not path.is_file():
        known = sorted(item.stem for item in Path(suites_dir).glob("*.json"))
        raise SuiteFileError(f"Suite file {path} does not exist. Known suites: {known}.")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise SuiteFileError(f"Suite file {path} is not valid JSON: {error}.") from error
    return parse_suite(data, expected_name=name)
