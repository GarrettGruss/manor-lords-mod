"""Run one test iteration and write runs/<id>/summary.json (spec 03).

Only fake phases exist now. The real game phases come later.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from runlib.fake_phases import OUTCOMES, build_fake_phases
from runlib.runfolder import (
    IterationLimitError,
    RunLock,
    RunLockedError,
    bump_iterations,
    create_run_folder,
    write_config,
)
from runlib.runner import execute_run
from runlib.summary import EXIT_CODES

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MAX_RUNS = 20


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one test iteration.")
    parser.add_argument("--fake", choices=OUTCOMES, help="use fake phases with this outcome (required for now)")
    parser.add_argument("--run-id", help="use this run id instead of a generated one")
    parser.add_argument("--runs-root", type=Path, default=REPO_ROOT / "runs")
    parser.add_argument("--max-runs", type=int, default=DEFAULT_MAX_RUNS, help="cap on runs in this runs folder")
    return parser.parse_args(argv)


def fail_before_run(message: str) -> int:
    # No run folder exists yet, so there is no summary.json to write.
    print(f"harness_error: {message}", file=sys.stderr)
    return EXIT_CODES["harness_error"]


def run_one(args: argparse.Namespace) -> int:
    try:
        with RunLock(args.runs_root) as lock:
            bump_iterations(args.runs_root, args.max_runs)
            run = create_run_folder(args.runs_root, args.run_id)
            config = {
                "run_id": run.run_id,
                "scenario": f"fake-{args.fake}",
                "fake_outcome": args.fake,
                "max_runs": args.max_runs,
                "environment": {},
                "start_notes": [f"took over a stale run lock from dead process {lock.took_over_pid}"]
                if lock.took_over_pid
                else [],
            }
            write_config(run, config)
            summary = execute_run(run, config, build_fake_phases(args.fake))
    except (RunLockedError, IterationLimitError, FileExistsError) as error:
        return fail_before_run(str(error))
    print(f"{summary.run_id} {summary.verdict} reason={summary.reason or '-'} summary={run.summary_path}")
    return EXIT_CODES[summary.verdict]


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    if args.fake is None:
        return fail_before_run("--fake <outcome> is required. The real game phases are not built yet.")
    return run_one(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
