"""The real-game gate (spec 19): a release needs a passing real run with the same mod files.

A real run writes runs/<id>/mod_files.json (the SHA-256 of every file under mod/) and names it in
summary.environment.mod_files. A fake run has no such file, so it never counts.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

from .files import mod_files


class GateError(Exception):
    """A gate scenario has no matching passing real run."""


@dataclass
class RunInfo:
    run_id: str
    scenario: str
    verdict: str
    started: str
    game_build: str | None
    file_hashes: dict[str, str]


@dataclass
class GateResult:
    scenario: str
    run_id: str
    started: str
    notes: list[str] = field(default_factory=list)


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def current_hashes(mod_root: Path, mod_name: str, shared: list[str]) -> dict[str, str]:
    """Hashes of the release source files, keyed like mod_files.json: path relative to mod/."""
    folders = [mod_root / mod_name] + [mod_root / "shared" / name for name in shared]
    return {path.relative_to(mod_root).as_posix(): sha256_of(path) for folder in folders for path in mod_files(folder)}


def _read_run(run_dir: Path) -> RunInfo | None:
    """A real run as RunInfo, or None for a folder that is not a real run."""
    try:
        summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
        name = summary.get("environment", {}).get("mod_files")
        hashes = json.loads((run_dir / name).read_text(encoding="utf-8")) if name else None
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(hashes, dict):
        return None
    environment = summary["environment"]
    return RunInfo(run_dir.name, str(summary.get("scenario")), str(summary.get("verdict")), str(summary.get("started", "")),
                   environment.get("game_build"), hashes)


def real_runs(runs_root: Path) -> list[RunInfo]:
    runs = [_read_run(folder) for folder in sorted(runs_root.glob("*")) if (folder / "summary.json").is_file()]
    return sorted((run for run in runs if run), key=lambda run: run.started)


def _differences(run: RunInfo, wanted: dict[str, str]) -> list[str]:
    return sorted(path for path, digest in wanted.items() if run.file_hashes.get(path) != digest)


def check_scenario(scenario: str, runs: list[RunInfo], wanted: dict[str, str], game_build: str | None) -> GateResult:
    """The latest passing run of `scenario` whose hashes match. Raise GateError with the reason and the fix."""
    same_scenario = [run for run in runs if run.scenario == scenario]
    passing = [run for run in same_scenario if run.verdict == "pass"]
    fix = f"Run it: uv run python harness/run.py --scenario {scenario}"
    if not same_scenario:
        raise GateError(f"gate scenario '{scenario}': no real run found. {fix}")
    if not passing:
        raise GateError(f"gate scenario '{scenario}': {len(same_scenario)} real run(s), none passed (latest: {same_scenario[-1].run_id} "
                        f"{same_scenario[-1].verdict}). {fix}")
    matching = [run for run in passing if not _differences(run, wanted)]
    if not matching:
        latest = passing[-1]
        changed = _differences(latest, wanted)
        raise GateError(f"gate scenario '{scenario}': the latest passing run {latest.run_id} used other mod files "
                        f"({len(changed)} differ, for example {', '.join(changed[:3])}). {fix}")
    if game_build:
        on_build = [run for run in matching if run.game_build == game_build]
        if not on_build:
            raise GateError(f"gate scenario '{scenario}': the matching run {matching[-1].run_id} ran on game build "
                            f"{matching[-1].game_build}, but mod.json tested.game_build is {game_build}. {fix}")
        matching = on_build
    best = matching[-1]
    return GateResult(scenario, best.run_id, best.started)
