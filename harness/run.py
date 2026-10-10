"""Run one test iteration and write runs/<id>/summary.json (spec 03).

--scenario <name> runs the real game. --fake <outcome> runs fake phases without a game.
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
from runlib.game import DEFAULT_TELEMETRY_INTERVAL_S
from runlib.phases import build_real_phases
from runlib.runner import Phase, execute_run
from runlib.scenario import list_scenarios
from runlib.summary import EXIT_CODES

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MAX_RUNS = 20
TEST_SAVE = "saveGame_0"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one test iteration.")
    parser.add_argument("--fake", choices=OUTCOMES, help="use fake phases with this outcome (no game)")
    parser.add_argument("--scenario", help=f"run the real game with this scenario. Known: {sorted(list_scenarios())}")
    parser.add_argument("--list-scenarios", action="store_true", help="print the scenarios and their time limits, then exit")
    parser.add_argument("--include-test-scenarios", action="store_true", help="with --list-scenarios: also list the hidden selftest scenarios")
    parser.add_argument("--keep-open", action="store_true", help="do not stop the game at the end")
    parser.add_argument("--telemetry-interval", type=float, default=DEFAULT_TELEMETRY_INTERVAL_S,
                        help="seconds between telemetry samples in the game (0 = off, default %(default)s)")
    parser.add_argument("--run-id", help="use this run id instead of a generated one")
    parser.add_argument("--runs-root", type=Path, default=REPO_ROOT / "runs")
    parser.add_argument("--max-runs", type=int, default=DEFAULT_MAX_RUNS, help="cap on runs in this runs folder")
    return parser.parse_args(argv)


def fail_before_run(message: str) -> int:
    # No run folder exists yet, so there is no summary.json to write.
    print(f"harness_error: {message}", file=sys.stderr)
    return EXIT_CODES["harness_error"]


def build_phases(args: argparse.Namespace) -> list[Phase]:
    if args.fake:
        return build_fake_phases(args.fake)
    return build_real_phases(args.scenario, keep_open=args.keep_open, test_save=TEST_SAVE,
                             telemetry_interval_s=args.telemetry_interval)


def build_config(args: argparse.Namespace, run, phases: list[Phase], lock) -> dict:
    return {
        "run_id": run.run_id,
        "scenario": f"fake-{args.fake}" if args.fake else args.scenario,
        "fake_outcome": args.fake,
        "test_save": None if args.fake else TEST_SAVE,
        "keep_open": args.keep_open,
        "telemetry_interval_s": None if args.fake else args.telemetry_interval,
        "limits_s": {phase.name: phase.time_limit_s for phase in phases},
        "max_runs": args.max_runs,
        "environment": {},
        "start_notes": [f"took over a stale run lock from dead process {lock.took_over_pid}"]
        if lock.took_over_pid
        else [],
    }


def run_one(args: argparse.Namespace) -> int:
    try:
        phases = build_phases(args)  # a wrong scenario name fails here, before any lock or folder
    except ValueError as error:
        return fail_before_run(str(error))
    try:
        with RunLock(args.runs_root) as lock:
            bump_iterations(args.runs_root, args.max_runs)
            run = create_run_folder(args.runs_root, args.run_id)
            config = build_config(args, run, phases, lock)
            write_config(run, config)
            summary = execute_run(run, config, phases)
    except (RunLockedError, IterationLimitError, FileExistsError) as error:
        return fail_before_run(str(error))
    print(f"{summary.run_id} {summary.verdict} reason={summary.reason or '-'} summary={run.summary_path}")
    return EXIT_CODES[summary.verdict]


def print_scenarios(include_hidden: bool) -> int:
    for name, info in list_scenarios(include_hidden).items():
        print(f"{name:<20} limit {info.limit_s:>5.0f} s  {info.summary}")
    return 0


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    if args.list_scenarios:
        return print_scenarios(args.include_test_scenarios)
    if (args.fake is None) == (args.scenario is None):
        return fail_before_run("exactly one of --fake <outcome> and --scenario <name> is required.")
    return run_one(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
