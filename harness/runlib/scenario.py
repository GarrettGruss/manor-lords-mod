"""Scenario registry and the bridge setup.

A scenario is a Python module in `harness/scenarios/`. It defines:
  NAME     the scenario name (default: the file name with "_" replaced by "-")
  LIMIT_S  the hard time limit for the whole scenario, in seconds
  LONG_REASON  required when LIMIT_S is above LONG_LIMIT_S (300 s): why the scenario needs so much time
  HIDDEN   True for test scenarios. They are not listed unless asked for.
  EXCLUSIVE  True if the scenario needs the screen or the real mouse or keyboard for long. A suite runs it with no other game.
  run(ctx) the function. It gets a ScenarioContext and returns ctx.result().
"""

from __future__ import annotations

import importlib
import importlib.util
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
# A limit above LONG_LIMIT_S is for a soak or a multi-year run. It needs a written reason (LONG_REASON in the module).
# MAX_LIMIT_S fits a 2-game-year soak: 730 days at the measured 2.5 game s per wall s is about 11700 s, plus the boot.
LONG_LIMIT_S = 300.0
MAX_LIMIT_S = 13500.0
# The limits of the other phases (preflight 60, deploy 120, launch 60, boot 240, collect 60, teardown 30) and some room.
RUN_OVERHEAD_S = 600.0
MIN_RUN_TIMEOUT_S = 900.0


@dataclass(frozen=True)
class ScenarioInfo:
    limit_s: float
    hidden: bool = False
    summary: str = ""
    long_reason: str = ""
    exclusive: bool = False


SCENARIOS: dict[str, Callable] = {}
SCENARIO_INFO: dict[str, ScenarioInfo] = {}
SCENARIO_SOURCE: dict[str, Path] = {}  # the file that defines each discovered scenario


def check_limit(name: str, limit_s: float, long_reason: str = "") -> None:
    """Refuse a limit that is not positive, above MAX_LIMIT_S, or above LONG_LIMIT_S without a reason."""
    if not 0 < limit_s <= MAX_LIMIT_S:
        raise ValueError(f"Scenario {name!r}: LIMIT_S {limit_s} must be above 0 and at most {MAX_LIMIT_S:g} s.")
    if limit_s > LONG_LIMIT_S and not long_reason.strip():
        raise ValueError(
            f"Scenario {name!r}: LIMIT_S {limit_s:g} s is above {LONG_LIMIT_S:g} s. "
            "A long scenario needs a LONG_REASON text that says why."
        )


def register(name: str, limit_s: float = DEFAULT_LIMIT_S, hidden: bool = False, summary: str = "",
             long_reason: str = "", exclusive: bool = False) -> Callable:
    def add(function):
        if name in SCENARIOS:
            raise ValueError(f"Scenario {name!r} is registered twice.")
        check_limit(name, limit_s, long_reason)
        SCENARIOS[name] = function
        SCENARIO_INFO[name] = ScenarioInfo(limit_s, hidden, summary, long_reason, exclusive)
        return function

    return add


def get_scenario(name: str) -> Callable:
    if name not in SCENARIOS:
        raise ValueError(f"Unknown scenario {name!r}. Known scenarios: {sorted(list_scenarios())}.")
    return SCENARIOS[name]


def get_limit_s(name: str) -> float:
    info = SCENARIO_INFO.get(name)
    return info.limit_s if info else DEFAULT_LIMIT_S


def is_exclusive(name: str) -> bool:
    info = SCENARIO_INFO.get(name)
    return bool(info and info.exclusive)


def run_timeout_s(name: str, floor_s: float = MIN_RUN_TIMEOUT_S) -> float:
    """How long a launcher may wait for run.py on this scenario: the scenario limit plus the other phases.

    The suite runner and run_series.py use it, so the kill timer of the launcher never ends a long scenario
    before its own limit does.
    """
    return max(floor_s, get_limit_s(name) + RUN_OVERHEAD_S)


def list_scenarios(include_hidden: bool = False) -> dict[str, ScenarioInfo]:
    return {
        name: info
        for name, info in sorted(SCENARIO_INFO.items())
        if include_hidden or not info.hidden
    }


def _register_module(module, source: Path) -> None:
    """Register the scenario of one module. The same file twice is ignored. Another file with the same name fails."""
    name = getattr(module, "NAME", module.__name__.rsplit(".", 1)[-1].replace("_", "-"))
    if name in SCENARIOS:
        if SCENARIO_SOURCE[name] == source:
            return
        raise ValueError(f"Scenario {name!r} is defined twice: {SCENARIO_SOURCE[name]} and {source}. Scenario names must be unique.")
    summary = (module.__doc__ or "").strip().splitlines()[0:1]
    register(name, module.LIMIT_S, getattr(module, "HIDDEN", False), summary[0] if summary else "",
             getattr(module, "LONG_REASON", ""), getattr(module, "EXCLUSIVE", False))(module.run)
    SCENARIO_SOURCE[name] = source


def load_scenario_modules(package: str = "scenarios") -> None:
    """Import every module of the scenarios package and register it."""
    harness_dir = str(REPO_ROOT / "harness")
    if harness_dir not in sys.path:
        sys.path.insert(0, harness_dir)
    package_module = importlib.import_module(package)
    for module_info in pkgutil.iter_modules(package_module.__path__):
        module = importlib.import_module(f"{package}.{module_info.name}")
        _register_module(module, Path(module.__file__).resolve())


def mod_scenario_files(mod_root: Path) -> list[Path]:
    """The scenario files of all mods: mod/<Name>/scenarios/**/*.py (files that start with _ are helpers)."""
    return sorted(path for path in mod_root.glob("*/scenarios/**/*.py") if not path.name.startswith("_"))


def load_mod_scenarios(mod_root: Path = REPO_ROOT / "mod") -> None:
    """Import and register the scenarios that a mod keeps beside its own files."""
    for path in mod_scenario_files(mod_root):
        relative = path.relative_to(mod_root).with_suffix("")
        module_name = "modscenario_" + "_".join(relative.parts)
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        _register_module(module, path.resolve())


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
load_mod_scenarios()
