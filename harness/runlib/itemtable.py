"""Compare `itemStats` rows read from the running game with the vanilla values (spec 09).

With no data pak the game rows equal the vanilla file. With a data pak some rows differ.
A pak test states the new values in the environment variable HARNESS_EXPECT_ITEM_ROWS,
a JSON map: {"17": {"Value": 0.75}}. Those values replace the vanilla ones for the check.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Callable

VANILLA_PATH = Path(__file__).resolve().parent.parent / "vanilla" / "itemStats.json"
EXPECT_ENV = "HARNESS_EXPECT_ITEM_ROWS"
FIELDS = ("Weight", "Value", "spoilageRate")
TOLERANCE = 1e-4


class ItemTableError(Exception):
    """The vanilla file or the expectation variable is wrong. The message says what."""


def load_vanilla(path: Path = VANILLA_PATH) -> dict:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ItemTableError(f"cannot read the vanilla file {path}: {error}") from error
    if not isinstance(data.get("rows"), dict) or not isinstance(data.get("row_count"), int):
        raise ItemTableError(f"vanilla file {path} needs 'row_count' and 'rows'")
    return data


def parse_overrides(text: str | None) -> dict[str, dict[str, float]]:
    """Parse HARNESS_EXPECT_ITEM_ROWS. An empty value means no override."""
    if not text:
        return {}
    try:
        overrides = json.loads(text)
    except ValueError as error:
        raise ItemTableError(f"{EXPECT_ENV} is not valid JSON: {error}") from error
    if not isinstance(overrides, dict):
        raise ItemTableError(f"{EXPECT_ENV} must be a JSON object: row -> field -> value")
    for row, fields in overrides.items():
        check_override_row(row, fields)
    return overrides


def check_override_row(row: str, fields) -> None:
    if not isinstance(fields, dict) or not fields:
        raise ItemTableError(f"{EXPECT_ENV}: row {row!r} needs an object of field values")
    for field, value in fields.items():
        if field not in FIELDS:
            raise ItemTableError(f"{EXPECT_ENV}: field {field!r} is not one of {list(FIELDS)}")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ItemTableError(f"{EXPECT_ENV}: {row}.{field} must be a number")


def expected_rows(vanilla: dict, overrides: dict) -> dict[str, dict[str, float]]:
    """The vanilla rows with the overrides applied. A row that is not in the vanilla file is added."""
    rows = {row: dict(fields) for row, fields in vanilla["rows"].items()}
    for row, fields in overrides.items():
        rows.setdefault(row, {}).update(fields)
    return rows


def compare_rows(expect, read: Callable[[str, str], float], rows: dict, tolerance: float = TOLERANCE) -> None:
    """Read every field of every row and record one expectation for each."""
    for row, fields in rows.items():
        for field, wanted in fields.items():
            value = read(row, field)
            expect.record(f"item {row} {field}", abs(value - wanted) <= tolerance, value, f"{wanted} +- {tolerance}")


def overrides_from_environment() -> dict:
    return parse_overrides(os.environ.get(EXPECT_ENV))
