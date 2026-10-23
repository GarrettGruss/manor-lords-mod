"""Spike scenario (change spike-public-order-factor, #403, route A): hold Region.publicOrder by a write on every tick.

Run with `--env ORDER_TARGET=<n>`: n 0..100 holds that value, -1 only reads (control). 10 game days at speed 3.
The mod OrderProbe samples every 100 ms (real time) and writes the stats. Never calls a save function.
"""
import json

NAME = "probe-order-tick-write"
DESCRIPTION = "Spike: hold the region public order with a write on every tick; flicker rate and effect (route A)."
COVERS: list[str] = []
HIDDEN = True
LIMIT_S = 900
LONG_REASON = "10 game days at speed 3 with a 100 ms sampler."
PREFIX = "OrderProbe."


def run(ctx) -> dict:
    cmd = lambda name, **a: ctx.mod.command(PREFIX + name, **a)  # noqa: E731
    target = int(ctx.variant_option("ORDER_TARGET", "-1"))
    ctx.log.info(f"now {cmd('now')}")
    ctx.screenshot("start")
    ctx.log.info(f"hold {cmd('hold', target=target)}")
    ctx.time.run_game_days(5, speed=3)
    ctx.screenshot("day5")
    ctx.time.run_game_days(5, speed=3)
    ctx.screenshot("day10")
    stats = cmd("stats")
    cmd("stop")
    (ctx.run_dir / "order_stats.json").write_text(json.dumps(stats, indent=1), encoding="utf-8")
    ctx.log.info(f"stats ticks {stats['ticks']} own {stats['own']} other {stats['other']}")
    ctx.metric("ticks", stats["ticks"])
    ctx.metric("own", stats["own"])
    ctx.metric("other", stats["other"])
    return ctx.result()
