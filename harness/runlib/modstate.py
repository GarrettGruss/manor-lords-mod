"""Observe and drive the state that a mod defines (spec 10, U10).

A mod adds commands with HarnessCommands.register and metrics with HarnessCommands.metric.
Every mod serves them itself, in its own Lua state, through the folder `<run>/modcmd/<ModName>/`.
`ModState` sends commands there, and reads metrics with the built-in command `harness.metrics`.
Names follow one rule: `<ModName>.<name>`. See docs/harness/10-invasion-testability/implementation-notes/mod-state-contract.md.

A metric is read from the mod when you ask, so it is always current (a read is one command round trip, about 0.1 s).
"""

from __future__ import annotations

import re
import time
from typing import Any, Callable

from .commands import CommandRefused, ModCommandChannel

NAME_RULE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*\.[A-Za-z][A-Za-z0-9_]*$")
MOD_RULE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
POLL_S = 0.5
DEFAULT_WAIT_S = 15.0
_MISSING = object()


class ModCommandError(Exception):
    """The mod refused a command. `reason` is the message of the mod."""

    def __init__(self, command: str, reason: str):
        super().__init__(f"{command}: {reason}")
        self.command = command
        self.reason = reason


class ModMetricError(Exception):
    """A metric is missing, or it did not reach the wanted value in time."""


def check_name(name: str) -> None:
    if not isinstance(name, str) or not NAME_RULE.fullmatch(name):
        raise ValueError(f"bad name {name!r}: use <ModName>.<name>, letters, digits and underscore, a letter first")


def check_mod_name(mod: str) -> None:
    if not isinstance(mod, str) or not MOD_RULE.fullmatch(mod):
        raise ValueError(f"bad mod name {mod!r}: letters, digits and underscore, a letter first")


def mod_of(name: str) -> str:
    """The mod name in a command or metric name: the text before the first dot."""
    check_name(name)
    return name.split(".", 1)[0]


class ModState:
    """`ctx` needs `mod_commands` (a ModCommandChannel) and `ensure_alive`.

    `sleep` and `monotonic` are parameters so tests can use a fake clock.
    """

    def __init__(self, ctx, sleep: Callable[[float], None] = time.sleep, monotonic: Callable[[], float] = time.monotonic):
        self._ctx = ctx
        self._sleep = sleep
        self._monotonic = monotonic
        self._started = monotonic()
        self._history: list[dict] = []
        self._errors: dict = {}

    # ---- commands ----

    @property
    def _channel(self) -> ModCommandChannel:
        return self._ctx.mod_commands

    def command(self, name: str, **args: Any) -> Any:
        """Run a mod command and return its result. Raise ModCommandError with the message of the mod when it refuses.

        A missing answer (the mod is not loaded, or the game stalls) raises ModDidNotAnswer from the channel.
        """
        mod = mod_of(name)
        self._ctx.ensure_alive()
        try:
            answer = self._channel.send(mod, name, args)
        except CommandRefused as refused:
            raise ModCommandError(name, refused.reason) from refused
        return answer.get("result")

    def refusal(self, name: str, **args: Any) -> str | None:
        """Run a command that the mod should refuse. Return the message of the mod, or None when it accepted the command.

        Why: a test of a rule often needs "this must be refused". The command still runs, so an accepted command changes state.
        """
        try:
            self.command(name, **args)
        except ModCommandError as error:
            return error.reason
        return None

    def commands(self, mod: str) -> list[dict]:
        """The commands that a mod registered: [{"name", "args": {argument: rule}}], sorted by name."""
        check_mod_name(mod)
        self._ctx.ensure_alive()
        return self._channel.send(mod, "harness.list_commands")["result"]["commands"]

    # ---- metrics ----

    def read_metrics(self, mod: str) -> dict:
        """Read all metrics of a mod now: {name: value}. Each read is also kept for `metrics_window`."""
        check_mod_name(mod)
        self._ctx.ensure_alive()
        result = self._channel.send(mod, "harness.metrics")["result"]
        self._errors = result.get("errors") or {}
        values = dict(result.get("metrics") or {})
        self._history.append({"t": self._monotonic() - self._started, "values": values})
        return values

    def metric(self, name: str, default: Any = _MISSING) -> Any:
        """The current value of a metric, read from the mod now.

        A metric that the mod does not have raises ModMetricError, or gives `default`. A mod that does not answer raises an error.
        """
        values = self.read_metrics(mod_of(name))
        if name in values:
            return values[name]
        if default is not _MISSING:
            return default
        problem = self._errors.get(name)
        detail = f" (the metric function failed: {problem})" if problem else ""
        raise ModMetricError(f"the mod does not report the metric {name}{detail}. Did it call HarnessCommands.metric?")

    def wait_metric(self, name: str, predicate: Callable[[Any], bool], timeout_s: float = DEFAULT_WAIT_S) -> Any:
        """Wait until `predicate(value)` is true for the current value of the metric. Return that value.

        Raise ModMetricError at the timeout. The message holds the last value.
        """
        started = self._monotonic()
        while True:
            self._ctx.ensure_alive()
            value = self.metric(name, None)
            if value is not None and predicate(value):
                return value
            if self._monotonic() - started >= timeout_s:
                raise ModMetricError(f"metric {name} did not reach the wanted value in {timeout_s:g} s (last value: {value!r})")
            self._sleep(POLL_S)

    def metrics_window(self, names: list[str] | None = None, start_s: float | None = None,
                       end_s: float | None = None) -> list[dict]:
        """The metric reads of this run so far: [{"t", "values": {name: value}}], one row for each read.

        `t` is the time in seconds since the scenario made `ctx.mod`. The mod keeps no history, so a row exists only
        when a scenario read the metrics (with `metric`, `wait_metric` or `read_metrics`). `names` and the time range limit the rows.
        """
        for name in names or []:
            check_name(name)
        rows = []
        for row in self._history:
            if (start_s is not None and row["t"] < start_s) or (end_s is not None and row["t"] > end_s):
                continue
            values = {key: value for key, value in row["values"].items() if names is None or key in names}
            rows.append({"t": row["t"], "values": values})
        return rows
