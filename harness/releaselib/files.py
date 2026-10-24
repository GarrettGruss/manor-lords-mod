"""Which files go into a release zip, and which modules a mod really needs (spec 19)."""

from __future__ import annotations

import re
from pathlib import Path

# Modules that only the harness may use. A release must not contain them or require them.
HARNESS_ONLY = frozenset({
    "HarnessActions", "HarnessBoot", "HarnessLog", "HarnessCommands", "HarnessTelemetry", "HarnessReload",
    "HarnessAutosave", "HarnessLoadProbe", "HarnessLogTest", "UEBridge", "InvasionStandIn", "RaidStandIn",
})

# A hard dependency. `pcall(require, "X")` is an optional one and does not match this pattern.
HARD_REQUIRE = re.compile(r'(?<![\w.])require\s*\(\s*["\']([A-Za-z0-9_]+)["\']\s*\)')
LUA_COMMENT = re.compile(r"--[^\n]*")

# Files of a mod folder that stay out of the zip.
SKIP_PARTS = {"__pycache__"}

# Top-level folders of a mod that are sources for the build or the tests. They never go into a release.
NOT_RELEASED = ("data", "scenarios")


class ClosureError(Exception):
    """A mod needs a module that it does not declare, or a harness-only module."""


def hard_requires(lua_text: str) -> set[str]:
    return set(HARD_REQUIRE.findall(LUA_COMMENT.sub("", lua_text)))


def lua_files(folder: Path) -> list[Path]:
    return sorted(p for p in folder.rglob("*.lua") if not SKIP_PARTS & set(p.parts))


def mod_files(folder: Path) -> list[Path]:
    return sorted(p for p in folder.rglob("*") if p.is_file() and not SKIP_PARTS & set(p.parts))


def _requires_of(folder: Path) -> set[str]:
    found: set[str] = set()
    for path in lua_files(folder):
        found |= hard_requires(path.read_text(encoding="utf-8", errors="replace"))
    return found


def shared_closure(mod_dir: Path, shared_dir: Path, declared: list[str]) -> list[str]:
    """The shared modules the zip must hold: the declared ones and everything they require.

    Raise ClosureError when the mod or a shared module needs a harness-only module,
    needs a shared module that does not exist, or when the mod needs a shared module that it does not declare.
    """
    own = _requires_of(mod_dir)
    _refuse_harness_only(own, mod_dir.name)
    # A module that is a Lua file of the mod itself (for example config or scheduler) is not a shared module.
    local = {path.stem for path in lua_files(mod_dir)}
    undeclared = sorted(name for name in own if name not in declared and name not in local)
    if undeclared:
        raise ClosureError(f"{mod_dir.name} requires {', '.join(undeclared)} but mod.json shared does not list it")
    closure: list[str] = []
    queue = list(declared)
    while queue:
        name = queue.pop(0)
        if name in closure:
            continue
        folder = shared_dir / name
        if not folder.is_dir():
            raise ClosureError(f"shared module {name} does not exist in {shared_dir}")
        needs = _requires_of(folder)
        _refuse_harness_only(needs, name)
        closure.append(name)
        queue.extend(sorted(needs))
    return sorted(closure)


def _refuse_harness_only(names: set[str], owner: str) -> None:
    bad = sorted(names & HARNESS_ONLY)
    if bad:
        raise ClosureError(f"{owner} requires the harness-only module {', '.join(bad)}. Move the game call to ManorCore, or use pcall(require, ...) for an optional one.")
