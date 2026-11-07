"""Order tooltip: the revolt counter and the blocked item (change add-order-tooltip-revolt-timer).

Run on the fixture `playtest-noai` (five housed families, unarmed homes, no Outlaws pawn at the start):
  uv run python harness/run.py --scenario order-tooltip-revolt-timer --fixture playtest-noai --slot 1 --max-runs 1000
The tooltip opens when the real mouse rests on the order icon (spike #422), so this scenario needs a visible window and runs alone.
It saves nothing. Three states, each with a picture:
  1. No timer: no counter and no blocked item.
  2. A timer with 2 of 4 homes armed: the counter and the blocked item `Revolt blocked: 2 of 4 armed homes`.
  3. A timer with all homes armed: the counter, and no blocked item.
It also measures the cost of the armed count (first read and cached read).
"""

import time

from runlib import osinput

NAME = "order-tooltip-revolt-timer"
LIMIT_S = 900
EXCLUSIVE = True  # real mouse input
LONG_REASON = "The Outlaws pawn needs game time at the start, and the tooltip opens about 1 s after the real cursor rests on the icon."
PREFIX = "InvasionMod."
ICON = (0.711, 0.065)  # the order icon in the top right group, as a fraction of the window
AWAY = (0.9, 0.6)
SPEED = 3
SPEAR, SHIELD = 133, 271
CACHE_S = 3


def command(ctx, name: str, **args) -> dict:
    return ctx.mod.command(PREFIX + name, **args)


def bandits(ctx) -> dict:
    return command(ctx, "bandits_state")


def tooltip(ctx) -> dict:
    return command(ctx, "order_tooltip_state")


def open_tooltip(ctx, wanted_opens: int) -> dict:
    ctx.hover_with_mouse(*AWAY)
    time.sleep(0.6)
    ctx.hover_with_mouse(*ICON)
    ctx.run_until(lambda: tooltip(ctx)["applied"] >= wanted_opens, 20, what="the mod rows in the tooltip")
    time.sleep(1.5)  # the tooltip frame draws about 1 s after the open
    return tooltip(ctx)


def names(seen: dict) -> list:
    return [row.split(" | ")[0] for row in seen["rows"]]


def warm_up(ctx) -> None:
    for attempt in range(4):
        try:
            ctx.time.run_game_seconds(2, speed=SPEED)
            return
        except Exception as error:  # TimeControlError
            ctx.log.info(f"warm-up {attempt} failed: {error}")
            ctx.popups()
    raise RuntimeError("the game clock did not start")


def wait_for_pawn(ctx) -> None:
    ctx.run_until(lambda: bandits(ctx)["outlaws"]["ready"], 90, what="ensure_outlaw_pawn at the start")
    for _ in range(12):  # the camp cleanup needs game time
        if not bandits(ctx)["outlaws"]["camp_cleanup"]:
            break
        ctx.time.run_game_seconds(20, speed=SPEED)


def run(ctx) -> dict:
    osinput.Win32Input().bring_to_front(ctx.game_window()["hwnd"])
    warm_up(ctx)
    wait_for_pawn(ctx)
    ctx.time.pause()
    start = bandits(ctx)
    ctx.check("the Outlaws pawn exists", start["bandit_pawn"] is True, start["outlaws"])
    families = start["families"]
    needed = min(6, families - 1)
    ctx.metric("families", families)
    first = tooltip(ctx)
    ctx.check("the tooltip hook is set", first["hooked"], first)

    # 1. No timer.
    command(ctx, "bandits_set_order", value=80)
    command(ctx, "bandits_tick_now")
    command(ctx, "bandits_set_order", value=80)
    s1 = bandits(ctx)
    ctx.check("state 1: no timer runs", s1["timer"]["active"] is False, s1["timer"])
    seen = open_tooltip(ctx, first["applied"] + 1)
    ctx.screenshot("tooltip-no-timer")
    ctx.check("state 1: no counter and no blocked item", not any(n.startswith(("Peasants revolt", "Revolt blocked")) for n in names(seen)), seen["rows"])

    # 2. A timer, too few armed homes: the blocked item.
    command(ctx, "bandits_stock_homes", good=SPEAR, amount=2, homes=2)
    armed2 = command(ctx, "bandits_homes")["valid"]  # two families may share a home
    command(ctx, "bandits_set_order", value=10)
    command(ctx, "bandits_set_timer_days_left", days=40)
    s2 = bandits(ctx)
    ctx.check("state 2: the timer runs with 40 days left", s2["timer"]["active"] and s2["timer"]["days_left"] == 40, s2["timer"])
    time.sleep(CACHE_S + 0.5)  # the armed count of earlier reads is stale
    cost_first = command(ctx, "bandits_revolt_status")
    cost_cached = command(ctx, "bandits_revolt_status")
    ctx.metric("armed_count_cpu_ms_first", round(cost_first["cpu_ms"], 3))
    ctx.metric("armed_count_cpu_ms_cached", round(cost_cached["cpu_ms"], 3))
    time.sleep(CACHE_S + 0.5)
    seen = open_tooltip(ctx, seen["applied"] + 1)
    ctx.screenshot("tooltip-timer-blocked")
    counter = [n for n in names(seen) if n.startswith("Peasants revolt")]
    flag = [n for n in names(seen) if n.startswith("Revolt blocked")]
    ctx.check("state 2: the counter shows 40 days", counter == ["Peasants revolt in 40 days"], seen["rows"])
    ctx.check("state 2: the blocked item shows the armed count", flag == [f"Revolt blocked: {armed2} of {needed} armed homes"], seen["rows"])
    ctx.check("state 2: the blocked item is below the counter", names(seen).index(flag[0]) == names(seen).index(counter[0]) + 1, seen["rows"])

    # 3. A timer, all homes armed: no blocked item.
    command(ctx, "bandits_stock_homes", good=SPEAR, amount=2, homes=families)
    command(ctx, "bandits_stock_homes", good=SHIELD, amount=1, homes=families)
    ctx.check("all homes are armed", command(ctx, "bandits_homes")["valid"] == families, families)
    time.sleep(CACHE_S + 0.5)
    seen = open_tooltip(ctx, seen["applied"] + 1)
    ctx.screenshot("tooltip-timer-possible")
    ctx.check("state 3: the counter shows 40 days", "Peasants revolt in 40 days" in names(seen), seen["rows"])
    ctx.check("state 3: no blocked item", not any(n.startswith("Revolt blocked") for n in names(seen)), seen["rows"])
    ctx.check("no error was logged", seen.get("last_error") is None, seen)
    return ctx.result()
