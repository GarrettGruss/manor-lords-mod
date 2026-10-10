"""Fake phases for tests and for `run.py --fake`. They need no game.

They use the real phase names and write small files like the real game would.
"""

from __future__ import annotations

import json
import time

from .runner import Phase, PhaseContext, PhaseFailed

OUTCOMES = ("pass", "fail", "crash", "timeout", "harness_error")
FAKE_TIMEOUT_LIMIT_S = 0.3  # tiny, so the timeout outcome is fast
FAKE_TIMEOUT_SLEEP_S = 1.5


def _write_json(path, data) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _log(ctx: PhaseContext, line: str) -> None:
    with (ctx.run.path / "mod.log").open("a", encoding="utf-8") as log_file:
        log_file.write(line + "\n")


def _preflight(outcome: str):
    def run(ctx: PhaseContext) -> str | None:
        if outcome == "harness_error":
            raise RuntimeError("Steam is not running (fake preflight failure)")
        return None

    return run


def _deploy(ctx: PhaseContext) -> str | None:
    ctx.config.setdefault("environment", {})["mods"] = {"HarnessBoot": "fake-sha256"}
    return None


def _launch(ctx: PhaseContext) -> str | None:
    _log(ctx, "fake game started")
    return None


def _boot(ctx: PhaseContext) -> str | None:
    boot = {"state": "READY", "pause_calls": 2}
    _write_json(ctx.run.boot_path, boot)
    ctx.state["boot"] = boot
    return None


def _scenario(outcome: str):
    def run(ctx: PhaseContext) -> str | None:
        shot = ctx.run.screenshots_dir / "start.png.txt"
        shot.write_text("fake screenshot", encoding="utf-8")
        if outcome == "timeout":
            time.sleep(FAKE_TIMEOUT_SLEEP_S)
        if outcome == "crash":
            _log(ctx, "fake game died")
            ctx.state["crash"] = {"reason": "the game process ended during scenario", "exit_code": -1073741819}
            raise ConnectionError("lost the connection to the game")
        passed = outcome != "fail"
        result = {
            "passed": passed,
            "asserts": [{"name": "clock moves", "ok": passed, "value": 1 if passed else 0, "range": [0, 5]}],
        }
        _write_json(ctx.run.path / "scenario.json", result)
        ctx.state["scenario_result"] = result
        if not passed:
            raise PhaseFailed("assert 'clock moves' failed")
        return None

    return run


def _collect(ctx: PhaseContext) -> str | None:
    screenshots = sorted(path.relative_to(ctx.run.path).as_posix() for path in ctx.run.screenshots_dir.iterdir())
    logs = sorted(path.name for path in ctx.run.path.glob("*.log"))
    if ctx.state["crash"]:
        (ctx.run.crash_dir / "crash.txt").write_text("fake crash report", encoding="utf-8")
    ctx.state["artifacts"] = {"screenshots": screenshots, "logs": logs}
    return None


def _teardown(ctx: PhaseContext) -> str | None:
    ctx.state["game_stop_requested"] = True
    return None


def build_fake_phases(outcome: str) -> list[Phase]:
    if outcome not in OUTCOMES:
        raise ValueError(f"Unknown fake outcome {outcome!r}. Use one of {OUTCOMES}.")
    scenario_limit = FAKE_TIMEOUT_LIMIT_S if outcome == "timeout" else 5
    return [
        Phase("preflight", _preflight(outcome), 5),
        Phase("deploy", _deploy, 5),
        Phase("launch", _launch, 5),
        Phase("boot", _boot, 5),
        Phase("scenario", _scenario(outcome), scenario_limit),
        Phase("collect", _collect, 5, always_run=True),
        Phase("teardown", _teardown, 5, always_run=True),
    ]
