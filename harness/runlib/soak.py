"""Samples and numbers for a long run at high speed (spec 10, U9 and criterion Q1). Pure code, no game.

A sample is taken at each poll of `ctx.run_until`: wall time, game clock, `daysTotal` and the memory of the game process.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from .waiting import ScenarioFailure

MB = 1024 * 1024
MIN_PROGRESS_S = 0.001  # a clock change below this is "no progress" (a pause or a pop-up)


@dataclass(frozen=True)
class Sample:
    wall_s: float
    clock: float
    days_total: int
    rss_mb: float | None


class GameOver(ScenarioFailure):
    """The game reports a victory status other than "playing" (for example the defeat screen)."""


VICTORY_STATUS_PLAYING = 0  # BP_MLGameInstance_C.currentGameVictoryStatus while the game goes on


def check_game_over(status: int, days_total: int) -> None:
    """Raise GameOver with a clear message when the status is not "playing". A defeat stops the clock for good."""
    if status != VICTORY_STATUS_PLAYING:
        raise GameOver(f"game over: currentGameVictoryStatus is {status} at daysTotal {days_total}. "
                       "The settlement was defeated (starved), so a longer run is not possible without feeding it.")


class Feeder:
    """Callable for `on_poll`. Gives food every `every_days` game days, so the start village does not starve.

    The base fixture starves and is defeated at about day 137 (spike S8). `give` adds the goods.
    """

    def __init__(self, every_days: int, give: Callable[[], None], first_day: int):
        self._every = every_days
        self._give = give
        self._last = first_day
        self.times = 0

    def __call__(self, days_total: int) -> bool:
        if days_total - self._last < self._every:
            return False
        self._give()
        self._last = days_total
        self.times += 1
        return True


def process_memory_mb(processes: Iterable) -> float | None:
    """The working set of the game processes in MB (psutil process objects). None if no process answers."""
    total, seen = 0, False
    for process in processes:
        try:
            total += process.memory_info().rss
            seen = True
        except Exception:  # noqa: BLE001 - a process that ended is a crash, and the scenario reports that itself
            continue
    return round(total / MB, 1) if seen else None


def running_rate(samples: list[Sample]) -> float | None:
    """Game seconds for each wall second, counted only over sample gaps where the clock moved.

    A gap with a pop-up or a pause does not lower the rate. Those gaps are counted by `stalled_gaps`.
    """
    game_s = wall_s = 0.0
    for before, after in zip(samples, samples[1:]):
        moved = after.clock - before.clock
        if moved > MIN_PROGRESS_S:
            game_s += moved
            wall_s += after.wall_s - before.wall_s
    return round(game_s / wall_s, 2) if wall_s > 0 else None


def overall_rate(samples: list[Sample]) -> float | None:
    """Game seconds for each wall second over the whole run, stalls included."""
    if len(samples) < 2 or samples[-1].wall_s <= samples[0].wall_s:
        return None
    return round((samples[-1].clock - samples[0].clock) / (samples[-1].wall_s - samples[0].wall_s), 2)


def stalled_gaps(samples: list[Sample]) -> int:
    return sum(1 for before, after in zip(samples, samples[1:]) if after.clock - before.clock <= MIN_PROGRESS_S)


def longest_stall_s(samples: list[Sample]) -> float:
    """The longest wall time in a row with no clock progress."""
    longest = current = 0.0
    for before, after in zip(samples, samples[1:]):
        if after.clock - before.clock <= MIN_PROGRESS_S:
            current += after.wall_s - before.wall_s
            longest = max(longest, current)
        else:
            current = 0.0
    return round(longest, 1)


class Sampler:
    """Callable for `on_poll`. Reads the game through functions, so tests can use fakes."""

    def __init__(self, monotonic: Callable[[], float], read_clock: Callable[[], float],
                 read_days: Callable[[], int], read_memory_mb: Callable[[], float | None]):
        self._monotonic = monotonic
        self._read = (read_clock, read_days, read_memory_mb)
        self._started = monotonic()
        self.samples: list[Sample] = []

    def __call__(self) -> Sample:
        read_clock, read_days, read_memory = self._read
        sample = Sample(round(self._monotonic() - self._started, 2), read_clock(), read_days(), read_memory())
        self.samples.append(sample)
        return sample
