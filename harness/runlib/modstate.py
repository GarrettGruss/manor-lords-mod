"""Observe and drive the state that a mod defines (spec 10, U10).

A mod adds commands with HarnessCommands.register and metrics with HarnessTelemetry.register.
`ModState` sends the commands through the HarnessActions command channel and reads the metrics from telemetry.jsonl.
Names follow one rule: `<ModName>.<name>`. See docs/specs/10-invasion-testability/implementation-notes/mod-state-contract.md.

A metric value is as old as the last telemetry sample (5 s of wall time by default). After a command,
use `wait_metric` and not `metric`. A command answer is always current.
"""

from __future__ import annotations

import re
import time
from typing import Any, Callable

from .commands import CommandChannel, CommandRefused

NAME_RULE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*\.[A-Za-z][A-Za-z0-9_]*$")
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


class ModState:
    """`ctx` needs `commands` (a CommandChannel), `telemetry` (a TelemetryReader) and `ensure_alive`.

    `sleep` and `monotonic` are parameters so tests can use a fake clock.
    """

    def __init__(self, ctx, sleep: Callable[[float], None] = time.sleep, monotonic: Callable[[], float] = time.monotonic):
        self._ctx = ctx
        self._sleep = sleep
        self._monotonic = monotonic

    # ---- commands ----

    @property
    def _channel(self) -> CommandChannel:
        return self._ctx.commands

    def command(self, name: str, **args: Any) -> Any:
        """Run a mod command and return its result. Raise ModCommandError with the message of the mod when it refuses.

        A missing answer (the mod is not loaded, or the game stalls) raises CommandError from the channel.
        """
        check_name(name)
        self._ctx.ensure_alive()
        try:
            answer = self._channel.send(name, args=args)
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

    def commands(self) -> list[dict]:
        """The registered commands: [{"name", "args": {argument: rule}}], sorted by name."""
        self._ctx.ensure_alive()
        return self._channel.send("harness.list_commands")["result"]["commands"]

    # ---- metrics ----

    def _samples(self) -> list[dict]:
        return self._ctx.telemetry.read()

    def metric(self, name: str, default: Any = _MISSING) -> Any:
        """The latest value of a custom metric. Without `default`, a metric that no sample holds raises ModMetricError."""
        check_name(name)
        for sample in reversed(self._samples()):
            custom = sample.get("custom") or {}
            if name in custom:
                return custom[name]
        if default is not _MISSING:
            return default
        raise ModMetricError(f"no telemetry sample holds the metric {name}. Is the mod loaded and the game in a map?")

    def wait_metric(self, name: str, predicate: Callable[[Any], bool], timeout_s: float = DEFAULT_WAIT_S) -> Any:
        """Wait until `predicate(value)` is true for the latest value of the metric. Return that value.

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

    def metrics_window(self, names: list[str] | None = None, start_clock: float | None = None,
                       end_clock: float | None = None) -> list[dict]:
        """Custom metric values over time: [{"clock", "date", "values": {name: value}}], one row per sample.

        `names` limits the metrics. The clocks limit the game clock range. Use it for rates and trends.
        """
        for name in names or []:
            check_name(name)
        rows = []
        for sample in self._samples():
            clock = sample.get("clock")
            if not isinstance(clock, (int, float)):
                continue
            if (start_clock is not None and clock < start_clock) or (end_clock is not None and clock > end_clock):
                continue
            custom = sample.get("custom") or {}
            values = {key: value for key, value in custom.items() if names is None or key in names}
            rows.append({"clock": clock, "date": sample.get("date"), "values": values})
        return rows
