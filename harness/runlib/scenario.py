"""Scenario registry and the bridge setup.

A scenario is a Python module in `harness/scenarios/`. It defines:
  NAME     the scenario name (default: the file name with "_" replaced by "-")
  LIMIT_S  the hard time limit for the whole scenario, in seconds
  HIDDEN   True for test scenarios. They are not listed unless asked for.
  run(ctx) the function. It gets a ScenarioContext and returns ctx.result().
"""

from __future__ import annotations

import importlib
import os
import pkgutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .bridge_client import Bridge
from .game import GameInstall
from .runner import PhaseContext

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_LIMIT_S = 90.0


@dataclass(frozen=True)
class ScenarioInfo:
    limit_s: float
    hidden: bool = False
    summary: str = ""


SCENARIOS: dict[str, Callable] = {}
SCENARIO_INFO: dict[str, ScenarioInfo] = {}


def register(name: str, limit_s: float = DEFAULT_LIMIT_S, hidden: bool = False, summary: str = "") -> Callable:
    def add(function):
        if name in SCENARIOS:
            raise ValueError(f"Scenario {name!r} is registered twice.")
        SCENARIOS[name] = function
        SCENARIO_INFO[name] = ScenarioInfo(limit_s, hidden, summary)
        return function

    return add


def get_scenario(name: str) -> Callable:
    if name not in SCENARIOS:
        raise ValueError(f"Unknown scenario {name!r}. Known scenarios: {sorted(list_scenarios())}.")
    return SCENARIOS[name]


def get_limit_s(name: str) -> float:
    info = SCENARIO_INFO.get(name)
    return info.limit_s if info else DEFAULT_LIMIT_S


def list_scenarios(include_hidden: bool = False) -> dict[str, ScenarioInfo]:
    return {
        name: info
        for name, info in sorted(SCENARIO_INFO.items())
        if include_hidden or not info.hidden
    }


def load_scenario_modules(package: str = "scenarios") -> None:
    """Import every module of the scenarios package and register it."""
    harness_dir = str(REPO_ROOT / "harness")
    if harness_dir not in sys.path:
        sys.path.insert(0, harness_dir)
    package_module = importlib.import_module(package)
    for module_info in pkgutil.iter_modules(package_module.__path__):
        module = importlib.import_module(f"{package}.{module_info.name}")
        name = getattr(module, "NAME", module_info.name.replace("_", "-"))
        if name in SCENARIOS:
            continue
        summary = (module.__doc__ or "").strip().splitlines()[0:1]
        register(name, module.LIMIT_S, getattr(module, "HIDDEN", False), summary[0] if summary else "")(module.run)


def configure_bridge_client(ctx: PhaseContext, install: GameInstall) -> Bridge:
    """Point the Python bridge client at this run's bridge folder and return a Bridge.

    The bridge module reads its environment variables once, at the first call, and keeps the result.
    So the variables are set first, and the cached game location is cleared in case it was already used.
    """
    os.environ["UE4SS_BRIDGE_GAME_DIR"] = str(install.win64)
    os.environ["UE4SS_BRIDGE_DATA_DIR"] = str(ctx.run.bridge_dir.resolve())
    mcp_dir = str(REPO_ROOT / "mcp")
    if mcp_dir not in sys.path:
        sys.path.insert(0, mcp_dir)
    from ue4ss_bridge import server

    server._GAME = None
    return Bridge(server.one)


load_scenario_modules()
