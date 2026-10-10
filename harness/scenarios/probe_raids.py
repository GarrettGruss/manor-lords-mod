"""Probe for spec 10: what the harness can observe and drive about raids, on the base game.

A research tool, not a test. It never fails on a game answer: every answer goes to `probe.jsonl` in the run folder.
Choose a group with the environment variable HARNESS_PROBE (s1, s2, s3, s5, s10). One group is one run, because a call may crash the game.
"""

import json
import os
import time

NAME = "probe-raids"
LIMIT_S = 300
HIDDEN = True

TIMER_FIELDS = ["daysUntilNextRaid", "daysSinceLastRaid", "lastBanditCampSpawnedDay", "day", "daysTotal", "Year", "Season"]


class Probe:
    def __init__(self, ctx):
        self.ctx = ctx
        self.bridge = ctx.bridge
        self.channel = ctx.actions._commands
        self.path = ctx.run_dir / "probe.jsonl"
        self.calendar = ctx.bridge.calendar_path()

    def note(self, step: str, **data) -> dict:
        entry = {"step": step, **data}
        self.ctx.log.info(f"PROBE {json.dumps(entry, default=str)[:1500]}")
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, default=str) + "\n")
        return entry

    def attempt(self, step: str, work):
        """Run `work`; record its result or its error. A game crash raises through ensure_alive."""
        self.ctx.log.info(f"PROBE start {step}")
        try:
            result = work()
            self.note(step, ok=True, result=result)
            return result
        except Exception as error:  # noqa: BLE001 - the probe records every answer
            self.ctx.ensure_alive(step)
            self.note(step, ok=False, error=str(error)[:500])
            return None

    def command(self, step: str, name: str, **fields):
        started = time.monotonic()
        result = self.attempt(step, lambda: self.channel.send(name, **fields))
        self.note(step + " wall", wall_s=round(time.monotonic() - started, 3))
        return result

    def timer(self) -> dict:
        return {name: self.bridge.read_property(self.calendar, name) for name in TIMER_FIELDS}

    def census(self, step: str, sample: int = 0):
        return self.command(step, "units_census", sample=sample)


def group_s1(probe: Probe) -> None:
    bridge, calendar = probe.bridge, probe.calendar
    probe.command("raid_state", "raid_state")
    probe.command("census baseline", "units_census", sample=5, trace=1)
    probe.note("timer start", timer=probe.timer())
    probe.attempt("write daysUntilNextRaid=50", lambda: bridge.write_property(calendar, "daysUntilNextRaid", 50))
    probe.attempt("write daysSinceLastRaid=10", lambda: bridge.write_property(calendar, "daysSinceLastRaid", 10))
    probe.note("timer after write", timer=probe.timer())
    probe.attempt("run 6 s", lambda: probe.ctx.time.run_game_seconds(6, speed=1))
    probe.note("timer after 6 s", timer=probe.timer())
    probe.attempt("run 1 day at speed 3", lambda: probe.ctx.time.run_game_days(1, speed=3))
    probe.note("timer after 1 day", timer=probe.timer())
    probe.attempt("write daysUntilNextRaid=1", lambda: bridge.write_property(calendar, "daysUntilNextRaid", 1))
    for day in range(1, 4):
        probe.attempt(f"run day {day}", lambda: probe.ctx.time.run_game_days(1, speed=3))
        probe.note(f"timer day {day}", timer=probe.timer())
        probe.census(f"census day {day}", sample=5)
    probe.attempt("write daysUntilNextRaid=0", lambda: bridge.write_property(calendar, "daysUntilNextRaid", 0))
    for day in range(4, 7):
        probe.attempt(f"run day {day}", lambda: probe.ctx.time.run_game_days(1, speed=3))
        probe.note(f"timer day {day}", timer=probe.timer())
        probe.census(f"census day {day}", sample=5)
    probe.attempt("player inbox", lambda: len(bridge.read_property(bridge.player_path(), "InBox")))


def group_s2(probe: Probe) -> None:
    probe.census("census baseline", sample=3)
    probe.command("spawn_raiders 1 squad", "spawn_raiders", squads=1)
    probe.census("census after raiders", sample=10)
    probe.command("spawn_bandit_camp", "spawn_bandit_camp")
    probe.census("census after camp", sample=3)
    probe.command("spawn_elite_raiders", "spawn_elite_raiders")
    probe.census("census after elite", sample=10)
    probe.attempt("SpawnBanditSquad", lambda: probe.bridge.call_function("first:MLCheatManager", "SpawnBanditSquad"))
    probe.census("census after bandit squad", sample=10)
    probe.attempt("SpawnRaidersOfType Raiders", lambda: probe.bridge.call_function("first:MLCheatManager", "SpawnRaidersOfType", ["Raiders"]))
    probe.census("census after cheat raiders", sample=10)


def group_s1b(probe: Probe) -> None:
    """Timer 1, then day by day: the timer, the lists that could announce a raid, the squads and where they stand."""
    bridge, calendar = probe.bridge, probe.calendar
    probe.command("raid_state", "raid_state")
    probe.command("census baseline", "units_census", sample=2)
    probe.attempt("write daysUntilNextRaid=3", lambda: bridge.write_property(calendar, "daysUntilNextRaid", 3))
    for day in range(1, 8):
        probe.attempt(f"run day {day}", lambda: probe.ctx.time.run_game_days(1, speed=3))
        probe.note(f"timer day {day}", timer=probe.timer())
        probe.command(f"raid_state day {day}", "raid_state")
        probe.census(f"census day {day}", sample=1)


def group_s5(probe: Probe) -> None:
    """Put loot on 3 bandits, kill them, and look for what the death creates."""
    probe.command("raid_state", "raid_state")
    probe.census("census baseline", sample=1)
    probe.command("set_unit_loot", "set_unit_loot", side="bandit", count=3, amount=7)
    probe.census("census with loot", sample=3)
    probe.command("kill 3 with loot", "kill_units", side="bandit", count=3, with_loot=1, actors=1)
    probe.attempt("run 5 s", lambda: probe.ctx.time.run_game_seconds(5, speed=1))
    probe.census("census after kill", sample=1)
    probe.command("kill 2 more", "kill_units", side="bandit", count=2, actors=1)
    probe.census("census after second kill", sample=1)


def measure_rate(probe: Probe, speed: int, wall_s: float = 6.0) -> dict:
    """Game clock seconds per wall second at one speed (the measure window excludes set_speed)."""
    try:
        probe.ctx.time.set_speed(speed)
    except Exception as error:  # noqa: BLE001 - the probe records a refused speed
        return {"speed": speed, "error": str(error)[:160], "game_speed_now": probe.bridge.read_game_speed(),
                "clock": probe.bridge.measure_clock(3.0)}
    first = probe.bridge.measure_clock(wall_s)
    return {"speed": speed, "game_s": first["change"], "wall_s": wall_s, "rate": round(first["change"] / wall_s, 2)}


def bridge_call_cost(probe: Probe, calls: int = 30) -> float:
    started = time.monotonic()
    for _ in range(calls):
        probe.bridge.read_clock_value()
    return round((time.monotonic() - started) / calls * 1000, 1)


def group_s10(probe: Probe) -> None:
    """Add raider squads (18 units each) in steps and measure the clock rate at 1x and 8x after each step."""
    probe.census("census baseline")
    for step in range(5):
        rates = [measure_rate(probe, 1), measure_rate(probe, 3)]
        probe.ctx.time.pause()
        census = probe.command(f"census step {step}", "units_census")
        units = census["census"]["units"] if census else None
        probe.note(f"step {step}", units=units, rates=rates, bridge_call_ms=bridge_call_cost(probe))
        if step < 4:
            probe.command(f"spawn 6 squads (step {step})", "spawn_raiders", squads=6)


GROUPS = {"s10": group_s10, "s5": group_s5, "s1": group_s1, "s1b": group_s1b, "s2": group_s2}


def run(ctx) -> dict:
    group = os.environ.get("HARNESS_PROBE", "s1")
    probe = Probe(ctx)
    probe.note("group", name=group)
    GROUPS[group](probe)
    ctx.check("probe finished", True, group)
    return ctx.result()
