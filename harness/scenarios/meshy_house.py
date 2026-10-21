"""Build one burgage house and take close screenshots of it (change add-meshy-agent-house-test).

Run it on the default fixture (base). With `--pak meshyhouse` the three level 1 cottage meshes are replaced by a model made
with the Meshy agent CLI; without the pak the vanilla house shows. It saves nothing.
The replaced mesh keeps the vanilla asset path, so the path cannot tell the two runs apart: read the screenshots.
"""

import math
import time

from runlib import plotgeom

NAME = "meshy-agent-house"
DESCRIPTION = "Builds one cottage level 1 burgage house and photographs it from close (vanilla or with the meshyhouse pak)."
LIMIT_S = 1500
SPEED = 2
LONG_REASON = "A burgage house shows its mesh about 10 game days after the plot is placed."
TIMBER = 16
TIMBER_AMOUNT = 60
BUILD_DAYS_LIMIT = 24
FINISH_DAYS_LIMIT = 40  # the plot counts as built at day 1, the house mesh shows after about 8 more days
COTTAGE_MESH = "SM_MERGED_C_SG_Cottage_Lv1"
CAMERA_SETTLE_S = 1.5
CAMERA_LAST_S = 0.5
CAMERA_TRIES = 4
CAMERA_OFF_CM = 300
ZOOMS = (3000, 1500, 600)
SIDE_ZOOM = 900


def cottage_actors(ctx) -> dict:
    return ctx.commands.send("mesh_actors", mesh=COTTAGE_MESH)


def house_visible(ctx, house) -> bool:
    """True when the new cottage's mesh component is visible. It is hidden while the house is a construction site."""
    rows = ctx.commands.send("mesh_actors", mesh=COTTAGE_MESH, materials="1")["actors"]
    near = [r for r in rows if abs(r["x"] - house[0]) < 800 and abs(r["y"] - house[1]) < 800]
    if not near:
        return False
    component = near[0]["component"].split(" ", 1)[1]
    visible = ctx.bridge.read_property(component, "bVisible")
    ctx.log.info(f"new house component bVisible {visible}")
    return bool(visible)


def look(ctx, label: str, x: float, y: float, yaw: float | None = None) -> None:
    """Centre the camera on (x, y) and take a picture. The camera follows the pawn only while the game runs (speed 1)."""
    if yaw is not None:
        ctx.bridge.call_function(ctx.bridge.player_path(), "K2_SetActorRotation", [{"Pitch": 0, "Yaw": yaw, "Roll": 0}, False])
    ground = {"X": 0.0, "Y": 0.0}
    for _ in range(CAMERA_TRIES):
        try:
            ctx.bridge.centre_camera_on(x, y)
            time.sleep(CAMERA_SETTLE_S)
            ground = ctx.bridge.centre_camera_on(x, y)
        except RuntimeError as error:  # the camera looked at the sky: wait and try again
            ctx.log.info(f"camera {label}: {error}")
            time.sleep(CAMERA_SETTLE_S)
            continue
        if math.hypot(ground["X"] - x, ground["Y"] - y) < CAMERA_OFF_CM:
            break
    time.sleep(CAMERA_LAST_S)  # the pawn keeps drifting, so the picture follows at once
    off_cm = math.hypot(ground["X"] - x, ground["Y"] - y)
    ctx.metric(f"camera_off_cm_{label}", round(off_cm))
    ctx.log.info(f"camera {label} wanted ({x:.0f}, {y:.0f}) yaw {yaw} ground under centre {ground}")
    ctx.screenshot(label)


def run(ctx) -> dict:
    actions = ctx.actions
    before = cottage_actors(ctx)
    built_before = actions.burgage_count(True)
    spots = actions.tent_find_spot()
    spot, centre = spots["spots"][0], spots["centre"]
    plots = plotgeom.make_plots(spot["x"], spot["y"], spot["z"], spot["x"] - centre["x"], spot["y"] - centre["y"], 1)
    house = plots[0]["primary"]
    ctx.log.info(f"house position {house[:3]}")
    actions.give_item(TIMBER, TIMBER_AMOUNT)
    actions.open_burgage_tool()
    actions.plot_field_place(plots)
    actions.commit_plots()
    days = 0
    while actions.burgage_count(True) <= built_before and days < BUILD_DAYS_LIMIT:
        ctx.popups()
        ctx.time.run_game_days(1, speed=SPEED)
        days += 1
    ctx.metric("build_days", days)
    ctx.check("the burgage house is built", actions.burgage_count(True) > built_before, [built_before, days])
    after = cottage_actors(ctx)
    ctx.log.info(f"cottage actors before {before['total']} after {after['total']}: {after['actors']}")
    ctx.check("a level 1 cottage mesh user appeared", after["total"] > before["total"], [before["total"], after["total"]])
    waited = 0
    while waited < FINISH_DAYS_LIMIT and not house_visible(ctx, house):
        ctx.popups()
        ctx.time.run_game_days(4, speed=3)
        waited += 4
    ctx.metric("construction_days_after_plot_built", waited)
    ctx.check("the house is finished (not a construction site)", house_visible(ctx, house), waited)
    ctx.time.set_speed(1)
    ctx.bridge.write_property(ctx.bridge.player_path(), "placeFieldMode", False)
    after = ctx.commands.send("mesh_actors", mesh=COTTAGE_MESH, materials="1")
    old = {(a["x"], a["y"]) for a in before["actors"]}
    new = [a for a in after["actors"] if (a["x"], a["y"]) not in old]
    ctx.check("exactly one new cottage actor", len(new) == 1, new)
    target = new[0] if new else {"x": house[0], "y": house[1], "z": house[2], "yaw": 0, "component": None}
    ctx.log.info(f"new house actor {target}; plot house point {house[:3]}")
    ctx.metric("house_z_below_plot_cm", house[2] - target["z"])
    if target["component"]:
        where = ctx.bridge.call_function(target["component"].split(" ", 1)[1], "K2_GetComponentLocation")
        target = {**target, "x": where["X"], "y": where["Y"]}
    player = ctx.bridge.player_path()
    saved_zoom = ctx.bridge.read_property(player, "zoomLevel")
    for zoom in ZOOMS:
        ctx.bridge.write_property(player, "zoomLevel", zoom)
        look(ctx, f"house_z{zoom}", target["x"], target["y"])
    console = ctx.variant_option("MESHY_CONSOLE", "")  # texture streaming test: console commands split by ";"
    if console:
        ctx.bridge.write_property(player, "zoomLevel", 600)
        for command in console.split(";"):
            ctx.log.info(f"console {command}: {ctx.bridge._result('console', command=command.strip())}")
        time.sleep(4)
        look(ctx, "house_z600_console", target["x"], target["y"])
        for prop in ("NeverStream", "LODBias", "CachedCombinedLODBias", "MipGenSettings", "LODGroup"):
            try:
                ctx.log.info(f"texture_0 {prop} = {ctx.bridge.read_property('/Game/HarnessMod/MeshyHouse/texture_0.texture_0', prop)}")
            except RuntimeError as error:
                ctx.log.info(f"texture_0 {prop} unreadable: {error}")
    # Live material experiments: MESHY_EXP, MESHY_EXP2.. = "s=a=1,b=2;v=c=1:0:0" (s scalars, v vectors, t textures). They add up. One picture each.
    for number, group in enumerate(filter(None, (ctx.variant_option(name, "") for name in ("MESHY_EXP", "MESHY_EXP2", "MESHY_EXP3", "MESHY_EXP4")))):
        fields = {"s": "scalars", "v": "vectors", "t": "textures"}
        args = {fields[part[0]]: part[2:] for part in group.split(";")}
        ctx.bridge.write_property(player, "zoomLevel", 600)
        answer = ctx.commands.send("mesh_material_params", mesh=COTTAGE_MESH, near_x=int(target["x"]), near_y=int(target["y"]), **args)
        ctx.log.info(f"experiment {number} {group}: {answer}")
        time.sleep(2)
        look(ctx, f"house_exp{number}", target["x"], target["y"])
    # Test: MESHY_SWAP=lend puts our material on a game building and photographs it; MESHY_SWAP=borrow draws our house with its material.
    swap = ctx.variant_option("MESHY_SWAP", "")
    for mode in filter(None, swap.split("+")):
        ctx.bridge.write_property(player, "zoomLevel", 600)
        try:
            answer = ctx.commands.send("mesh_material_swap", mesh=COTTAGE_MESH, near_x=int(target["x"]), near_y=int(target["y"]), mode=mode)
        except Exception as error:  # a failed swap must not end the run: the other pictures are still needed
            ctx.log.info(f"swap {mode} failed: {error}")
            continue
        ctx.log.info(f"swap {mode}: {answer}")
        time.sleep(2)
        if mode == "lend":
            look(ctx, "other_lend", answer["x"], answer["y"])
        else:
            look(ctx, "house_borrow", target["x"], target["y"])
    ctx.bridge.write_property(player, "zoomLevel", SIDE_ZOOM)
    for name, turn in (("side_a", 90), ("side_b", 180)):
        look(ctx, f"house_{name}", target["x"], target["y"], target["yaw"] + turn)
    ctx.bridge.write_property(player, "zoomLevel", saved_zoom)
    return ctx.result()
