"""A fake game API for testing Lua mods without the game. See README.md in this folder."""

try:
    from .clock import FakeGameClock
    from .game import FakeGame
    from .manorlords import build_manor_lords_state
except ImportError as error:  # lupa is not installed
    # unittest discovery imports every package in harness/tests, also when the run does not need the kit.
    # Do not fail the whole discovery. A test that really needs the kit fails with the clear message below.
    _MISSING = str(error)

    def _needs_lupa(*args, **kwargs):
        raise ImportError(f"The fake game needs lupa. Run with: uv run --no-project --with lupa ... ({_MISSING})")

    FakeGame = FakeGameClock = build_manor_lords_state = _needs_lupa

__all__ = ["FakeGame", "FakeGameClock", "build_manor_lords_state"]
