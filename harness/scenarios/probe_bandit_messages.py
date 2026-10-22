"""Probe for the spike `spike-bandit-message-toggle`: which game code makes the bandit negotiation messages?

Research tool. It records every answer in `probe.jsonl` and never fails on a game answer. It never saves the game and uses no raw eval.
HARNESS_PROBE: `discover` (list functions, hook candidates, raid + native letter, screenshots) or `suppress` (same, with a suppress mode).
HARNESS_SUPPRESS: name of a suppress way for the mod command `probe_message_suppress` of HarnessActions (empty: none).
"""

import json
import os
import re

NAME = "probe-bandit-messages"
LIMIT_S = 400
HIDDEN = True
LONG_REASON = "Waits for a raid to spawn and for the letter reply, in game time."
SPEED = 2
PATTERN = re.compile(r"letter|message|notif|popup|raider|bandit|negot|relation|toast|banner|inbox|response", re.I)
OBJECT_CLASSES = ("PawnCPP", "PawnCPP_AI", "RTSMultiEngineCPP")
MAX_HOOKS = 40


def note(ctx, step: str, **data) -> None:
    entry = {"step": step, **data}
    ctx.log.info(f"PROBE {json.dumps(entry, default=str)[:1800]}")
    with (ctx.run_dir / "probe.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, default=str) + "\n")


def attempt(ctx, step: str, fn):
    try:
        result = fn()
    except Exception as error:  # noqa: BLE001 - a probe records the failure and goes on
        ctx.ensure_alive(step)
        note(ctx, step, error=repr(error)[:600])
        return None
    note(ctx, step, result=result)
    return result


def function_paths(ctx) -> list:
    matches = []
    targets = {"player": ctx.bridge.player_path(), "engine": ctx.bridge.engine_path()}
    ai = ctx.bridge._result("objects", class_name="PawnCPP_AI", limit=3)  # noqa: SLF001
    note(ctx, "ai objects", found=ai)
    for ref, path in targets.items():
        listed = attempt(ctx, f"funcs {ref}", lambda p=path: ctx.bridge._result("funcs", ref=p)) or []  # noqa: SLF001
        for row in listed:
            if PATTERN.search(row.get("name", "")):
                matches.append(f"{ref}:{row.get('owner')}:{row['name']}")
    note(ctx, "matching functions", count=len(matches), rows=matches)
    return matches


def probe_inbox(ctx, step: str):
    return attempt(ctx, step, lambda: ctx.actions._command("message_probe", mode="inspect"))  # noqa: SLF001


WIDGET_CLASSES = ("questMessageElaborate_C", "genericAchievement_EventMessage_C", "popupMessageWidget_C", "tutorialMessage_C",
                  "MessageFullscreen_C", "saveFinishedNotification_C")


def widgets(ctx, step: str) -> None:
    """Count the message widgets in memory and read the text properties of the first of each class."""
    rows = {}
    for name in WIDGET_CLASSES:
        found = attempt(ctx, f"{step} objects {name}", lambda n=name: ctx.bridge._result("objects", class_name=n, limit=4)) or {}  # noqa: SLF001
        live = [path for path in found.get("objects", []) if "Default__" not in path]
        rows[name] = len(live)
        if live:
            ref = live[-1].split(" ", 1)[-1]
            attempt(ctx, f"{step} props {name}", lambda r=ref: ctx.bridge._result("props", ref=r, include_super=False, read_soft=False, pattern="ext|ount|essage|isible"))  # noqa: SLF001
    note(ctx, f"{step} widget counts", rows=rows)


def run(ctx) -> dict:
    mode = os.environ.get("HARNESS_PROBE", "run")
    suppress = os.environ.get("HARNESS_SUPPRESS", "")
    note(ctx, "start", mode=mode, suppress=suppress)
    if mode == "discover":
        function_paths(ctx)
    for path in [p for p in os.environ.get("HARNESS_HOOKS", "").split(",") if p][:MAX_HOOKS]:
        attempt(ctx, f"hook {path}", lambda p=path: ctx.bridge._result("hook", function=p, label=p.split(":")[-1], max_args=6))  # noqa: SLF001
    if suppress:
        attempt(ctx, f"suppress mode {suppress}", lambda: ctx.actions._command("message_probe", mode=suppress))  # noqa: SLF001
    ctx.time.set_speed(SPEED)
    attempt(ctx, "popups 0", ctx.actions.popup_state)
    widgets(ctx, "before")
    ctx.screenshot("00-before")
    attempt(ctx, "spawn raid", lambda: ctx.actions.spawn_raid(1))
    ctx.time.run_game_seconds(15, speed=SPEED)
    widgets(ctx, "raid+15")
    attempt(ctx, "state after raid", ctx.actions.bandit_state)
    ctx.screenshot("01-raid")
    before = attempt(ctx, "state before letter", ctx.actions.bandit_state)
    attempt(ctx, "tag attacking", lambda: ctx.actions.bandit_tag("attacking"))
    ctx.actions.set_silver(200)
    widgets(ctx, "before letter")
    attempt(ctx, "settle offer", lambda: ctx.actions.bandit_settle_offer(30))
    widgets(ctx, "after letter at once")
    for index in range(1, 6):
        ctx.time.run_game_seconds(6, speed=SPEED)
        attempt(ctx, f"popups letter+{index}", ctx.actions.popup_state)
        probe_inbox(ctx, f"inbox letter+{index}")
        if index in (1, 3, 5):
            widgets(ctx, f"letter+{index}")
        if index == 3 and os.environ.get("HARNESS_HIDE") == "1":
            attempt(ctx, "hide banners", lambda: ctx.actions._command("message_probe", mode="hidebanners"))  # noqa: SLF001
            ctx.screenshot("02-hidden-a")
            widgets(ctx, "hidden")
        ctx.screenshot(f"02-letter-{index}")
    after = attempt(ctx, "state after bandit letter", ctx.actions.bandit_state)
    attempt(ctx, "other letter", lambda: ctx.actions.send_letter(["welcome_from_hildebolt"]))
    for index in range(1, 4):
        ctx.time.run_game_seconds(6, speed=SPEED)
        probe_inbox(ctx, f"inbox other+{index}")
        ctx.screenshot(f"03-other-{index}")
    attempt(ctx, "census", ctx.actions.units_census)
    attempt(ctx, "events", lambda: ctx.bridge._result("events", since=0, limit=200))  # noqa: SLF001
    ctx.metric("bandit_units_before", (before or {}).get("bandit_units", -1))
    ctx.metric("bandit_units_after", (after or {}).get("bandit_units", -1))
    return ctx.result()
