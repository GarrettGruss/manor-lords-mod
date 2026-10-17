"""Probe for issues #90 and #65 (spec 12): the working manor planner flow with the real mouse.

Flow (recorded in a live test, 2026-10-14): open the planner, click a card, click empty ground in the bailey to place,
check that the manor `blueprints` list grew and the rebuild cost is not empty, then click Commit, give goods, run days.
Use fixture manor-closed. Options (run.py --env): HARNESS_CARD_X, HARNESS_CARD_Y (card position), HARNESS_SPOTS ("fx,fy;fx,fy"),
HARNESS_STAT_TYPE (building type to read), HARNESS_DAYS (build days, default 40).
Mouse-free mode (HARNESS_MOUSEFREE=1, round 9): the planner stays closed. The probe adds the blueprint with `manor_blueprint_add`
(HARNESS_TYPE default 57, HARNESS_SPOT "x,y,z", optional HARNESS_MESH), checks that `blueprints` grew and the cost is filled,
then commits with `manor_planner commit` in the order HARNESS_ORDER (hand, convert_first, convert_only).
It calls no save function. It never calls convertBlueprintsToBuildings: the Commit button does it.
"""

import json
import time

from runlib.bridge_client import object_path

NAME = "probe-manor-flow"
LIMIT_S = 2400
EXCLUSIVE = True  # real mouse input: a parallel suite runs it with no other game
HIDDEN = True
LONG_REASON = "The probe waits several game days for builders."
MANOR_TYPE = 98
TIMBER, PLANKS, RUBBLE = 16, 17, 15
FOODS = (30, 171)
COMMIT_BUTTON = (0.905, 0.89)
DEFAULT_SPOTS = "0.40,0.62;0.45,0.66;0.50,0.62;0.35,0.66"


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
        data = ctx.bridge.read_property(path, "Data")
        if isinstance(data, dict) and data.get("bType") == MANOR_TYPE:
            return path
    return None


def count_of(value) -> int | None:
    if isinstance(value, (list, tuple)):
        return len(value)
    if isinstance(value, dict):
        for key in ("count", "num", "length", "n"):
            if isinstance(value.get(key), int):
                return value[key]
    return value if isinstance(value, int) else None


def blueprint_count(ctx, manor: str) -> int | None:
    return count_of(attempt(ctx, "blueprints", lambda: ctx.bridge.read_property(manor, "blueprints")))


def cost_is_filled(ctx, manor: str) -> bool:
    cost = attempt(ctx, "cost", lambda: ctx.bridge.call_function(manor, "getCastleReconstructionCost", [False]))
    return bool(cost)


def place_module(ctx, manor: str, spots: list[tuple[float, float]]) -> bool:
    """Click the first spot that adds a blueprint. The Commit click is only safe after the list grew and the cost is filled."""
    before = blueprint_count(ctx, manor)
    for index, (fx, fy) in enumerate(spots):
        attempt(ctx, "hover", lambda a=fx, b=fy: ctx.hover_with_mouse(a, b))
        time.sleep(1.5)
        ctx.screenshot(f"ghost{index}")
        attempt(ctx, "place click", lambda a=fx, b=fy: ctx.click_with_mouse(a, b))
        time.sleep(2)
        after = blueprint_count(ctx, manor)
        ctx.screenshot(f"placed{index}")
        if before is not None and after is not None and after > before:
            return cost_is_filled(ctx, manor)
    return False


def feed_builders(ctx) -> None:
    actions = ctx.actions
    attempt(ctx, "manor slots", lambda: actions.manor_worker_slot(45, 3))
    for index in range(3):
        attempt(ctx, f"assign worker {index}", actions.manor_assign_worker)
    for good, amount in ((RUBBLE, 60), (FOODS[0], 150), (FOODS[1], 150), (TIMBER, 80), (PLANKS, 120)):
        attempt(ctx, f"give {good}", lambda g=good, a=amount: actions.give_item(g, a))
    attempt(ctx, "more families", lambda: actions.family_add(6, adult=True))


def watch_build(ctx, manor: str, days: int) -> bool:
    """Advance days until IsConstructed is true again. Only the manor flag is read: part and mesh reads after a commit crash the game."""
    for day in range(1, days + 1):
        ctx.time.run_game_days(1, speed=3)
        ctx.popups()
        built = attempt(ctx, f"day {day} IsConstructed", lambda: ctx.bridge.call_function(manor, "IsConstructed"))
        if day % 10 == 0:
            ctx.screenshot(f"day{day}")
        if built is True and day > 1:
            return True
    return False


def mousefree_place(ctx, manor: str) -> bool:
    option = ctx.variant_option
    x, y, z = (float(v) for v in option("HARNESS_SPOT", "13000,-51163,2500").split(","))
    args = {"type": int(option("HARNESS_TYPE", "57")), "x": x, "y": y, "z": z, "yaw": 0}
    if option("HARNESS_MESH", ""):
        args["mesh"] = option("HARNESS_MESH", "")
    before = blueprint_count(ctx, manor)
    attempt(ctx, "blueprint add", lambda: ctx.actions._command("manor_blueprint_add", **args))
    after = blueprint_count(ctx, manor)
    ctx.screenshot("mousefree_placed")
    return before is not None and after is not None and after > before and cost_is_filled(ctx, manor)


def mousefree_commit(ctx) -> None:
    order = ctx.variant_option("HARNESS_ORDER", "hand")
    note(ctx, "commit start", order=order)
    attempt(ctx, "commit", lambda: ctx.actions._command("manor_planner", commit=True, order=order))
    time.sleep(3)
    ctx.ensure_alive("after commit")
    ctx.screenshot("mousefree_committed")


def parse_spots(text: str) -> list[tuple[float, float]]:
    return [tuple(float(v) for v in pair.split(",")) for pair in text.split(";")]  # type: ignore[misc]


def run(ctx) -> dict:
    option = ctx.variant_option
    attempt(ctx, "stat", lambda: ctx.actions._command("building_stat", kind=int(option("HARNESS_STAT_TYPE", "57"))))
    manor = find_manor_path(ctx)
    note(ctx, "manor path", manor=manor)
    if not manor:
        return ctx.fail("manor", "no manor master found")
    attempt(ctx, "close popups", ctx.actions.close_popups)
    attempt(ctx, "garrison before", lambda: ctx.bridge.call_function(manor, "getModularGarrisonLimit"))
    if option("HARNESS_MOUSEFREE", "0") == "1":
        if not mousefree_place(ctx, manor):
            return ctx.fail("place", "the blueprint did not register or the cost is empty")
        mousefree_commit(ctx)
        return finish_build(ctx, manor)
    attempt(ctx, "open planner", lambda: ctx.actions._command("manor_planner", ui=True))
    time.sleep(2)
    ctx.screenshot("planner")
    if option("HARNESS_STOP", "") == "planner":  # for a --keep-open session driven by hand
        return ctx.result()
    card = (float(option("HARNESS_CARD_X", "0.875")), float(option("HARNESS_CARD_Y", "0.449")))
    spots = parse_spots(option("HARNESS_SPOTS", DEFAULT_SPOTS))
    attempt(ctx, "unpause", ctx.bridge.unpause)  # the ghost follows the cursor only while the game runs
    placed = False
    for attempt_number in range(2):  # run s90f-1: the first card click did not select the card, so click again once
        if attempt_number == 0:  # a banner can eat world clicks; later the card may be selected, so do not click the world
            attempt(ctx, "dismiss banner", lambda: ctx.click_with_mouse(0.50, 0.306))
            time.sleep(1)
        attempt(ctx, "hover card", lambda: ctx.hover_with_mouse(*card))
        time.sleep(1)
        attempt(ctx, "click card", lambda: ctx.click_with_mouse(*card))
        time.sleep(2)
        ctx.screenshot(f"card{attempt_number}")
        placed = place_module(ctx, manor, spots)
        if placed:
            break
    if not placed:
        note(ctx, "not placed", reason="blueprints did not grow or the cost is empty")
        attempt(ctx, "planner close", lambda: ctx.actions._command("manor_planner", close=True))
        return ctx.fail("place", "the module was not registered as a blueprint")
    attempt(ctx, "commit click", lambda: ctx.click_with_mouse(*COMMIT_BUTTON))
    time.sleep(3)
    ctx.screenshot("committed")
    return finish_build(ctx, manor)


def finish_build(ctx, manor: str) -> dict:
    option = ctx.variant_option
    feed_builders(ctx)
    attempt(ctx, "unpause", ctx.bridge.unpause)
    built = watch_build(ctx, manor, int(option("HARNESS_DAYS", "40")))
    note(ctx, "build done", built=built)
    attempt(ctx, "manor_state after", ctx.actions.manor_state)
    attempt(ctx, "garrison after",lambda: ctx.bridge.call_function(manor, "getModularGarrisonLimit"))
    ctx.screenshot("end")
    return ctx.result()
