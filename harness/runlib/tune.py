"""Client side of the unit tuning commands (spec 28): tune_state, tune_set, tune_reset, spawn and preset export.

It talks to the command folder of a running game (`runs/<id>/commands`). It does not start the game.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .commands import CommandChannel, CommandError

SIDES = ("player", "bandit", "ai_lord", "other")
STATS = ("att", "def", "block", "armorPierce", "morale", "charge")
TEMPLATES = ("spearMilitia", "militiaFoot", "bowMilitia", "Brigands", "retinue_tier3", "mercenary_infantry", "mercenary_spearmen")
MAX_SQUADS = 6


def is_live_run(run: Path) -> bool:
    """A run can take commands when it has a commands folder or reached READY. The folder appears only with the first command."""
    return (run / "commands").is_dir() or (run / "ready.marker").is_file()


def find_newest_run(runs_dir: Path) -> Path:
    """The newest run folder that can take commands. Fail with a clear message if there is none."""
    candidates = [p for p in Path(runs_dir).iterdir() if p.is_dir() and is_live_run(p)] if Path(runs_dir).is_dir() else []
    if not candidates:
        raise CommandError(f"no run with a commands folder or ready.marker in {runs_dir}. Start one with: uv run python harness/run.py --scenario noop --keep-open")
    return max(candidates, key=lambda p: p.stat().st_mtime)


def resolve_run(runs_dir: Path, run_id: str | None) -> Path:
    if run_id is None:
        return find_newest_run(runs_dir)
    run = Path(runs_dir) / run_id
    if not is_live_run(run):
        raise CommandError(f"run {run_id} has no commands folder and no ready.marker in {runs_dir}")
    return run


class TuneClient:
    def __init__(self, run_dir: Path, timeout_s: float = 10.0):
        self.run_dir = Path(run_dir)
        self._channel = CommandChannel(self.run_dir / "commands", timeout_s=timeout_s)
        # The mod waits for the number after its last answer. Continue after the highest request in the folder.
        numbers = [int(p.stem) for p in (self.run_dir / "commands").glob("*.json") if p.stem.isdigit()]
        self._channel._number = max(numbers, default=0)

    def state(self) -> dict:
        return self._channel.send("tune_state")

    def set(self, side: str, field: str, value: float) -> dict:
        return self._channel.send("tune_set", side=side, field=field, value=value)

    def reset(self, side: str | None = None, field: str | None = None) -> dict:
        fields = {k: v for k, v in (("side", side), ("field", field)) if v is not None}
        return self._channel.send("tune_reset", **fields)

    def apply_values(self, values: dict[str, dict[str, float]]) -> list[dict]:
        """values: side -> field -> number. Sends one tune_set for each pair."""
        return [self.set(side, field, number) for side, fields in values.items() for field, number in fields.items()]

    def spawn_fight(self, groups: list[dict]) -> list[dict]:
        """groups: dicts with side, template, count (squads), dx, dy. Sends one spawn_units for each group."""
        answers = []
        for group in groups:
            if not 1 <= group["count"] <= MAX_SQUADS:
                raise CommandError(f"count must be 1 to {MAX_SQUADS}, got {group['count']}")
            answers.append(self._channel.send("spawn_units", side=group["side"], template=group["template"],
                                              count=group["count"], dx=group.get("dx", 0), dy=group.get("dy", 0)))
        return answers


def overrides_to_preset(overrides: list[dict], run_id: str) -> dict:
    """Turn the override rows of tune_state into {side: {field: value}}. Squad overrides keep their scope key."""
    values: dict[str, dict[str, float]] = {}
    for row in overrides:
        scope = row["scope"].split(":", 1)[1] if row["scope"].startswith("side:") else row["scope"]
        values.setdefault(scope, {})[row["field"]] = row["value"]
    return {"created": datetime.now(timezone.utc).isoformat(timespec="seconds"), "run": run_id, "overrides": values}


def export_preset(overrides: list[dict], run_id: str, folder: Path, name: str) -> Path:
    safe = "".join(c for c in name if c.isalnum() or c in "-_") or "preset"
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{safe}.json"
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(overrides_to_preset(overrides, run_id), indent=2) + "\n", encoding="utf-8")
    temp.replace(path)
    return path
