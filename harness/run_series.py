"""Run the launcher N times in a row and print a table (spec 03).

  .venv\Scripts\python.exe harness\run_series.py --scenario smoke --runs 5

Writes runs/series-<time>.json. Exit code: 0 if every run passed, otherwise 1.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from runlib.runfolder import atomic_write_text
from runlib.series import format_table, run_series, tally

HARNESS_DIR = Path(__file__).resolve().parent
RUNS_ROOT = HARNESS_DIR.parent / "runs"
MAX_SERIES_RUNS = 20


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Run the launcher several times.")
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--max-runs", type=int, help="pass the iteration cap on to run.py")
    args = parser.parse_args(argv)
    if not 1 <= args.runs <= MAX_SERIES_RUNS:
        print(f"--runs must be 1 to {MAX_SERIES_RUNS}.", file=sys.stderr)
        return 4
    extra = ["--max-runs", str(args.max_runs)] if args.max_runs else []

    rows = run_series(HARNESS_DIR / "run.py", args.scenario, args.runs, extra)
    counts = tally(rows)
    print()
    print(format_table(rows))
    print(f"\nVerdicts: {counts}")

    RUNS_ROOT.mkdir(exist_ok=True)
    out_path = RUNS_ROOT / f"series-{datetime.now(timezone.utc):%Y%m%d-%H%M%S}.json"
    atomic_write_text(out_path, json.dumps({"scenario": args.scenario, "verdicts": counts, "rows": rows}, indent=2))
    print(f"Results: {out_path}")
    return 0 if counts.get("pass") == len(rows) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
