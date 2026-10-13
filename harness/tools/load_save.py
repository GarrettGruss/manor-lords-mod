"""Start the game with a save, or in a fresh new game, and leave it open (spec 06, parts D and E).

    uv run python harness/tools/load_save.py manor-bailey              a fixture name (harness/fixtures/fixtures.json)
    uv run python harness/tools/load_save.py D:/saves/saveGame_5.sav   a save file (its _descr.sav must be next to it)
    uv run python harness/tools/load_save.py --new-game [--map Jagged_Cliffs]   a fresh new game, no save is loaded

It runs `run.py --scenario noop --keep-open` with `--fixture`, `--save` or `--new-game`. A save run installs the save into the
user's save folder under a free slot name (`saveGame_<max+1>`), the game loads it, and HarnessBoot checks that the loaded slot is the
wanted one. A fresh start installs nothing: HarnessBoot opens the map with no slot, pushes the autosave timer away and pauses.
The game stays open and paused. Close it with the `stop_game` MCP tool or `harness/game-close.ps1`. The next run removes an
installed slot, or run `harness/tools/fixtures.py uninstall`. Extra arguments go to run.py (for example `--run-id NAME`).
Exit code: the exit code of run.py.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HARNESS = Path(__file__).resolve().parent.parent


def run_args(target: str | None, extra: list[str]) -> list[str]:
    """The run.py command. `target` None means a fresh start: `--new-game` and `--map` are in `extra`."""
    base = [sys.executable, str(HARNESS / "run.py"), "--scenario", "noop", "--keep-open"]
    if target is None:
        return [*base, "--new-game", *extra]
    choice = ["--save", target] if target.lower().endswith(".sav") else ["--fixture", target]
    return [*base, *choice, *extra]


def split_arguments(argv: list[str]) -> tuple[str | None, list[str]]:
    """Return (target, extra). `--new-game` in argv gives target None."""
    if "--new-game" in argv:
        extra = [arg for arg in argv if arg != "--new-game"]
        return None, extra
    return argv[0], argv[1:]


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if argv else 2
    target, extra = split_arguments(argv)
    return subprocess.run(run_args(target, extra), cwd=HARNESS.parent).returncode


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
