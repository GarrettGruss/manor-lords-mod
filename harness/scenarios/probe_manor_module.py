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
LV3_TYPE = 83
LV3_MESH = "/Game/NotStronghold/Buildings/Merged/SM_MERGED_C_SG_Tower_Lv3"
TIMBER, RUBBLE, PLANKS = 16, 15, 17
FOODS = (30, 171)
BUILD_DAYS = 60
# Screen fractions: the gatehouse in the fixture view, then the screen centre.
DOWN_ARROW = (0.741, 0.49)  # the planner card list scroll arrow, as a fraction of the window
SCROLL_CLICKS = 0
HIDE_STAGES = ((57, 58),) # spike #90: cards 81 and 83 are re-enabled by the mmlv3ui pak
PAGE = 8  # master_parts rows per call. 40 rows did not answer in 10 s (run s65d-2)
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


def list_parts(ctx, manor_id) -> dict:
    """All parts of the manor, read in pages. Key: the actor name. Value: the compact row."""
    parts = {}
    start = 1
    while True:
        reply = ctx.actions.master_parts(building=manor_id, limit=PAGE, start=start, detail=True)
        for row in reply.get("rows", []):
            parts[row.get("name") or f"index{row['index']}"] = row
        if start + PAGE > reply.get("parts", 0):
            return parts
        start += PAGE


def report_new_parts(ctx, manor_id, before: dict) -> None:
    after = attempt(ctx, "parts after", lambda: list_parts(ctx, manor_id)) or {}
    new = [row for name, row in after.items() if name not in before]
    note(ctx, "parts diff", before=len(before), after=len(after), new=new)
    typed = [row for row in new if row.get("btype") == MODULE_TYPE or f"bType_{MODULE_TYPE}" in (row.get("tags") or [])]
    note(ctx, "type 123 parts", count=len(typed), rows=typed)
    if new:
        first = new[0]
        attempt(ctx, "camera on new part", lambda: ctx.bridge.centre_camera_on(first["x"], first["y"]))
        time.sleep(2)
        ctx.screenshot("module_built")


def scroll_cards(ctx) -> None:
    """The card list is a WrapBox (no ScrollBox exists: run s65c-3). Collapse cards in stages and take a screenshot after each stage."""
    for stage, ids in enumerate(HIDE_STAGES):
        found = attempt(ctx, "cards again", lambda: ctx.bridge._result("objects", class_name="buildingCardWidget_C", limit=60)["objects"]) or []
        for ref in found:
            path = object_path(ref)
            if path.startswith("/Engine/Transient") and ctx.bridge.read_property(path, "ID") in ids:
                attempt(ctx, "collapse card", lambda p=path: ctx.bridge.call_function(p, "SetVisibility", [1]))
        time.sleep(3)
        ctx.screenshot(f"planner_card123_stage{stage}")


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
    if ctx.variant_option("HARNESS_PROBE", "planner") in ("lv3", "lv3place"):
        place_lv3(ctx, manor)
        return
    attempt(ctx, "planner close", lambda: ctx.actions._command("manor_planner", close=True))


def place_lv3(ctx, manor) -> None:
    """Pick the Lv3 keep card (slot ID 83, left card), move over the bailey, place with a real click, then Commit."""
    if ctx.variant_option("HARNESS_DISMISS", "0") == "1":  # the "A New Message" banner may eat world clicks
        attempt(ctx, "dismiss message", lambda: ctx.click_with_mouse(0.50, 0.306))
        time.sleep(1)
    attempt(ctx, "click card", lambda: ctx.click_with_mouse(float(ctx.variant_option("HARNESS_CARD_X", "0.83")), 0.449))
    spots = ((0.40, 0.55), (0.45, 0.60), (0.50, 0.62))
    if ctx.variant_option("HARNESS_GRID", "0") == "1":  # round 2: find a spot where the ghost is white
        spots = ((0.35, 0.62), (0.45, 0.70), (0.40, 0.80), (0.50, 0.80), (0.30, 0.55), (0.55, 0.65))
    chosen = ctx.variant_option("HARNESS_PLACE", "")  # "fx,fy": hover there and click Place
    if chosen:
        spots = (tuple(float(v) for v in chosen.split(",")),)
    for step, (fx, fy) in enumerate(spots):
        attempt(ctx, "hover bailey", lambda a=fx, b=fy: ctx.hover_with_mouse(a, b))
        time.sleep(1.5)
        ctx.screenshot(f"lv3_ghost{step}")
    attempt(ctx, "place click", lambda: ctx.click_with_mouse(*spots[-1]))
    time.sleep(2)
    ctx.screenshot("lv3_placed")
    attempt(ctx, "manor_state placed", ctx.actions.manor_state)
    attempt(ctx, "canConstructCastle", lambda: ctx.bridge.call_function(manor, "canConstructCastle", [[]]))
    attempt(ctx, "getBuildingArea", lambda: ctx.bridge.call_function(manor, "getBuildingArea"))
    attempt(ctx, "blueprint ghosts", lambda: ctx.bridge.read_property(manor, "blueprintGhosts"))
    attempt(ctx, "walls", lambda: ctx.bridge.read_property(manor, "walls"))
    if ctx.variant_option("HARNESS_CLICKCOMMIT", "0") == "1":  # real click on the planner Commit button
        attempt(ctx, "commit click", lambda: ctx.click_with_mouse(0.905, 0.89))
        time.sleep(3)
        ctx.screenshot("lv3_commit_click")
    attempt(ctx, "hover away", lambda: ctx.hover_with_mouse(0.30, 0.70))
    time.sleep(2)
    ctx.screenshot("lv3_after_move")
    # The Commit button stayed grey and a click removed the module (runs s90-3, s90-4). Commit by command, then close the planner.
    if ctx.variant_option("HARNESS_PROBE", "planner") == "lv3":
        attempt(ctx, "planner commit", lambda: ctx.actions._command("manor_planner", commit=True))
    attempt(ctx, "planner close", lambda: ctx.actions._command("manor_planner", close=True))
    time.sleep(2)


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
    if ctx.variant_option("HARNESS_PROBE", "planner") == "lv3place":
        return ctx.result()
    module_type, mesh = (LV3_TYPE, LV3_MESH) if ctx.variant_option("HARNESS_PROBE", "planner") == "lv3" else (MODULE_TYPE, MESH)
    feed_builders(ctx)
    count_module_users(ctx, "before")
    manor_id = (attempt(ctx, "manor id", actions.manor_state) or {}).get("region_manor_id")
    parts_before = attempt(ctx, "parts before", lambda: list_parts(ctx, manor_id)) or {}
    note(ctx, "parts before count", count=len(parts_before))
    if module_type != LV3_TYPE:  # the Lv3 module was planned in the planner and committed there
        attempt(ctx, "blueprint add", lambda: actions._command("manor_blueprint_add", type=module_type, x=SPOT[0], y=SPOT[1], z=SPOT[2],
                                                              yaw=0, mesh=mesh, commit=True))
    ctx.screenshot("committed")
    watch(ctx)
    count_module_users(ctx, "after")
    attempt(ctx, "manor_state end", actions.manor_state)
    ctx.screenshot("end")
    report_new_parts(ctx, manor_id, parts_before)
    return ctx.result()
