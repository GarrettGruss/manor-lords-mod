"""A small client for the commands and metrics of RaidStandIn, and an independent copy of its calendar rules.

The scenarios use `RaidMod` to talk to the mod through `ctx.mod`. They use `season_of` and `ALLOWED_SEASONS` as the oracle
for the season rules: the test must not ask the mod what the rule is. The numbers here follow the header of
mod/RaidStandIn/Scripts/main.lua.
"""

from __future__ import annotations

import zlib

PREFIX = "RaidStandIn."
MOD_NAME = "RaidStandIn"
YEAR_DAYS = 360
SEASON_DAYS = 90
SEASONS = ("spring", "summer", "autumn", "winter")
ALLOWED_SEASONS = {"cuman": {"summer"}, "norse": {"spring", "autumn"}}
DOMINANT_UNIT = {"cuman": "horse_archers", "norse": "shock_infantry"}
OBJECTIVES = {"cuman": "loot", "norse": "burn"}
RETREAT_REASONS = ("leader_dead", "morale_break", "full_loot", "timer_end")
SEED_RANGE = 10000


def season_of(day: int) -> str:
    return SEASONS[(day % YEAR_DAYS) // SEASON_DAYS]


def seed_base_for(ctx) -> int:
    """A base seed that differs between runs but is fixed for one run. It is logged, so a failed run can be repeated."""
    base = zlib.crc32(ctx.run_dir.name.encode("utf-8")) % SEED_RANGE
    ctx.log.info(f"seed base {base} (from the run folder name {ctx.run_dir.name})")
    return base


def dominant_unit(composition: dict) -> str:
    return max(sorted(composition), key=lambda unit: composition[unit])


def distinct_units(composition: dict) -> int:
    return len([count for count in composition.values() if count > 0])


class RaidMod:
    """Commands and metrics of RaidStandIn. `ctx` is the scenario context."""

    def __init__(self, ctx):
        self._ctx = ctx

    def __call__(self, name: str, **args):
        return self._ctx.mod.command(PREFIX + name, **args)

    def refusal(self, name: str, **args):
        return self._ctx.mod.refusal(PREFIX + name, **args)

    def metric(self, name: str):
        return self._ctx.mod.metric(PREFIX + name)

    def start(self, **config) -> dict:
        """Reset the mod and set its config. Random leader death is off unless the caller asks, so the test controls every retreat."""
        self("reset")
        settings = {"leader_death_percent": 0, "announce_days": 1, **config}
        return self("configure", **settings)

    def arrive(self, faction: str = "cuman", days: int = 2, **config) -> dict:
        """A clean mod with one raid that has arrived. Returns the active raid."""
        self.start(**config)
        self("set_day", day=100)
        self("set_timer", days=days, faction=faction)
        self("advance_days", days=days)
        return self("current_raid")

    def auto_run(self, tier: int, seed: int, days: int) -> list[dict]:
        """A clean mod that schedules its own raids for `days` toy days. Returns the raid log."""
        self("reset")
        self("configure", tier=tier, seed=seed, auto=True)
        self("advance_days", days=days)
        return self("raid_log", count=100)["raids"]
