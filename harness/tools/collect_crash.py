"""Copy crash reports of a run's game into runs/<id>/crash/, after the run ended.

Use it when a `--keep-open` game crashed after the collect phase:
    uv run python harness\\tools\\collect_crash.py runs\\<id>

Exit code: 0 done (also when nothing new was found), 1 the run has no game record.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from runlib.game import GameInstall  # noqa: E402
from runlib.latecrash import LateCrashError, collect_late_crashes  # noqa: E402


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Copy late crash reports into a run folder.")
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args(argv)
    try:
        result = collect_late_crashes(GameInstall(), args.run_dir.resolve())
    except LateCrashError as error:
        print(json.dumps({"error": str(error)}))
        return 1
    print(json.dumps(result, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
