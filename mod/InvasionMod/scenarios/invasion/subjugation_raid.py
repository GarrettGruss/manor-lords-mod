"""M02 iteration 03, S1 to S4: the subjugation raid (major) is planned after the first raid (the yearly roll; the test plans it at once), is large, targets the stand-in region, and does not plunder or leave.

Options (run.py --env): INVASION_DIFFICULTY (1 to 3, default 1). It saves nothing.
"""

import re
import time

from runlib import osinput

NAME = "invasion-subjugation-raid"
DESCRIPTION = "The subjugation raid is planned after the first raid, spawns large, and keeps fighting without plunder or leave."
LIMIT_S = 1500
SPEED = 3
LONG_REASON = "The first raid must end (up to 25 game days), then the subjugation raid runs 12 game days. At speed 3 this takes about 700 s."
DAY_LIMIT = 40
SUB_DAYS = 12
SPAWN = re.compile(r"INVASION spawn day=(\d+) .*kind=(\w+) target=(\S+) stand_in=(\w+)")
BANNER = re.compile(r"INVASION raid banner kind=subjugation day=(\d+) days_left=(\d+) target=(.*?) raiders=(\d+) shown=(\w+)")
BANNER_DAYS = 30


def log_lines(ctx) -> list[str]:
    log = ctx.run_dir / "mod.log"
    return log.read_text(encoding="utf-8", errors="replace").splitlines() if log.exists() else []


def raids(ctx) -> list[dict]:
    return ctx.mod.command("InvasionMod.raid_behavior_state")["raids"]


def shot(ctx, name: str, settle: float = 1.0) -> None:
    osinput.Win32Input().bring_to_front(ctx.game_window()["hwnd"])
    time.sleep(settle)
    ctx.screenshot(name)


def shot_menu(ctx, name: str) -> None:
    ctx.mod.command("InvasionMod.raid_widget_open")
    time.sleep(1.0)
    shot(ctx, name)
    ctx.mod.command("InvasionMod.raid_widget_close")


def run_day(ctx) -> None:
    ctx.popups()
    try:
        ctx.time.run_game_days(1, speed=SPEED)
    except Exception as error:  # TimeControlError: the clock did not move
        ctx.log.info(f"day failed ({error}); closing pop-ups and trying again")
        ctx.popups()
        ctx.time.run_game_days(1, speed=SPEED)


def run(ctx) -> dict:
    difficulty = int(ctx.variant_option("INVASION_DIFFICULTY", "1"))
    ctx.mod.command("InvasionMod.invasion_set_difficulty", value=difficulty)
    ctx.run_until(lambda: ctx.mod.command("InvasionMod.invasion_plan_now")["raid_day"] > 0, 30, what="the raid plan")
    ctx.mod.command("InvasionMod.invasion_set_size", size="small")
    ctx.mod.command("InvasionMod.invasion_force_next")
    ctx.run_until(lambda: len(raids(ctx)) >= 1, 30, what="the first raid record")
    ctx.run_until(lambda: ctx.mod.command("InvasionMod.invasion_plan_now", kind="subjugation")["day"] is not None and ctx.mod.command("InvasionMod.invasion_subjugation_state")["sub_day"] > 0, 30, what="the subjugation plan")
    state = ctx.mod.command("InvasionMod.invasion_subjugation_state")
    wait = state["sub_day"] - ctx.mod.command("InvasionMod.invasion_state")["day"]
    ctx.check("S1 the subjugation raid is planned 1 to 90 days ahead (the season rule)", 1 <= wait <= 90, wait)
    ctx.log.info(f"yearly plan {ctx.mod.command('InvasionMod.invasion_plan_now')}")
    shot_menu(ctx, "raid-menu-planned")
    ctx.check("S2 it is large: 3 squads x difficulty", state["squads"] == 3 * difficulty, state["squads"])
    # The season rule plans the raid 1 to 90 days ahead; the first raid can last 25 days. Move the day out so the first raid ends first.
    ctx.mod.command("InvasionMod.invasion_set_raid_days", days=45, kind="subjugation")

    days = 0
    while raids(ctx)[0]["state"] == "active" and days < DAY_LIMIT:
        run_day(ctx)
        days += 1
    ctx.check("the first raid ended before the subjugation raid", raids(ctx)[0]["state"] != "active", raids(ctx)[0]["state"])

    # update-raid-banners: one banner 30 game days before the raid. Move the raid day to 33 days ahead and run 4 days.
    ctx.mod.command("InvasionMod.invasion_set_raid_days", days=BANNER_DAYS + 3, kind="subjugation")
    # Run live and take the picture the moment the banner line is logged: the banner fades in a few seconds.
    ctx.time.set_speed(SPEED)
    deadline = time.time() + 90
    while time.time() < deadline and not any(BANNER.search(line) for line in log_lines(ctx)):
        time.sleep(0.2)
    shot(ctx, "banner-30-days", 0.1)
    ctx.time.pause()
    banners = [m.groups() for m in map(BANNER.search, log_lines(ctx)) if m]
    ctx.check("S5 one banner, 30 days before the raid, naming the target", len(banners) == 1 and int(banners[0][1]) == BANNER_DAYS, banners)
    ctx.check("S5 the stand-in target is named as you", all(target == "you" for _, _, target, _, _ in banners), banners)
    ctx.check("S5 the banner estimate equals the planned size", all(int(raiders) == state["raiders"] for _, _, _, raiders, _ in banners), [banners, state["raiders"]])
    ctx.mod.command("InvasionMod.invasion_subjugation_force_next")
    ctx.run_until(lambda: len(raids(ctx)) >= 2, 30, what="the subjugation raid record")
    for _ in range(SUB_DAYS):
        run_day(ctx)
    sub = raids(ctx)[1]
    ctx.log.info(f"subjugation raid: {sub}")
    spawns = [m.groups() for m in map(SPAWN.search, log_lines(ctx)) if m]
    ctx.check("S3 the spawn log names the kind and the stand-in target", any(kind == "subjugation" and stand == "true" for _, kind, _, stand in spawns), spawns)
    ctx.check("S3 the tracker knows the raid as subjugation", sub["kind"] == "subjugation" and sub["lord_raid"] is True, sub)
    ctx.check("S4 no plunder tick", sub["plundered"] == 0, sub["plundered"])
    ctx.check("S4 no leave reason (it fights on)", sub.get("leave_reason") is None and sub["leaving"] is False, sub.get("leave_reason"))
    ctx.metric("subjugation_initial", sub["initial"])
    ctx.metric("subjugation_living", sub["living"])
    ctx.metric("subjugation_deaths", sub["deaths"])
    return ctx.result()
