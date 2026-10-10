"""Probe for spec 02: why does the game fall back to 1x after changeGameSpeed?

Needs the temporary mod HarnessProbeClock (its hooks log who sets the speed). It writes `probe.jsonl`
in the run folder. Read `mod.log` next to it. Not a test: it never fails on a game answer.
"""

import json
import time

NAME = "probe-speed-fallback"
LIMIT_S = 90
HIDDEN = True
OBSERVE_S = 9.0
SAMPLE_S = 0.5


def _sample(ctx, started: float) -> dict:
    bridge = ctx.bridge
    return {
        "t": round(time.monotonic() - started, 2),
        "clock": bridge.read_clock_value(),
        "gameSpeed": bridge.read_game_speed(),
        "bIsPlayerPaused": bridge.read_property(bridge.player_path(), "bIsPlayerPaused"),
    }


def _observe(ctx, label: str, handle) -> None:
    started = time.monotonic()
    while time.monotonic() - started < OBSERVE_S:
        handle.write(json.dumps({"phase": label, **_sample(ctx, started)}) + "\n")
        handle.flush()
        time.sleep(SAMPLE_S)


def run(ctx) -> dict:
    bridge = ctx.bridge
    with (ctx.run_dir / "probe.jsonl").open("w", encoding="utf-8") as handle:
        ctx.log.info("PROBE unPauseGame")
        handle.write(json.dumps({"unpause": bridge.unpause(5.0)}) + "\n")
        ctx.log.info("PROBE changeGameSpeed(3)")
        bridge.call_on_player("changeGameSpeed", [3, False])
        _observe(ctx, "after changeGameSpeed(3)", handle)
        ctx.log.info("PROBE changeGameSpeed(3) again")
        bridge.call_on_player("changeGameSpeed", [3, False])
        _observe(ctx, "after second changeGameSpeed(3)", handle)
    ctx.time.pause()
    return ctx.result()
