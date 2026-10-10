"""Extra environment variables for the game process: `run.py --env KEY=VALUE` (spec 10, U4).

An A/B variant can switch a mod feature through an environment variable. The rules keep a variant
from changing how the harness itself works (run folder, private appdata, path, bridge).
"""

from __future__ import annotations

import re

NAME_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{0,63}$")
MAX_VALUE_CHARS = 256
# A name that starts with one of these is refused: the harness owns these variables.
FORBIDDEN_PREFIXES = ("HARNESS_RUN_DIR", "LOCALAPPDATA", "PATH", "UE4SS_BRIDGE")
# The harness sets these in build_game_environment. They are refused too, so a variant cannot turn the harness off.
HARNESS_OWNED = ("HARNESS_AUTOBOOT", "HARNESS_TEST_SAVE", "HARNESS_TELEMETRY_INTERVAL_S")
SECRET_WORDS = ("KEY", "TOKEN", "SECRET", "PASSWORD")


class EnvOptionError(ValueError):
    """A --env option is not allowed. The message says why."""


def check_env_entry(name: str, value: str) -> None:
    if not NAME_PATTERN.fullmatch(name):
        raise EnvOptionError(f"bad environment name {name!r}: use A-Z, 0-9 and _, start with a letter, at most 64 characters")
    if name.startswith(FORBIDDEN_PREFIXES) or name in HARNESS_OWNED:
        raise EnvOptionError(f"environment name {name!r} is reserved for the harness")
    if len(value) > MAX_VALUE_CHARS or not value.isprintable():
        raise EnvOptionError(f"bad value for {name}: use printable characters, no newline, at most {MAX_VALUE_CHARS}")


def parse_env_options(options: list[str]) -> dict[str, str]:
    """Turn ['A=1', 'B=x'] into a checked dict. A name given twice is an error."""
    result: dict[str, str] = {}
    for option in options:
        name, separator, value = option.partition("=")
        if not separator:
            raise EnvOptionError(f"--env needs KEY=VALUE, got {option!r}")
        check_env_entry(name, value)
        if name in result:
            raise EnvOptionError(f"environment name {name} is given twice")
        result[name] = value
    return result


def is_secret_name(name: str) -> bool:
    return any(word in name for word in SECRET_WORDS)


def masked_for_config(env: dict[str, str]) -> dict[str, str]:
    """The env for config.json. The value of a secret-looking name is hidden."""
    return {name: "***" if is_secret_name(name) else value for name, value in env.items()}
