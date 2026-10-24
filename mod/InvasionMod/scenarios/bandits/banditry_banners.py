"""Bandits: the three banners (timer start, warning 30 game days before the leave, leave) show once each, with pictures.

The timer is moved with `bandits_set_timer_days_left`. The banners are counted by their log lines in mod.log.
Run on the default fixture and on `--fixture playtest-noai`. It saves nothing.
"""

import time

from runlib import osinput

NAME = "bandits-banditry-banners"
LIMIT_S = 900
SPEED = 3
LONG_REASON = "About 3 game days at speed 3 (13 s each) in short steps, plus the start."
PREFIX = "InvasionMod."



def state(ctx) -> dict:
    return ctx.mod.command(PREFIX + "bandits_state")


def log_text(ctx) -> str:
    log = ctx.run_dir / "mod.log"
    return log.read_text(encoding="utf-8", errors="replace") if log.exists() else ""


def count(ctx, text: str) -> int:
    return log_text(ctx).count(text)


def shot_when_logged(ctx, name: str, text: str, total: int, trigger=None) -> None:
    """Run live, take the picture the moment the log line shows (the banner fades in a few seconds), then pause."""
    ctx.time.set_speed(1)
    if trigger:
        trigger()
    deadline = time.time() + 120
    while time.time() < deadline and count(ctx, text) < total:
        time.sleep(0.1)
    osinput.Win32Input().bring_to_front(ctx.game_window()["hwnd"])
    time.sleep(0.3)
    ctx.screenshot(name)
    ctx.time.pause()


def run(ctx) -> dict:
    start_before = count(ctx, "BANDITS timer started")
    shot_when_logged(ctx, "banner-timer-start", "BANDITS timer started", start_before + 1,
                     lambda: ctx.mod.command(PREFIX + "bandits_set_order", value=20))
    ctx.check("one timer start banner", count(ctx, "BANDITS timer started") == start_before + 1, log_text(ctx)[-400:])

    ctx.mod.command(PREFIX + "bandits_set_timer_days_left", days=31)
    shot_when_logged(ctx, "banner-warning", "BANDITS warning", 1)
    warned = count(ctx, "BANDITS warning")
    ctx.check("one warning banner at 30 game days before the leave", warned == 1 and state(ctx)["timer"]["days_left"] <= 30, [warned, state(ctx)["timer"]])
    ctx.time.run_game_seconds(20, speed=SPEED)
    ctx.check("the warning does not repeat", count(ctx, "BANDITS warning") == 1, count(ctx, "BANDITS warning"))

    ctx.mod.command(PREFIX + "bandits_set_timer_days_left", days=1)
    leaves_before = state(ctx)["leaves"]
    shot_when_logged(ctx, "banner-leave", "BANDITS leave day=", leaves_before + 1)
    after = state(ctx)
    ctx.check("the villagers left once", after["leaves"] == leaves_before + 1, after)
    ctx.check("one leave line in the log", count(ctx, "BANDITS leave day=") == 1, count(ctx, "BANDITS leave day="))
    ctx.metric("families_left", after["last_leave"]["removed"])
    return ctx.result()
