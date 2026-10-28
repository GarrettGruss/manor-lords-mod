"""M02 iteration 06, G1 to G5: the great raid runs a wave, then the relief army and the final battle.

Options (run.py --env): INVASION_DIFFICULTY (1 to 3, default 1). It saves nothing.
It measures game days per wall second before the waves, with 15 squads, and with the 15 + 15 + final squads.
"""

import re
import time

NAME = "invasion-great-raid-waves"
DESCRIPTION = "The great raid spawns waves, the relief army and the final army; the scenario measures the speed with them."
LIMIT_S = 1500
SPEED = 3
LONG_REASON = "Three timed stretches of game days at speed 3 with up to 55 squads on the map."
MEASURE_DAYS = 3
WAVE = re.compile(r"INVASION great wave (\d+) day=\d+ squads=(\d+)")
RELIEF = re.compile(r"INVASION great relief day=\d+ squads=(\d+) spawned=(\w+)")
FINAL = re.compile(r"INVASION great final day=\d+ squads=(\d+)")
BORDER = re.compile(r"INVASION great (wave \d+|final) border side=(\w+) at=(-?\d+),(-?\d+) distance=(\d+) direction=([\w-]+)")
MIN_SPAWN_DISTANCE = 30000


def log_text(ctx) -> str:
    log = ctx.run_dir / "mod.log"
    return log.read_text(encoding="utf-8", errors="replace") if log.exists() else ""


def great(ctx) -> dict:
    return ctx.mod.command("InvasionMod.invasion_great_state")


def run_day(ctx) -> None:
    # A spotted army drops the game to speed 1 (change update-spawn-from-map-border: the armies now walk in and are spotted on the way).
    for attempt in range(1, 6):
        ctx.popups()
        try:
            ctx.time.run_game_days(1, speed=SPEED)
            return
        except Exception as error:  # TimeControlError: the clock did not move
            ctx.log.info(f"day failed ({error}); attempt {attempt} of 5, closing pop-ups and trying again")
    ctx.popups()
    ctx.time.run_game_days(1, speed=SPEED)


def measure(ctx, label: str) -> float:
    start = time.monotonic()
    for _ in range(MEASURE_DAYS):
        run_day(ctx)
    rate = MEASURE_DAYS / (time.monotonic() - start)
    ctx.metric(f"days_per_second_{label}", round(rate, 3))
    ctx.log.info(f"speed {label}: {rate:.3f} game days per wall second")
    return rate


def run(ctx) -> dict:
    difficulty = int(ctx.variant_option("INVASION_DIFFICULTY", "1"))
    ctx.mod.command("InvasionMod.invasion_set_difficulty", value=difficulty)
    ctx.run_until(lambda: great(ctx)["day"] is not None, 30, what="the game day")
    measure(ctx, "baseline")

    ctx.mod.command("InvasionMod.invasion_great_force_start")
    ctx.run_until(lambda: great(ctx)["wave"] >= 1, 60, what="wave 1")
    waves = [tuple(int(v) for v in m.groups()) for m in map(WAVE.search, log_text(ctx).splitlines()) if m]
    ctx.check("G1 wave 1 has 15 squads", (1, 15) in waves, waves)
    measure(ctx, "wave15")

    for _ in range(difficulty - 1):
        ctx.mod.command("InvasionMod.invasion_great_skip_wait")
        before = great(ctx)["wave"]
        ctx.run_until(lambda: great(ctx)["wave"] > before, 60, what="the next wave")
    ctx.check("G1 exactly difficulty waves", great(ctx)["wave"] == difficulty, great(ctx))

    ctx.mod.command("InvasionMod.invasion_great_skip_wait")
    ctx.run_until(lambda: great(ctx)["phase"] >= 2, 60, what="the relief army and the final army")
    text = log_text(ctx)
    relief = [m.groups() for m in map(RELIEF.search, text.splitlines()) if m]
    final = [int(m.group(1)) for m in map(FINAL.search, text.splitlines()) if m]
    expected = {1: 15, 2: 8, 3: 0}[difficulty]
    ctx.check("G2 relief squads match the difficulty", relief and int(relief[0][0]) == expected, relief)
    ctx.check("G2 the relief army spawned", relief and relief[0][1] == "true", relief)
    ctx.check("G3 the final army has the configured 25 squads", final == [25], final)
    borders = [(m.group(1), int(m.group(5)), m.group(6)) for m in map(BORDER.search, text.splitlines()) if m]
    ctx.log.info(f"border points: {borders}")
    ctx.check("G6 every wave and the final army has a border point", len(borders) == difficulty + 1, borders)
    ctx.check("G6 no army starts within 30000 units of the manor", all(distance >= MIN_SPAWN_DISTANCE for _, distance, _ in borders), borders)
    measure(ctx, "wave_relief_final")
    ctx.check("G5 the game still answers with all squads on the map", great(ctx)["phase"] in (2, 3), great(ctx))
    ctx.metric("phase_end", great(ctx)["phase"])
    return ctx.result()
