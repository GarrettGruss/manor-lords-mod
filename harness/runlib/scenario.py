"""Scenario registry. A scenario is a function that gets the phase context and returns a result dict.

Step 3 adds real scenarios with `@register("name")`.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Callable

from .game import GameInstall, ensure_game_alive
from .runner import PhaseContext

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCENARIOS: dict[str, Callable[[PhaseContext], dict]] = {}


def register(name: str):
    def add(function):
        if name in SCENARIOS:
            raise ValueError(f"Scenario {name!r} is registered twice.")
        SCENARIOS[name] = function
        return function

    return add


def get_scenario(name: str) -> Callable[[PhaseContext], dict]:
    if name not in SCENARIOS:
        raise ValueError(f"Unknown scenario {name!r}. Known scenarios: {sorted(SCENARIOS)}.")
    return SCENARIOS[name]


def configure_bridge_client(ctx: PhaseContext, install: GameInstall) -> None:
    """Point the Python bridge client at this run's bridge folder. Set before the first bridge call."""
    os.environ["UE4SS_BRIDGE_GAME_DIR"] = str(install.win64)
    os.environ["UE4SS_BRIDGE_DATA_DIR"] = str(ctx.run.bridge_dir.resolve())
    for folder in (REPO_ROOT / "mcp", REPO_ROOT / "harness" / "tools"):
        if str(folder) not in sys.path:
            sys.path.insert(0, str(folder))


def read_clock_through_bridge(wait_seconds: float = 3.0) -> dict:
    import read_clock  # harness/tools/read_clock.py, found through configure_bridge_client

    return read_clock.read_clock(wait_seconds)


@register("noop")
def noop(ctx: PhaseContext) -> dict:
    """Placeholder. It proves that the game is alive and paused, and that the bridge works."""
    ensure_game_alive(ctx, "scenario")
    clock = read_clock_through_bridge()
    ensure_game_alive(ctx, "scenario")
    passed = bool(clock.get("ok") and clock.get("paused"))
    return {"passed": passed, "asserts": [], "note": "noop scenario", "clock": clock}
