"""A fake game API for testing Lua mods without the game. See README.md in this folder."""

from .clock import FakeGameClock
from .game import FakeGame
from .manorlords import build_manor_lords_state

__all__ = ["FakeGame", "FakeGameClock", "build_manor_lords_state"]
