"""Probe for issue #59 (spike: steer a squad to a point).

Research tool. It records every answer in `probe.jsonl` and never fails on a game answer.
Choose a mode with HARNESS_PROBE:
  player_move   spawn one player squad, order it 4000 units east with steer_move, watch the distance to the point
  bandit_move   the same for a bandit squad (the spec 15 result says the order is ignored)
  both_hooked   hook formALineArmy and related functions, then player_move (the hook shows what the call does)
"""

import json
import os

from runlib import battle

NAME = "probe-steer"
LIMIT_S = 300
EXCLUSIVE = True  # real mouse input: a parallel suite runs it with no other game
HIDDEN = True
LONG_REASON = "The probe watches a squad walk for about 60 game seconds."
DISTANCE = 4000
WATCH_STEPS = 12
STEP_GAME_S = 5
SPEED = 3
PAWN = "/Script/ManorLords.PawnCPP:"
HOOKS = tuple(PAWN + name for name in (
    "formALineArmy", "selectSquad", "deselectSquad", "projectAttackFormation", "projectHoldSquad",
    "RMB_BP_pressed", "RMB_BP_released", "LMB_BP_pressed", "LMB_BP_released", "respawnSquadPathArrows",
))
MOUSE_HOOKS = (
    "/Script/ManorLords.SquadComponent:SetPushStance",
    "/Script/ManorLords.SquadComponent:SetBehaviourStance",
)
BLUEPRINT_HOOKS = (
    "/Game/CPP_BP/MyPawnCPP_BP3.MyPawnCPP_BP3_C:RMB_BP_pressed",
    "/Game/CPP_BP/MyPawnCPP_BP3.MyPawnCPP_BP3_C:RMB_BP_released",
    "/Game/CPP_BP/MyPawnCPP_BP3.MyPawnCPP_BP3_C:InpActEvt_RightMouseButton_K2Node_InputKeyEvent_2",
    "/Game/CPP_BP/MyPawnCPP_BP3.MyPawnCPP_BP3_C:InpActEvt_RightMouseButton_K2Node_InputKeyEvent_3",
)
CURSOR_DX = 1500
CURSOR_DY = 800
CURSOR_Z = 3000
MOUSE_FX = 0.62
MOUSE_FY = 0.45


class Probe:
    def __init__(self, ctx):
        self.ctx = ctx
        self.path = ctx.run_dir / "probe.jsonl"

    def note(self, step: str, **data) -> None:
        entry = {"step": step, **data}
        self.ctx.log.info(f"PROBE {json.dumps(entry, default=str)[:1800]}")
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, default=str) + "\n")

    def attempt(self, step: str, work):
        try:
            result = work()
        except Exception as error:  # noqa: BLE001 - the probe records every answer
            self.ctx.ensure_alive(step)
            self.note(step, error=str(error)[:500])
            return None
        self.note(step, result=result)
        return result


def distance(center: dict | None, point: tuple[float, float]) -> float | None:
    if not center:
        return None
    return round(((center["x"] - point[0]) ** 2 + (center["y"] - point[1]) ** 2) ** 0.5)


def spawn_squad(probe, side: str) -> int | None:
    answer = probe.attempt(f"spawn {side}", lambda: probe.ctx.actions.spawn_units(side, battle.SPEAR))
    if not answer:
        return None
    return answer["answer"]["squads"][0]["id"]


def order_and_watch(probe, side: str) -> None:
    actions = probe.ctx.actions
    squad = spawn_squad(probe, side)
    if squad is None:
        return
    probe.ctx.time.run_game_seconds(3, speed=SPEED)
    state = probe.attempt("state before", lambda: actions.steer_state(squad))
    center = state and state.get("center")
    if not center:
        return
    point = (center["x"] + DISTANCE, center["y"])
    probe.attempt("order", lambda: actions.steer_move(squad, point[0], point[1], center.get("z") or 0))
    for step in range(1, WATCH_STEPS + 1):
        probe.ctx.time.run_game_seconds(STEP_GAME_S, speed=SPEED)
        now = actions.steer_state(squad)
        probe.note(f"watch {step}", game_s=step * STEP_GAME_S, center=now.get("center"), target_mean=now.get("target_mean"),
                   units=now.get("units"), distance=distance(now.get("center"), point))


def player_move(probe) -> None:
    order_and_watch(probe, "player")


def bandit_move(probe) -> None:
    order_and_watch(probe, "bandit")


def both_hooked(probe) -> None:
    probe.attempt("hook", lambda: probe.ctx.actions.steer_hook(list(HOOKS)))
    order_and_watch(probe, "player")
    probe.attempt("hook log", probe.ctx.actions.steer_hook_log)


def mouse_order(probe) -> None:
    """A real right click (OS mouse) orders a selected player squad. The hooks record what the game calls."""
    ctx, actions = probe.ctx, probe.ctx.actions
    probe.attempt("hook", lambda: actions.steer_hook(list(HOOKS + MOUSE_HOOKS + BLUEPRINT_HOOKS)))
    squad = spawn_squad(probe, "player")
    if squad is None:
        return
    ctx.time.run_game_seconds(3, speed=SPEED)
    probe.attempt("select", lambda: actions.steer_select(squad))
    before = actions.steer_state(squad)
    probe.note("state before", state=before)
    ctx.unpause()
    ctx.time.set_speed(SPEED)
    point = probe.attempt("right click", lambda: ctx.order_with_mouse(MOUSE_FX, MOUSE_FY))
    ctx.pause()
    if not point:
        return
    target = (point["X"], point["Y"])
    probe.note("click point", point=point, distance_before=distance(before.get("center"), target))
    for step in range(1, WATCH_STEPS + 1):
        ctx.time.run_game_seconds(STEP_GAME_S, speed=SPEED)
        now = actions.steer_state(squad)
        probe.note(f"watch {step}", game_s=step * STEP_GAME_S, center=now.get("center"), target_mean=now.get("target_mean"),
                   distance=distance(now.get("center"), target))
    probe.attempt("hook log", actions.steer_hook_log)


def lua_rmb(probe) -> None:
    """No OS click: put the cursor over a world point, then call the right-click events of the pawn from Lua."""
    ctx, actions = probe.ctx, probe.ctx.actions
    probe.attempt("hook", lambda: actions.steer_hook(list(HOOKS + BLUEPRINT_HOOKS)))
    squad = spawn_squad(probe, "player")
    if squad is None:
        return
    ctx.time.run_game_seconds(3, speed=SPEED)
    probe.attempt("select", lambda: actions.steer_select(squad))
    before = actions.steer_state(squad)
    center = before["center"]
    probe.note("state before", state=before)
    ctx.unpause()
    ctx.time.set_speed(SPEED)
    cursor = probe.attempt("cursor", lambda: actions.steer_cursor(center["x"] + CURSOR_DX, center["y"] + CURSOR_DY, CURSOR_Z))
    ctx.time.run_game_seconds(1, speed=SPEED)
    point = (probe.attempt("mouse3d", actions.steer_mouse3d) or {}).get("point")
    probe.attempt("rmb", actions.steer_rmb)
    if not point:
        return
    target = (point["x"], point["y"])
    probe.note("target", point=point, cursor=cursor, distance_before=distance(center, target))
    for step in range(1, WATCH_STEPS + 1):
        ctx.time.run_game_seconds(STEP_GAME_S, speed=SPEED)
        now = actions.steer_state(squad)
        probe.note(f"watch {step}", game_s=step * STEP_GAME_S, center=now.get("center"), target_mean=now.get("target_mean"),
                   distance=distance(now.get("center"), target))
    probe.attempt("hook log", actions.steer_hook_log)


def cursor_click(probe) -> None:
    """The mod puts the cursor over a chosen world point (steer_cursor), then one real right click at the cursor orders the squad."""
    ctx, actions = probe.ctx, probe.ctx.actions
    squad = spawn_squad(probe, "player")
    if squad is None:
        return
    ctx.time.run_game_seconds(3, speed=SPEED)
    probe.attempt("select", lambda: actions.steer_select(squad))
    before = actions.steer_state(squad)
    center = before["center"]
    ctx.unpause()
    ctx.time.set_speed(SPEED)
    probe.attempt("cursor", lambda: actions.steer_cursor(center["x"] + CURSOR_DX, center["y"] + CURSOR_DY, CURSOR_Z))
    point = probe.attempt("right click at cursor", ctx.order_with_mouse)
    if not point:
        return
    target = (point["X"], point["Y"])
    probe.note("target", point=point, distance_before=distance(center, target))
    for step in range(1, WATCH_STEPS + 1):
        ctx.time.run_game_seconds(STEP_GAME_S, speed=SPEED)
        now = actions.steer_state(squad)
        probe.note(f"watch {step}", game_s=step * STEP_GAME_S, center=now.get("center"), distance=distance(now.get("center"), target))


MODES = {"cursor_click": cursor_click, "lua_rmb": lua_rmb, "player_move": player_move, "bandit_move": bandit_move, "both_hooked": both_hooked, "mouse_order": mouse_order}


def run(ctx) -> dict:
    probe = Probe(ctx)
    mode = os.environ.get("HARNESS_PROBE", "player_move")
    if mode not in MODES:
        raise ValueError(f"HARNESS_PROBE must be one of {sorted(MODES)}")
    probe.note("mode", mode=mode)
    MODES[mode](probe)
    return ctx.result()
