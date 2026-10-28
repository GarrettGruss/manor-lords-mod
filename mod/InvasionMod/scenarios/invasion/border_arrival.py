"""Change update-spawn-from-map-border: a lord raid comes in from the map border, shows its direction, and starts at arrival.

Checks: the border point is outside the playable square and at least 30000 units from the manor; the direction notice names the
side; the tracker reports the raid as marching (no leave rule) and then as arrived within the march limit; the squads end near the
manor. Options (run.py --env): INVASION_DIFFICULTY (1 to 3, default 2). It saves nothing.
"""

import re
import time

from runlib import osinput

NAME = "invasion-border-arrival"
DESCRIPTION = "A lord raid spawns at the map border, the banner names its direction, the raid starts at arrival."
LIMIT_S = 900
SPEED = 3
LONG_REASON = "The army marches about 3 to 6 game days from the edge; at speed 3 this takes a few minutes."
MIN_SPAWN_DISTANCE = 30000
MARCH_LIMIT_DAYS = 12
BORDER = re.compile(r"INVASION (\S+) border side=(\w+) at=(-?\d+),(-?\d+) distance=(\d+) direction=([\w-]+)")
APPROACH = re.compile(r"INVASION approach banner: .*? from the ([\w-]+)")
SQUARE = (-89459, 84174, -89040, 84593)  # Jagged_Cliffs map edge (spike B); a different map would need its own numbers


def log_text(ctx) -> str:
    log = ctx.run_dir / "mod.log"
    return log.read_text(encoding="utf-8", errors="replace") if log.exists() else ""


def raids(ctx) -> list[dict]:
    return ctx.mod.command("InvasionMod.raid_behavior_state")["raids"]


def shot(ctx, name: str, settle: float = 1.0) -> None:
    osinput.Win32Input().bring_to_front(ctx.game_window()["hwnd"])
    time.sleep(settle)
    ctx.screenshot(name)


def look_at(ctx, x: float, y: float) -> bool:
    """Centre the camera (the player pawn follows it). The trace can miss next to the cliffs: try a few points around."""
    for dx, dy in ((0, 0), (4000, 0), (0, 4000), (-4000, 0), (0, -4000)):
        try:
            ctx.bridge.centre_camera_on(x + dx, y + dy)
            return True
        except RuntimeError as error:
            ctx.log.info(f"camera at ({x + dx}, {y + dy}) failed: {error}")
    return False


def run_day(ctx) -> None:
    ctx.popups()
    try:
        ctx.time.run_game_days(1, speed=SPEED)
    except Exception as error:  # TimeControlError: the clock did not move
        ctx.log.info(f"day failed ({error}); closing pop-ups and trying again")
        ctx.popups()
        ctx.time.run_game_days(1, speed=SPEED)


def run(ctx) -> dict:
    difficulty = int(ctx.variant_option("INVASION_DIFFICULTY", "2"))
    ctx.mod.command("InvasionMod.invasion_set_difficulty", value=difficulty)
    ctx.run_until(lambda: ctx.mod.command("InvasionMod.invasion_plan_now")["raid_day"] > 0, 30, what="the raid plan")
    ctx.mod.command("InvasionMod.invasion_set_size", size="medium")
    ctx.time.set_speed(1)  # slow: the picture of the banner and of the army at the edge must come before the army walks away
    ctx.mod.command("InvasionMod.invasion_force_next")
    deadline = time.time() + 60
    while time.time() < deadline and not APPROACH.search(log_text(ctx)):
        time.sleep(0.1)
    ctx.time.pause()
    sides = [m.groups() for m in map(BORDER.search, log_text(ctx).splitlines()) if m]
    ctx.check("a border point was chosen", len(sides) >= 1, sides)
    if not sides:
        return ctx.result()
    _, side, x, y, distance, direction = sides[0]
    x, y, distance = int(x), int(y), int(distance)
    outside = x < SQUARE[0] or x > SQUARE[1] or y < SQUARE[2] or y > SQUARE[3]
    ctx.check("the border point is outside the playable square", outside, [x, y])
    ctx.check("the border point is at least 30000 units from the manor", distance >= MIN_SPAWN_DISTANCE, distance)
    ctx.log.info(f"border side={side} direction={direction} at=({x},{y}) distance={distance}")
    banner = APPROACH.search(log_text(ctx))
    ctx.check("the banner text names the direction", banner is not None and banner.group(1) == direction, [banner and banner.group(1), direction])
    look_at(ctx, x, y)
    shot(ctx, "army-at-the-edge", 0.5)
    ctx.time.set_speed(1)
    for number in range(1, 13):  # the game shows its own messages first; one of these pictures shows the notice
        shot(ctx, f"direction-banner-{number}", 0.5)
    ctx.time.pause()

    rows = raids(ctx)
    ctx.check("the raid is tracked and marching", len(rows) == 1 and rows[0].get("marching") is True, rows)
    ctx.check("no leave reason while marching", rows and rows[0].get("leave_reason") is None and rows[0].get("leaving") is False, rows)
    spawn_day = rows[0]["spawn_day"] if rows else None
    days = 0
    while rows and rows[0].get("marching") and days < MARCH_LIMIT_DAYS:
        run_day(ctx)
        days += 1
        rows = raids(ctx)
    ctx.check("the raid arrived", rows and rows[0].get("marching") is False, rows)
    if rows:
        ctx.check_range("march days from spawn to arrival", rows[0]["arrival_day"] - spawn_day, 1, 8)
        ctx.check("the raid starts at arrival", rows[0]["start_day"] == rows[0]["arrival_day"], rows[0])
        ctx.metric("march_days", rows[0]["arrival_day"] - spawn_day)
        ctx.metric("living_at_arrival", rows[0]["living"])
    for _ in range(2):  # the vanguard arrives first; the squad closes up within two more days
        run_day(ctx)
    look_at(ctx, -43956, -63097)  # the player pawn follows the camera: distance_to_player is the distance to the camera
    time.sleep(1.0)
    state = ctx.actions.lords_state(log=0)
    mine = [lord for lord in state.get("lords", []) if lord.get("name") == "Hussite Raiders"]
    near = [q for lord in mine for q in lord["squads"] if q.get("distance_to_player") is not None and q["distance_to_player"] <= 15000]
    ctx.check("squads stand near the manor after arrival", len(near) >= 1, [q.get("distance_to_player") for lord in mine for q in lord["squads"]])
    shot(ctx, "army-at-the-manor", 0.5)
    ctx.ensure_alive("border arrival")
    return ctx.result()
