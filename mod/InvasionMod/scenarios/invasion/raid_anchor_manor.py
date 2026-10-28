"""fix-raid-anchor-manor: a forced lord raid anchors its challenge and army at the player manor, not at the region under the camera.

The scenario moves the camera far from the village first (a precondition check proves the camera region differs), then forces a
raid. It checks the challenge center and the army position against the manor (or the average of the home buildings).
Run it on fixtures `base` and `playtest-noai` (--fixture). It saves nothing.
"""

import math
import time

from runlib import osinput

NAME = "invasion-raid-anchor-manor"
DESCRIPTION = "A lord raid anchors at the player manor with the camera over another region."
LIMIT_S = 400
LONG_REASON = "The run forces a raid, then waits for the army to walk about 30 game seconds, plus boot and camera moves."
SPEED = 3
CAMERA_OFFSET = 54000
ANCHOR_TOLERANCE = 600
ARMY_STEP_S = 30
ARMY_STEPS = 8
ARRIVED = 8000
RAID_LORD = "Hussite Raiders"


def distance(a: dict, b: dict) -> float:
    return math.hypot(a["x"] - b["x"], a["y"] - b["y"])


def army_centre(state: dict) -> dict | None:
    points = [s for lord in state["lords"] if lord.get("name") == RAID_LORD for s in lord["squads"] if s.get("alive") and s.get("x") is not None]
    if not points:
        return None
    return {"x": sum(s["x"] for s in points) / len(points), "y": sum(s["y"] for s in points) / len(points)}


def run(ctx) -> dict:
    home = ctx.actions.battlefield_state(home=True)
    ctx.check("the home anchor is known", home.get("would_anchor") is not None, home)
    anchor = home["would_anchor"]
    ctx.log.info(f"home anchor {anchor} kind={home.get('would_anchor_kind')}")
    ctx.bridge.centre_camera_on(anchor["x"] + CAMERA_OFFSET, anchor["y"])
    time.sleep(2.0)
    camera = ctx.actions.battlefield_state(target=0)
    camera_gap = distance(camera["would_anchor"], anchor)
    ctx.log.info(f"camera region anchor {camera['would_anchor']} kind={camera.get('would_anchor_kind')} gap={camera_gap:.0f}")
    ctx.metric("camera_gap", round(camera_gap))
    ctx.check("precondition: the camera region is not the home region", camera_gap > 10000, camera_gap)

    ctx.mod.command("InvasionMod.invasion_set_difficulty", value=1)
    ctx.run_until(lambda: ctx.mod.command("InvasionMod.invasion_plan_now")["raid_day"] > 0, 30, what="the raid plan")
    ctx.mod.command("InvasionMod.invasion_set_size", size="small")
    ctx.mod.command("InvasionMod.invasion_force_next")
    ctx.run_until(lambda: bool(ctx.mod.command("InvasionMod.raid_behavior_state")["raids"]), 30, what="the raid record")
    ctx.check("the raid is a lord raid", ctx.mod.command("InvasionMod.raid_behavior_state")["raids"][0].get("lord_raid") is True, "no lord raid")

    ctx.time.run_game_seconds(3, speed=SPEED)
    challenges = ctx.actions.lords_state(log=0)["challenges"]
    ctx.check("a challenge exists", bool(challenges), challenges)
    center = challenges[-1]["center"] if challenges else None
    if center:
        gap = distance(center, anchor)
        ctx.metric("challenge_gap", round(gap))
        ctx.check("the challenge center is at the home anchor", gap <= ANCHOR_TOLERANCE, gap)
        ctx.check("the challenge center is not at the camera region", distance(center, camera["would_anchor"]) > 10000, center)

    gaps, centre = [], None
    for _ in range(ARMY_STEPS):
        ctx.time.run_game_seconds(ARMY_STEP_S, speed=SPEED)
        seen = army_centre(ctx.actions.lords_state(log=0))
        if seen is None:
            break  # the army fought at the manor and is gone (it now walks in from the map border, so it can die before the last step)
        centre = seen
        if centre:
            gaps.append(round(distance(centre, anchor)))
            ctx.log.info(f"army {centre} gap to the manor {gaps[-1]}")
            if gaps[-1] <= ARRIVED:
                break
    ctx.check("the raid army is on the map", centre is not None, centre)
    if centre:
        ctx.metric("army_gap", gaps[-1])
        ctx.check("the army came closer to the manor", gaps[-1] < gaps[0] or gaps[-1] <= ARRIVED, gaps)
        ctx.check("the army ends nearer to the manor than to the camera region", gaps[-1] < distance(centre, camera["would_anchor"]), gaps)

    ctx.bridge.centre_camera_on(anchor["x"], anchor["y"])
    osinput.Win32Input().bring_to_front(ctx.game_window()["hwnd"])
    time.sleep(2.0)
    ctx.screenshot("army-at-manor")
    return ctx.result()
