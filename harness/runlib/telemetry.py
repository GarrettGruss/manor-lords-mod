"""Read <run>/telemetry.jsonl, the file that the HarnessTelemetry mod writes (spec 04)."""

from __future__ import annotations

import json
from pathlib import Path

FILE_NAME = "telemetry.jsonl"


class TelemetryReader:
    def __init__(self, run_dir: Path):
        self.path = Path(run_dir) / FILE_NAME

    def read(self) -> list[dict]:
        """All samples so far. A missing file gives an empty list. The last line may be half written: it is skipped."""
        try:
            lines = self.path.read_text(encoding="utf-8").splitlines()
        except FileNotFoundError:
            return []
        samples = []
        for number, line in enumerate(lines):
            try:
                samples.append(json.loads(line))
            except json.JSONDecodeError:
                if number != len(lines) - 1:
                    raise ValueError(f"{self.path} line {number + 1} is not valid JSON")
        return samples

    def window(self, start_clock: float, end_clock: float) -> list[dict]:
        """The samples whose game clock is in [start_clock, end_clock]."""
        return [s for s in self.read() if isinstance(s.get("clock"), (int, float)) and start_clock <= s["clock"] <= end_clock]


SAMPLE_KEYS = ("t", "clock", "paused", "date", "player", "regions", "errors")
DATE_KEYS = ("day", "month", "year", "season")
PLAYER_KEYS = ("silver", "influence", "kingsFavour")
REGION_KEYS = ("name", "settled", "approval", "publicOrder", "wealth", "food", "population", "homeless")


def missing_fields(sample: dict) -> list[str]:
    """Names of fields that are absent or null in a sample. `paused` may be null in the first sample."""
    missing = [key for key in SAMPLE_KEYS if key not in sample or (sample[key] is None and key != "paused")]
    for group, keys in (("date", DATE_KEYS), ("player", PLAYER_KEYS)):
        missing += [f"{group}.{key}" for key in keys if (sample.get(group) or {}).get(key) is None]
    for index, region in enumerate(sample.get("regions") or [], 1):
        missing += [f"region{index}.{key}" for key in REGION_KEYS if region.get(key) is None]
    return missing
