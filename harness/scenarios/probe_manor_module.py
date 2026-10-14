"""Probe for issue #65 (spec 12): does the manor planner show card 123, and is a type 123 module finished by builders?

Research tool. Use fixture manor-bailey with the paks mm123data and mm123ui (--pak twice).
Modes (HARNESS_PROBE): planner (open the planner, screenshot, no commit), build (commit type 123, feed builders, watch).
It records each answer in `probe.jsonl`. It calls no save function and no unsafe command.
"""

import json
import time

from runlib.bridge_client import object_path

NAME = "probe-manor-module"
LIMIT_S = 2400
HIDDEN = True
LONG_REASON = "The probe waits several game days for builders."
MANOR_TYPE = 98
MODULE_TYPE = 123
MESH = "/Game/ManorLords/Buildings/Merged/SM_MERGED_C_SG_Gatehouse_Lv1_Ubeam"
TIMBER, RUBBLE, PLANKS = 16, 15, 17
FOODS = (30, 171)
BUILD_DAYS = 60
# Screen fractions: the gatehouse in the fixture view, then the screen centre.
DOWN_ARROW = (0.741, 0.49)  # the planner card list scroll arrow, as a fraction of the window
SCROLL_CLICKS = 0
HIDE_CARDS = (57, 58, 50)  # the cards in front of card 123 (472, the outer tower, stays)
SPOT = (13000, -51163, 2500)  # the place used in run s65-1, inside the bailey area


def note(ctx, step: str, **data) -> None:
    entry = {"step": step, **data}
    ctx.log.info(f"PROBE {json.dumps(entry, default=str)[:1800]}")
    with (ctx.run_dir / "probe.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, default=str) + "\n")


def attempt(ctx, step: str, work):
    try:
        result = work()
    except Exception as error:  # noqa: BLE001 - the probe records every answer
        ctx.ensure_alive(step)
        note(ctx, step, error=str(error)[:500])
        return None
    note(ctx, step, result=result)
    return result


def find_manor_path(ctx) -> str | None:
    found = ctx.bridge._result("objects", class_name="SMBuildingMaster", limit=60)["objects"]
    for ref in found:
        path = object_path(ref)
        data = attempt(ctx, f"data of {path[-30:]}", lambda p=path: ctx.bridge.read_property(p, "Data"))
        if isinstance(data, dict) and data.get("bType") == MANOR_TYPE:
            return path
    return None


def dump_cards(ctx) -> None:
    """Record every live buildingWidget (card): path, ID, Visibility and parent widget."""
    found = attempt(ctx, "card widgets", lambda: ctx.bridge._result("objects", class_name="buildingCardWidget_C", limit=60)["objects"])
    for ref in found or []:
        path = object_path(ref)
        if not path.startswith("/Engine/Transient"):
            continue
        fields = {name: attempt(ctx, f"{path[-28:]} {name}", lambda p=path, n=name: ctx.bridge.read_property(p, n))
                  for name in ("ID", "Visibility", "bIsEnabled")}
        note(ctx, "card", path=path[-60:], **fields)


def count_module_users(ctx, label: str) -> None:
    """The type 123 test blueprint uses the gatehouse mesh, so a new mesh user and a new manor part show the finished module."""
    attempt(ctx, f"{label} mesh users", lambda: ctx.actions._command("mesh_users", mesh="Gatehouse_Lv1_Ubeam"))
    manor_id = (ctx.actions.manor_state() or {}).get("region_manor_id")
    attempt(ctx, f"{label} manor parts count", lambda: {k: v for k, v in ctx.actions.master_parts(building=manor_id, limit=1).items()
                                                        if k in ("parts", "valid_parts", "built")})


def scroll_cards(ctx) -> None:
    """The card list is a WrapBox (no ScrollBox exists: run s65c-3). Collapse the cards in front so card 123 moves into view. Not run yet."""
    found = attempt(ctx, "cards again", lambda: ctx.bridge._result("objects", class_name="buildingCardWidget_C", limit=60)["objects"]) or []
    for ref in found:
        path = object_path(ref)
        if path.startswith("/Engine/Transient") and ctx.bridge.read_property(path, "ID") in HIDE_CARDS:
            attempt(ctx, "collapse card", lambda p=path: ctx.bridge.call_function(p, "SetVisibility", [1]))
    time.sleep(1)
    ctx.screenshot("planner_card123")


def open_planner(ctx, manor: str) -> None:
    player = ctx.bridge.player_path()
    attempt(ctx, "close popups", ctx.actions.close_popups)
    attempt(ctx, "manor_planner", lambda: ctx.actions._command("manor_planner"))
    widgets = attempt(ctx, "planner widgets", lambda: ctx.bridge._result("objects", class_name="castlePlanner_C", limit=5)["objects"])
    for ref in widgets or []:
        path = object_path(ref)
        if not path.startswith("/Engine/Transient"):
            continue
        for prop in ("Visibility", "bIsEnabled"):
            attempt(ctx, f"widget {prop}", lambda p=path, n=prop: ctx.bridge.read_property(p, n))
        attempt(ctx, "widget IsInViewport", lambda p=path: ctx.bridge.call_function(p, "IsInViewport"))
        attempt(ctx, "widget SetVisibility", lambda p=path: ctx.bridge.call_function(p, "SetVisibility", [0]))
        attempt(ctx, "widget AddToViewport", lambda p=path: ctx.bridge.call_function(p, "AddToViewport", [50]))
    dump_cards(ctx)
    time.sleep(1)
    ctx.screenshot("planner_a_paused")
    for step in range(SCROLL_CLICKS):
        attempt(ctx, f"scroll {step}", lambda: ctx.click_with_mouse(*DOWN_ARROW))
        time.sleep(1)
        ctx.screenshot(f"planner_scroll{step}")
    scroll_cards(ctx)
    attempt(ctx, "planner close", lambda: ctx.actions._command("manor_planner", close=True))


def feed_builders(ctx) -> None:
    actions = ctx.actions
    attempt(ctx, "manor slots", lambda: actions.manor_worker_slot(45, 3))
    for index in range(3):
        attempt(ctx, f"assign worker {index}", actions.manor_assign_worker)
    for good, amount in ((RUBBLE, 60), (FOODS[0], 150), (FOODS[1], 150)):
        attempt(ctx, f"give {good}", lambda g=good, a=amount: actions.give_item(g, a))
    attempt(ctx, "give timber", lambda: actions.give_item(TIMBER, 60))
    attempt(ctx, "manor put timber", lambda: actions.manor_put(TIMBER, 40))
    attempt(ctx, "more families", lambda: actions.family_add(6, adult=True))


def watch(ctx) -> None:
    for day in range(1, BUILD_DAYS + 1):
        ctx.time.run_game_days(1, speed=3)
        ctx.popups()
        state = attempt(ctx, f"day {day} manor", ctx.actions.manor_state)
        modules = (state or {}).get("modules", [])
        if modules and all(m.get("built") for m in modules) and day > 3:
            note(ctx, "all modules built", day=day)
            return


def run(ctx) -> dict:
    actions = ctx.actions
    attempt(ctx, "stat 123", lambda: actions.building_stat(MODULE_TYPE))
    attempt(ctx, "manor_state", actions.manor_state)
    manor = find_manor_path(ctx)
    note(ctx, "manor path", manor=manor)
    if not manor:
        return ctx.fail("manor", "no manor master found")
    open_planner(ctx, manor)
    if ctx.variant_option("HARNESS_PROBE", "planner") == "planner":
        return ctx.result()
    feed_builders(ctx)
    count_module_users(ctx, "before")
    attempt(ctx, "blueprint add", lambda: actions._command("manor_blueprint_add", type=MODULE_TYPE, x=SPOT[0], y=SPOT[1], z=SPOT[2],
                                                          yaw=0, mesh=MESH, commit=True))
    ctx.screenshot("committed")
    watch(ctx)
    count_module_users(ctx, "after")
    manor_id = ((attempt(ctx, "manor id", actions.manor_state) or {}).get("region_manor_id"))
    attempt(ctx, "manor_state end", actions.manor_state)
    attempt(ctx, "parts of manor", lambda: actions.master_parts(building=manor_id, limit=40))
    ctx.screenshot("end")
    return ctx.result()
