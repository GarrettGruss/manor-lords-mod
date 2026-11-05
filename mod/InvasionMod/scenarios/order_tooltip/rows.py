"""Order tooltip: the Public Order tooltip shows the mod order terms as rows and the mod order in the header (game paused).

The tooltip opens when the real mouse rests on the order icon (spike #422), so this scenario needs a visible window and runs alone.
It saves nothing. Run on the default fixture.
"""

import time

from runlib import osinput

NAME = "order-tooltip-rows"
LIMIT_S = 600
EXCLUSIVE = True  # real mouse input
LONG_REASON = "The tooltip opens about 1 s after the real cursor rests on the icon, and the scenario opens it several times."
PREFIX = "InvasionMod."
ICON = (0.711, 0.065)  # the order icon in the top right group, as a fraction of the window
AWAY = (0.9, 0.6)
KEEP = 57  # the manor
WOOD, PLANKS, RUBBLE = 16, 17, 15  # the Keep costs 10 wood, 15 planks and 10 rubble


def bandits(ctx) -> dict:
    return ctx.mod.command(PREFIX + "bandits_state")


def tooltip(ctx) -> dict:
    return ctx.mod.command(PREFIX + "order_tooltip_state")


def open_tooltip(ctx, wanted_opens: int) -> dict:
    """Move the cursor away and back, wait until the mod rows show for open number `wanted_opens`."""
    ctx.hover_with_mouse(*AWAY)
    time.sleep(0.6)
    ctx.hover_with_mouse(*ICON)
    ctx.run_until(lambda: tooltip(ctx)["applied"] >= wanted_opens, 20, what="the mod rows in the tooltip")
    time.sleep(0.3)
    return tooltip(ctx)


def manor_built(ctx) -> bool:
    return any(module["built"] for module in ctx.actions.manor_state()["modules"])


def place_manor_site(ctx) -> None:
    """A Keep construction site, placed with the real mouse (the game must run for it)."""
    for good in (WOOD, PLANKS, RUBBLE):
        ctx.actions.give_item(good, 100)
    ctx.actions.place_building(KEEP)


def check_manor_rows(ctx) -> None:
    """The manor term counts only for a built manor: no Manor row for no manor and for a site, a green row for a built manor."""
    had_manor = manor_built(ctx)
    ctx.metric("manor_at_start", int(had_manor))
    if not had_manor:
        place_manor_site(ctx)
        ctx.time.pause()
        ctx.check("the Keep is a construction site, not built", not manor_built(ctx), ctx.actions.manor_state())
        ctx.mod.command(PREFIX + "bandits_set_order", value=50)
        tick = ctx.mod.command(PREFIX + "bandits_tick_now")["last_tick"]
        ctx.check("a site gives manor term 0", tick["manor_built"] is False and tick["manor_term"] == 0, tick)
        seen = open_tooltip(ctx, tooltip(ctx)["applied"] + 1)
        time.sleep(1.5)
        ctx.screenshot("tooltip-no-manor")
        ctx.check("no Manor row without a built manor", not any(row.startswith("Manor") for row in seen["rows"]), seen["rows"])
        ctx.actions.finish_manor_site(KEEP)
    ctx.check("the manor is built", manor_built(ctx), ctx.actions.manor_state())
    ctx.mod.command(PREFIX + "bandits_set_order", value=50)
    tick = ctx.mod.command(PREFIX + "bandits_tick_now")["last_tick"]
    ctx.check("a built manor gives manor term 10", tick["manor_built"] is True and tick["manor_term"] == 10, tick)


def run(ctx) -> dict:
    osinput.Win32Input().bring_to_front(ctx.game_window()["hwnd"])
    ctx.time.set_speed(1)
    check_manor_rows(ctx)
    ctx.time.pause()
    first = tooltip(ctx)
    ctx.check("the tooltip hook is set", first["hooked"], first)

    ctx.mod.command(PREFIX + "bandits_set_order", value=50)
    forced = ctx.mod.command(PREFIX + "bandits_tick_now")
    tick = forced["last_tick"]
    order = forced["mod_order"]
    seen = open_tooltip(ctx, first["applied"] + 1)
    time.sleep(1.5)  # the tooltip frame draws about 1 s after the open
    ctx.screenshot("tooltip-after-tick")
    ctx.check("the header is the mod order", seen["header"] == f"{order}%", [seen["header"], order])
    ctx.check("the Manor row has the manor term", f"Manor | +{tick['manor_term']}" in seen["rows"], seen["rows"])
    homeless = tick["homeless_term"]
    ctx.check("the Homeless row matches the homeless term", (f"Homeless families | -{homeless}" in seen["rows"]) == (homeless > 0), [homeless, seen["rows"]])
    ctx.check("no native row is in the list", all(row.split(" | ")[0] in ("Manor", "Homeless families", "Left for banditry") for row in seen["rows"]), seen["rows"])

    again = open_tooltip(ctx, seen["applied"] + 1)
    ctx.check("a second open shows the same rows with no duplicates", again["rows"] == seen["rows"], [seen["rows"], again["rows"]])

    ctx.mod.command(PREFIX + "bandits_leave_now", count=1)
    left = open_tooltip(ctx, again["applied"] + 1)
    time.sleep(1.5)
    ctx.screenshot("tooltip-after-leave")
    ctx.check("the Left for banditry row shows after a leave", any(row.startswith("Left for banditry | +25") for row in left["rows"]), left["rows"])

    ctx.mod.command(PREFIX + "bandits_tick_now")
    after = open_tooltip(ctx, left["applied"] + 1)
    ctx.check("the Left for banditry row is gone after the next tick", not any(row.startswith("Left for banditry") for row in after["rows"]), after["rows"])
    ctx.check("the header follows the mod order", after["header"] == f"{bandits(ctx)['mod_order']}%", [after["header"], bandits(ctx)["mod_order"]])
    ctx.check("no error was logged", after.get("last_error") is None, after)
    ctx.metric("rows_after_leave", len(left["rows"]))
    return ctx.result()
