"""Read the game state now through the bridge, in the same shape as one telemetry sample (spec 04).

A field that cannot be read is None, and its name goes into the `errors` list. A bad field never stops the snapshot.
"""

from __future__ import annotations

import time
from typing import Any, Callable

from .bridge_client import Bridge, object_path

DATE_FIELDS = {"day": "day", "month": "month", "year": "Year", "season": "Season"}
PLAYER_FIELDS = ("silver", "influence", "kingsFavour")
REGION_FIELDS = {"name": "regionName", "settled": "isSettled", "approval": "Approval", "publicOrder": "publicOrder",
                 "wealth": "regionalWealth", "food": "supplies_food"}
REGION_CALLS = {"population": "getNumTotalPopulation", "homeless": "getNumHomelessFamilies"}


class _Reader:
    """Runs reads with a guard and collects the names of failed reads."""

    def __init__(self) -> None:
        self.errors: list[str] = []

    def guard(self, label: str, read: Callable[[], Any]) -> Any:
        try:
            return read()
        except Exception as error:  # noqa: BLE001 - a bad field must not stop the snapshot
            self.errors.append(f"{label}: {str(error).splitlines()[0][-80:] if str(error) else type(error).__name__}")
            return None


def _read_region(bridge: Bridge, reader: _Reader, path: str, index: int) -> dict:
    region = {key: reader.guard(f"region{index}.{key}", lambda n=name: bridge.read_property(path, n))
              for key, name in REGION_FIELDS.items()}
    for key, function in REGION_CALLS.items():
        region[key] = reader.guard(f"region{index}.{key}", lambda f=function: bridge.call_function(path, f))
    return region


def _read_regions(bridge: Bridge, reader: _Reader, engine: str) -> list[dict]:
    refs = reader.guard("regions", lambda: bridge.read_property(engine, "regions")) or []
    paths = [path for path in (reader.guard(f"region{i}.path", lambda r=ref: object_path(r)) for i, ref in enumerate(refs, 1)) if path]
    return [_read_region(bridge, reader, path, index) for index, path in enumerate(paths, 1)]


def snapshot(ctx_or_bridge: Any) -> dict:
    """Accepts a ScenarioContext or a Bridge."""
    bridge = getattr(ctx_or_bridge, "bridge", ctx_or_bridge)
    reader = _Reader()
    engine = reader.guard("engine", bridge.engine_path)
    if engine is None:
        return {"t": int(time.time()), "clock": None, "date": {}, "player": {}, "regions": [], "errors": reader.errors}
    clock = reader.guard("clock", lambda: bridge.read_clock_value(engine))
    calendar = reader.guard("date", lambda: bridge.calendar_path(engine))
    date = {key: reader.guard(f"date.{key}", lambda n=name: bridge.read_property(calendar, n)) for key, name in DATE_FIELDS.items()} if calendar else {}
    player_path = reader.guard("player", lambda: object_path(bridge.read_property(engine, "playerRef")))
    player = {name: reader.guard(f"player.{name}", lambda n=name: bridge.read_property(player_path, n)) for name in PLAYER_FIELDS} if player_path else {}
    regions = _read_regions(bridge, reader, engine)
    return {"t": int(time.time()), "clock": clock, "date": date, "player": player, "regions": regions, "errors": reader.errors}
