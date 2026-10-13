"""Probe for the open questions of issue #60 (spec 16, policy edicts).

Research tool. It writes every answer to `probe.jsonl` and never fails on a game answer.
Choose a mode with HARNESS_PROBE:
  census   one read of the policy state and the food stock (find the food goods)
  enact    try the conditions of PawnCPP:enactPolicy (slot, pawn.availablePolicies, resources)
  ab       Strict fasting A/B. HARNESS_ARM is "off" or "on". HARNESS_SHORTAGE=1 removes most of the food first.
"""

import json
import os
import time

from runlib import osinput
from runlib.game import find_game_processes
from runlib.windows import list_windows, pick_game_window

NAME = "probe-policy-followups"
LIMIT_S = 900
HIDDEN = True
LONG_REASON = "The A/B mode watches several game days."
POLICY = 12
AB_DAYS = int(os.environ.get("HARNESS_AB_DAYS", "6"))
GRID_STEP_PX = 30
GRID_FROM_PX = 200
GRID_TO_PX = 760
CARD_POSITION = (300, 300)
STEP_DAYS = 1
SPEED = 3
FOOD_GOODS = (171, 172, 230)  # berries, wheat bread, vegetables (spec 15 notes)
NORMAL_FOOD_EACH = 60
SHORTAGE_FOOD_EACH = 6
ENACT_SLOTS = (0, 1, 2)


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

    def region_read(self, name: str):
        bridge = self.ctx.bridge
        try:
            return bridge.read_property(bridge.player_region_path(), name)
        except Exception as error:  # noqa: BLE001
            return f"unreadable: {str(error)[:100]}"

    def numbers(self, step: str) -> dict | None:
        def read():
            state = self.ctx.actions.policy_state()
            census = self.ctx.actions.sack_census()
            return {
                "approval": state["approval"], "signed": state["signed"], "wealth": state["regional_wealth"],
                "silver": state["silver"], "influence": state["influence"], "factors": state["approval_factors"],
                "supplies_food": self.region_read("supplies_food"), "stock": census["stock"], "people": census["people"],
            }
        return self.attempt(step, read)


def census(probe) -> None:
    probe.numbers("start")
    probe.attempt("policy_state", probe.ctx.actions.policy_state)


def enact_calls(probe) -> None:
    actions = probe.ctx.actions
    for slot in ENACT_SLOTS:
        probe.attempt(f"enact 12 slot {slot}", lambda s=slot: actions._command("policy_enact", policy=POLICY, slot=s))  # noqa: SLF001
    bridge = probe.ctx.bridge
    pawn = bridge.player_path()
    probe.attempt("write pawn.availablePolicies", lambda: bridge.write_property(pawn, "availablePolicies", [2, 4, 7, 8, 10, 12]))
    probe.attempt("read pawn.availablePolicies", lambda: bridge.read_property(pawn, "availablePolicies"))
    probe.attempt("enact 12 slot 0 after write", lambda: actions.policy_enact(POLICY, 0))


def enact(probe) -> None:
    actions = probe.ctx.actions
    probe.numbers("start")
    enact_calls(probe)
    probe.attempt("raise resources", lambda: (actions.set_silver(5000), actions.set_influence(5000)))
    enact_calls(probe)
    probe.attempt("settlement level 2", lambda: actions.set_settlement_level(2))
    probe.attempt("policy_state level 2", actions.policy_state)
    enact_calls(probe)
    probe.numbers("end")


def raw_enact(probe, region: str, pawn: str, slot: int, policy: int):
    return probe.ctx.bridge.call_function(pawn, "enactPolicy", [region, slot, policy])


def enact2(probe) -> None:
    """Read the signature and the policy-related members, then call enactPolicy with many ids and slots (no Lua pre-check)."""
    bridge = probe.ctx.bridge
    pawn, region = bridge.player_path(), bridge.player_region_path()
    probe.attempt("pawn funcs", lambda: [f for f in bridge._result("funcs", ref=pawn) if "olic" in json.dumps(f) or "evelopment" in json.dumps(f)])  # noqa: SLF001
    probe.attempt("region funcs", lambda: [f for f in bridge._result("funcs", ref=region) if "olic" in json.dumps(f) or "evPoint" in json.dumps(f)])  # noqa: SLF001
    probe.attempt("pawn props", lambda: bridge._result("props", ref=pawn, include_super=True, read_soft=False, pattern="olic|evelop|point|Point"))  # noqa: SLF001
    probe.attempt("region props", lambda: bridge._result("props", ref=region, include_super=True, read_soft=False, pattern="olic|evelop|point|Point"))  # noqa: SLF001
    probe.attempt("sweep", lambda: probe.ctx.actions._command("policy_enact_sweep"))  # noqa: SLF001
    probe.attempt("state after", probe.ctx.actions.policy_state)


def hovered(probe) -> bool:
    return bool(probe.ctx.actions._command("menu_probe_read").get("button_hovered"))  # noqa: SLF001


def signed_ids(probe) -> list:
    return probe.ctx.actions.policy_state()["signed"]


def hook_events(probe) -> None:
    bridge = probe.ctx.bridge
    for label, path in (("sign", "/Script/ManorLords.Region:setPolicySigned"), ("enact", "/Script/ManorLords.PawnCPP:enactPolicy")):
        probe.attempt(f"hook {label}", lambda p=path, l=label: bridge._result("hook", function=p, label=l, max_args=4))  # noqa: SLF001


def click_card(probe) -> None:
    """Show one game policy card, find it by hover with the real mouse, click it, and read what changed."""
    actions = probe.ctx.actions
    hook_events(probe)
    probe.attempt("card show", lambda: actions._command("menu_probe_show", policy=POLICY, x=CARD_POSITION[0], y=CARD_POSITION[1]))  # noqa: SLF001
    probe.ctx.screenshot("card-shown")
    window = pick_game_window(list_windows(), {process.pid for process in find_game_processes()})
    probe.note("window", window=window)
    api = osinput.Win32Input()
    left, top, right, bottom = window["rect"]
    before = signed_ids(probe)
    found = None
    try:
        osinput.focus_game(api, window["hwnd"])
        with osinput.cursor_restored(api):
            for y in range(top + GRID_FROM_PX, min(top + GRID_TO_PX, bottom - 30), GRID_STEP_PX):
                for x in range(left + GRID_FROM_PX, min(left + GRID_TO_PX, right - 30), GRID_STEP_PX):
                    osinput.move_cursor(api, window["hwnd"], (x, y))
                    if hovered(probe):
                        found = (x, y)
                        break
                if found:
                    break
            probe.note("hover scan", found=found, offset=found and (found[0] - left, found[1] - top))
            if found:
                osinput.left_click(api, window["hwnd"])
                time.sleep(1.0)
    except osinput.InputError as error:
        probe.note("input refused", error=str(error))
    probe.ctx.screenshot("card-after-click")
    probe.note("click result", signed_before=before, signed_after=signed_ids(probe))
    probe.attempt("events", lambda: probe.ctx.bridge._result("events", since=0, limit=50))  # noqa: SLF001
    probe.attempt("card hide", lambda: actions._command("menu_probe_hide"))  # noqa: SLF001


def give_food(probe, amount_each: int) -> None:
    for good in FOOD_GOODS:
        probe.attempt(f"give food {good}", lambda g=good: probe.ctx.actions.give_item(g, amount_each))


def ab(probe) -> None:
    arm = os.environ.get("HARNESS_ARM", "off")
    if arm not in ("off", "on"):
        raise ValueError("HARNESS_ARM must be off or on")
    probe.note("arm", arm=arm, shortage=os.environ.get("HARNESS_SHORTAGE") == "1")
    give_food(probe, SHORTAGE_FOOD_EACH if os.environ.get("HARNESS_SHORTAGE") == "1" else NORMAL_FOOD_EACH)
    if arm == "on":
        probe.attempt("sign 12", lambda: probe.ctx.actions.policy_sign(POLICY, True))
    probe.numbers("day 0")
    for day in range(1, AB_DAYS + 1):
        probe.ctx.time.run_game_days(STEP_DAYS, speed=SPEED)
        probe.numbers(f"day {day}")
    if os.environ.get("HARNESS_CLICK") == "1":
        click_card(probe)


def aba(probe) -> None:
    """One game, three blocks: policy off, on, off. It saves launches; the village is the same in all blocks."""
    probe.note("design", blocks=["off", "on", "off"], days_each=AB_DAYS, shortage=os.environ.get("HARNESS_SHORTAGE") == "1")
    give_food(probe, SHORTAGE_FOOD_EACH if os.environ.get("HARNESS_SHORTAGE") == "1" else NORMAL_FOOD_EACH)
    probe.numbers("start")
    for block, signed in (("A1", False), ("B", True), ("A2", False)):
        probe.attempt(f"block {block} sign={signed}", lambda s=signed: probe.ctx.actions.policy_sign(POLICY, s) and None)
        probe.numbers(f"day {block} 0")
        for day in range(1, AB_DAYS + 1):
            probe.ctx.time.run_game_days(STEP_DAYS, speed=SPEED)
            probe.numbers(f"day {block} {day}")


def click_only(probe) -> None:
    click_card(probe)


MODES = {"census": census, "enact": enact, "enact2": enact2, "ab": ab, "click": click_only, "aba": aba}


def run(ctx) -> dict:
    probe = Probe(ctx)
    mode = os.environ.get("HARNESS_PROBE", "census")
    if mode not in MODES:
        raise ValueError(f"HARNESS_PROBE must be one of {sorted(MODES)}")
    probe.note("mode", mode=mode)
    MODES[mode](probe)
    return ctx.result()
