# Source of `pause_calls`

Checked by review on 2026-10-18.

- `summary.boot.pause_calls` is not in `boot.json`. The launcher counts it.
- `harness/runlib/phases.py`, `_wait_for_boot`: when `boot.json` shows `READY` or `FAILED`, it calls `count_pause_calls(ctx.run.path / "mod.log")` and stores the number with `_boot_result`.
- `harness/runlib/game.py`, `count_pause_calls`: counts the lines of `mod.log` that contain `PAUSE_CALL_MARKER` ("calling pauseGame"). It retries a refused read (the mod keeps the log open).
- So the test scenario `boot-timing` reads the same number with `count_pause_calls(ctx.run.path / "mod.log")`. This answers the open question in design.md.
