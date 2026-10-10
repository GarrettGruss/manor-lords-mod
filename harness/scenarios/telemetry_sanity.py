"""Run the game for 40 seconds at speed 1, then check the telemetry samples and a snapshot."""

from runlib.telemetry import missing_fields

NAME = "telemetry-sanity"
DESCRIPTION = "Run 40 game seconds at speed 1. Check the telemetry samples: fields, spacing, ranges, and a snapshot."
LIMIT_S = 120
RUN_GAME_SECONDS = 40
SPEED = 1
INTERVAL_RANGE_S = (3, 7)  # the mod samples every 5 s. The timestamps have a resolution of 1 s.
EXPECTED_REGIONS = 7
SETTLE_WAIT_S = 15  # the mod needs up to one interval to write a sample taken after the pause


def _spacing(samples: list[dict]) -> list[int]:
    return [later["t"] - earlier["t"] for earlier, later in zip(samples, samples[1:])]


def _all_regions(samples: list[dict], key: str) -> list[float]:
    return [region[key] for sample in samples for region in sample["regions"] if region.get(key) is not None]


def _stable_view(sample: dict) -> dict:
    """The fields that must be equal when the game is paused: names, flags, date and the player."""
    return {
        "date": sample["date"],
        "player": sample["player"],
        "regions": [(r["name"], r["settled"], r["population"]) for r in sample["regions"]],
    }


def _paused_sample_after(ctx, clock_end: float):
    samples = ctx.telemetry.read()
    found = [s for s in samples if s.get("paused") is True and isinstance(s.get("clock"), (int, float)) and s["clock"] >= clock_end - 0.01]
    return found[-1] if found else None


def run(ctx) -> dict:
    expect = ctx.expect
    record = ctx.time.run_game_seconds(RUN_GAME_SECONDS, speed=SPEED)
    moved = record["clock_end"] - record["clock_start"]
    # The sampler must not slow the game: the clock keeps its rate of 1 game second for each wall second.
    expect.in_range("clock rate while sampling", moved / record["wall_s"], 0.85, 1.15)

    samples = ctx.telemetry.window(record["clock_start"], record["clock_end"])
    expect.at_least("samples while running", len(samples), 5)
    expect.equals("fields missing in samples", sorted({name for s in samples for name in missing_fields(s)})[:5], [])
    expect.equals("read errors in samples", sorted({e for s in samples for e in s.get("errors", [])})[:3], [])
    gaps = _spacing(samples) or [0]
    expect.in_range("shortest gap between samples (s)", min(gaps), *INTERVAL_RANGE_S)
    expect.in_range("longest gap between samples (s)", max(gaps), *INTERVAL_RANGE_S)

    last = samples[-1]
    expect.equals("region count", len(last["regions"]), EXPECTED_REGIONS)
    for key in ("approval", "publicOrder"):
        values = _all_regions(samples, key)
        expect.in_range(f"lowest {key}", min(values), 0, 100)
        expect.in_range(f"highest {key}", max(values), 0, 100)
    for key, value in last["player"].items():
        expect.at_least(f"player {key} is not negative", value, 0)

    expect.eventually("a sample taken after the pause", lambda: _paused_sample_after(ctx, record["clock_end"]), SETTLE_WAIT_S)
    after_pause = _paused_sample_after(ctx, record["clock_end"])
    if after_pause:
        expect.equals("snapshot equals the last sample", _stable_view(ctx.snapshot()) == _stable_view(after_pause), True)
    return ctx.result()
