"""Load and check a suite file: harness/suites/<name>.json (spec 08)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from runlib import paks
from runlib.extra_env import EnvOptionError, check_env_entry

SUITES_DIR = Path(__file__).resolve().parent.parent / "suites"
ENTRY_KEYS = {"scenario", "repeat", "fixture", "optional", "variants", "expect"}
VARIANT_KEYS = {"name", "paks", "env"}
EXPECT_KEYS = {"metric", "direction", "min_rel_diff"}
DIRECTIONS = ("lower", "higher")
VARIANT_NAME = re.compile(r"^[A-Za-z0-9_-]{1,30}$")
DEFAULT_VARIANT_NAME = "default"
SUITE_KEYS = {"name", "scenarios", "time_budget_s", "flake_retries"}


class SuiteFileError(ValueError):
    """The suite file is missing or wrong. The message says what to fix."""


@dataclass(frozen=True)
class Variant:
    """One side of an A/B test: harness paks to install and extra game environment variables."""

    name: str = DEFAULT_VARIANT_NAME
    paks: tuple[str, ...] = ()
    env: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Expectation:
    """A pass or fail rule for an A/B result: the metric of a later variant must differ from the first in a direction."""

    metric: str
    direction: str  # "lower" or "higher": where the later variant must be, compared with the first
    min_rel_diff: float  # the relative difference of the medians must be at least this large


@dataclass(frozen=True)
class SuiteEntry:
    scenario: str
    repeat: int = 1
    fixture: str | None = None
    # An optional entry is skipped, not failed, when its scenario does not exist yet.
    optional: bool = False
    # An empty tuple means one implicit variant named "default" (the format before A/B variants).
    variants: tuple[Variant, ...] = ()
    expect: Expectation | None = None

    @property
    def has_variants(self) -> bool:
        return bool(self.variants)

    @property
    def run_variants(self) -> tuple[Variant | None, ...]:
        """What the runner loops over. None is the implicit default variant: no extra run.py options."""
        return self.variants or (None,)


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


def parse_variant(data, where: str) -> Variant:
    if not isinstance(data, dict):
        raise SuiteFileError(f"{where}: must be an object.")
    _check_unknown_keys(data, VARIANT_KEYS, where)
    name = data.get("name")
    if not isinstance(name, str) or not VARIANT_NAME.fullmatch(name):
        raise SuiteFileError(f"{where}: 'name' must be 1 to 30 characters from A-Z a-z 0-9 _ -, got {name!r}.")
    pak_names = data.get("paks", [])
    if not isinstance(pak_names, list):
        raise SuiteFileError(f"{where}: 'paks' must be a list of pak names.")
    env = data.get("env", {})
    if not isinstance(env, dict):
        raise SuiteFileError(f"{where}: 'env' must be an object of text values.")
    non_text = [key for key, value in env.items() if not isinstance(value, str)]
    if non_text:
        raise SuiteFileError(f"{where}: 'env' values must be text. Fix: {non_text}.")
    try:
        checked_paks = tuple(paks.check_name(pak) for pak in pak_names)
        for key, value in env.items():
            check_env_entry(key, value)
    except (paks.PakError, EnvOptionError) as error:
        raise SuiteFileError(f"{where}: {error}.") from error
    return Variant(name=name, paks=checked_paks, env=dict(env))


def parse_variants(data, where: str) -> tuple[Variant, ...]:
    if not isinstance(data, list) or not data:
        raise SuiteFileError(f"{where}: 'variants' must be a non-empty list.")
    variants = tuple(parse_variant(item, f"{where}, variants[{index}]") for index, item in enumerate(data))
    names = [variant.name for variant in variants]
    if len(set(names)) != len(names):
        raise SuiteFileError(f"{where}: variant names must be unique, got {names}.")
    return variants


def parse_expect(data, where: str, variant_count: int) -> Expectation:
    if not isinstance(data, dict):
        raise SuiteFileError(f"{where}: 'expect' must be an object.")
    _check_unknown_keys(data, EXPECT_KEYS, f"{where}, expect")
    if variant_count < 2:
        raise SuiteFileError(f"{where}: 'expect' needs at least two variants.")
    metric, direction, minimum = data.get("metric"), data.get("direction"), data.get("min_rel_diff", 0.0)
    if not isinstance(metric, str) or not metric:
        raise SuiteFileError(f"{where}, expect: 'metric' must be a non-empty string.")
    if direction not in DIRECTIONS:
        raise SuiteFileError(f"{where}, expect: 'direction' must be one of {list(DIRECTIONS)}, got {direction!r}.")
    if isinstance(minimum, bool) or not isinstance(minimum, (int, float)) or minimum < 0:
        raise SuiteFileError(f"{where}, expect: 'min_rel_diff' must be a number >= 0, got {minimum!r}.")
    return Expectation(metric=metric, direction=direction, min_rel_diff=float(minimum))


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
    variants = parse_variants(data["variants"], where) if "variants" in data else ()
    expect = parse_expect(data["expect"], where, len(variants)) if "expect" in data else None
    return SuiteEntry(scenario=scenario, repeat=repeat, fixture=fixture, optional=optional, variants=variants, expect=expect)


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
