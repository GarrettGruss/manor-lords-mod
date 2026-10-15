"""Collect crash reports of a game that crashed after its run ended (for example a `--keep-open` run)."""
from __future__ import annotations

import dataclasses
import json
from pathlib import Path

from . import fixtures
from .game import GameInstall
from .phases import GAME_RECORD_FILE, copy_new_crash_dirs, copy_new_dumps


class LateCrashError(Exception):
    pass


def read_game_record(run_path: Path) -> dict:
    path = run_path / GAME_RECORD_FILE
    if not path.is_file():
        raise LateCrashError(f"{path} is missing; the run is older than the game record, or the game never started")
    return json.loads(path.read_text(encoding="utf-8"))


def collect_late_crashes(install: GameInstall, run_path: Path) -> dict:
    """Copy new crash folders and UE4SS dumps of the run's game into runs/<id>/crash/. Already copied items are skipped."""
    record = read_game_record(run_path)
    crash_dir = run_path / "crash"
    crash_dir.mkdir(exist_ok=True)
    since, pid, notes = record["run_started_epoch"], record["pid"], []
    searched = [install]
    if record.get("appdata_dir"):
        # The UE crash handler writes into the REAL folder, but the private one is searched too (same as the collect phase).
        searched.insert(0, dataclasses.replace(install, saved_dir=fixtures.saved_dir_of(Path(record["appdata_dir"]))))
    copied: list[str] = []
    for where in searched:
        copied += copy_new_crash_dirs(where, crash_dir, since, notes, pid)
    copied += copy_new_dumps(install, crash_dir, since)
    return {"copied": copied, "notes": notes, "pid": pid}
