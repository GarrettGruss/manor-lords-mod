"""Probe for change fix-sack-fire-and-goods (design question 4): where are the raiders when the sack runs at the leave?

Research tool. Like raid_sack, but it polls every 10 game seconds and records the bandit squad centres and the raid record when the
raid leave reason or the sack count changes. It also looks for an alarm bell trigger (names only). It saves nothing.
"""

import json

NAME = "probe-sack-leave"
LIMIT_S = 1500
HIDDEN = True
LONG_REASON = "A role raid leaves after up to 25 game days."
SPEED = 3
POLL_GAME_S = 5
DAY_LIMIT = 40
CENTER = (-37635.0, -53829.0)   # the village (player pawn) of the base fixture
BELL_PATTERNS = ("[Bb]ell", "[Aa]larm", "[Ww]arn", "[Rr]ing")


def note(ctx, step: str, **data) -> None:
    entry = {"step": step, **data}
    ctx.log.info(f"PROBE {json.dumps(entry, default=str)[:1800]}")
    with (ctx.run_dir / "probe.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, default=str) + "\n")


def tracker(ctx) -> dict:
    raids = ctx.mod.command("InvasionMod.raid_behavior_state")["raids"]
    return raids[0] if raids else {}


def raiders(ctx) -> dict:
    census = ctx.actions.units_census(sample=0)
    out = []
    for squad in census["squads"]:
        if squad.get("center"):
            c = squad["center"]
            out.append({"id": squad["id"], "side": squad["side"], "size": squad["size"], "region": squad.get("region"),
                        "dist": round(((c["x"] - CENTER[0]) ** 2 + (c["y"] - CENTER[1]) ** 2) ** 0.5)})
    return {"bandit_units": census["by_side"].get("bandit"), "squads": out}


def bell_search(ctx) -> None:
    bridge = ctx.bridge
    targets = {"player": bridge.player_path(), "region": bridge.player_region_path(), "engine": bridge.engine_path()}
    for label, ref in ():
        for pat in BELL_PATTERNS:
            try:
                props = bridge._result("props", ref=ref, include_super=True, read_soft=False, pattern=pat)["properties"]
                note(ctx, f"bell props {label} {pat}", names=[(p.get("name"), p.get("value")) for p in props])
            except Exception as error:  # noqa: BLE001
                ctx.ensure_alive("bell")
                note(ctx, f"bell props {label} {pat}", error=str(error)[:200])
        try:
            funcs = bridge._result("funcs", ref=ref)
            text = json.dumps(funcs, default=str)
            names = sorted({n for n in __import__("re").findall(r'"name": "([^"]+)"', text)
                            if any(k in n.lower() for k in ("bell", "alarm", "warn"))})
            note(ctx, f"bell funcs {label}", names=names, total=text.count('"name"'))
        except Exception as error:  # noqa: BLE001
            ctx.ensure_alive("bell")
            note(ctx, f"bell funcs {label}", error=str(error)[:200])


def run(ctx) -> dict:
    bell_search(ctx)
    ctx.mod.command("InvasionMod.invasion_set_difficulty", value=1)
    ctx.run_until(lambda: ctx.mod.command("InvasionMod.invasion_state")["raid_day"] > 0, 30, what="the raid plan")
    ctx.mod.command("InvasionMod.invasion_set_size", size="small")
    ctx.mod.command("InvasionMod.invasion_force_next")
    ctx.run_until(lambda: bool(tracker(ctx)), 30, what="the raid record")
    last_key, polls, elapsed = None, 0, 0
    census_before = ctx.actions.sack_census()
    note(ctx, "start", raid=tracker(ctx), buildings=census_before["buildings"], stock=census_before["stock"]["total"])
    while elapsed < DAY_LIMIT * 40 + 120:
        ctx.popups()
        ctx.time.run_game_seconds(POLL_GAME_S, speed=SPEED)
        elapsed += POLL_GAME_S
        polls += 1
        raid, sack = tracker(ctx), ctx.mod.command("InvasionMod.sack_state")
        key = (raid.get("leave_reason"), raid.get("state"), sack["sack_count"])
        if key != last_key or polls % 12 == 0:
            census = ctx.actions.sack_census()
            note(ctx, f"t+{elapsed}", key=key, raid={k: raid.get(k) for k in ("state", "living", "leaving", "leave_reason", "loot", "burned")},
                 sack_history=sack["history"], buildings=census["buildings"], stock=census["stock"]["total"], raiders=raiders(ctx))
            last_key = key
        if sack["sack_count"] >= 1 or (raid.get("state") not in (None, "active") and raid.get("leave_reason") in ("losses",)):
            break
    for extra in range(3):
        ctx.time.run_game_seconds(20, speed=SPEED)
        census = ctx.actions.sack_census()
        note(ctx, f"after+{(extra + 1) * 20}", buildings=census["buildings"], stock=census["stock"]["total"], raiders=raiders(ctx))
    return ctx.result()
