"""Start the game with a save and leave it open (spec 06, part D).

    .venv\\Scripts\\python.exe harness\\tools\\load_save.py manor-bailey              a fixture name (harness/fixtures/fixtures.json)
    .venv\\Scripts\\python.exe harness\\tools\\load_save.py D:\\saves\\saveGame_5.sav    a save file (its _descr.sav must be next to it)

It runs `run.py --scenario noop --keep-open` with `--fixture` or `--save`. The run installs the save into the user's save folder under
a free slot name (`saveGame_<max+1>`), the game loads it, and HarnessBoot checks that the loaded slot is the wanted one.
The game stays open and paused. Close it with `harness\\game-close.ps1`. The next run removes the installed slot, or run
`harness\\tools\\fixtures.py uninstall`. Extra arguments go to run.py (for example `--run-id NAME`).
Exit code: the exit code of run.py.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HARNESS = Path(__file__).resolve().parent.parent


def run_args(target: str, extra: list[str]) -> list[str]:
    choice = ["--save", target] if target.lower().endswith(".sav") else ["--fixture", target]
    return [sys.executable, str(HARNESS / "run.py"), "--scenario", "noop", "--keep-open", *choice, *extra]


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if argv else 2
    return subprocess.run(run_args(argv[0], argv[1:]), cwd=HARNESS.parent).returncode


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
