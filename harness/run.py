"""Run one test iteration and write runs/<id>/summary.json (spec 03).

--scenario <name> runs the real game. --fake <outcome> runs fake phases without a game.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from runlib import paks
from runlib.extra_env import EnvOptionError, masked_for_config, parse_env_options
from runlib.fake_phases import OUTCOMES, build_fake_phases
from runlib.runfolder import (
    IterationLimitError,
    RunLock,
    RunLockedError,
    bump_iterations,
    create_run_folder,
    write_config,
)
from runlib.fixtures import DEFAULT_FIXTURE, FixtureError
from runlib.game import DEFAULT_TELEMETRY_INTERVAL_S
from runlib.phases import build_real_phases
from runlib.runner import Phase, execute_run
from runlib.scenario import list_scenarios
from runlib.summary import EXIT_CODES

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PAK_CONFIG = Path(__file__).resolve().parent / "pakmod.local.json"
DEFAULT_MAX_RUNS = 100  # a safety rail for unattended loops. Delete runs/.iterations to reset the counter.
TEST_SAVE = "saveGame_0"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one test iteration.")
    parser.add_argument("--fake", choices=OUTCOMES, help="use fake phases with this outcome (no game)")
    parser.add_argument("--scenario", help=f"run the real game with this scenario. Known: {sorted(list_scenarios())}")
    parser.add_argument("--list-scenarios", action="store_true", help="print the scenarios and their time limits, then exit")
    parser.add_argument("--include-test-scenarios", action="store_true", help="with --list-scenarios: also list the hidden selftest scenarios")
    parser.add_argument("--fixture", default=DEFAULT_FIXTURE,
                        help="save fixture to start from (harness/fixtures/fixtures.json, default %(default)s). "
                             "It is copied into the private appdata folder of the run, never next to the user's saves")
    parser.add_argument("--pak", action="append", default=[], metavar="NAME",
                        help="install the built harness pak NAME (from the pakmod work folder) before the game starts and "
                             "remove it at the end, also after a crash. Repeatable (spec 10, A/B variants)")
    parser.add_argument("--pak-config", type=Path, default=DEFAULT_PAK_CONFIG,
                        help="pakmod config that names the work folder of the paks (default %(default)s)")
    parser.add_argument("--env", action="append", default=[], metavar="KEY=VALUE",
                        help="extra environment variable for the game process. Name: ^[A-Z][A-Z0-9_]{0,63}$, not starting with "
                             "HARNESS_RUN_DIR, LOCALAPPDATA, PATH or UE4SS_BRIDGE. Value: printable, no newline. Repeatable")
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


def check_variant_options(args: argparse.Namespace) -> None:
    """Check --pak and --env before any lock or folder exists. Store the parsed env on args."""
    args.extra_env = parse_env_options(args.env)
    args.pak_names = [paks.check_name(name) for name in args.pak]
    if len(set(args.pak_names)) != len(args.pak_names):
        raise paks.PakError("a --pak name is given twice")
    if args.fake and (args.pak_names or args.extra_env):
        raise ValueError("--pak and --env need --scenario. A fake run has no game.")


def build_phases(args: argparse.Namespace) -> list[Phase]:
    if args.fake:
        return build_fake_phases(args.fake)
    work_dir = paks.work_dir_from_config(args.pak_config) if args.pak_names else None
    return build_real_phases(args.scenario, keep_open=args.keep_open, test_save=TEST_SAVE,
                             telemetry_interval_s=args.telemetry_interval, fixture=args.fixture,
                             pak_names=args.pak_names, pak_work_dir=work_dir, extra_env=args.extra_env)


def build_config(args: argparse.Namespace, run, phases: list[Phase], lock) -> dict:
    return {
        "run_id": run.run_id,
        "scenario": f"fake-{args.fake}" if args.fake else args.scenario,
        "fake_outcome": args.fake,
        "test_save": None if args.fake else TEST_SAVE,
        "fixture": None if args.fake else args.fixture,
        "private_appdata": not args.fake,
        "keep_open": args.keep_open,
        "telemetry_interval_s": None if args.fake else args.telemetry_interval,
        "limits_s": {phase.name: phase.time_limit_s for phase in phases},
        "max_runs": args.max_runs,
        "paks": args.pak_names,
        "env": masked_for_config(args.extra_env),
        # Keys only: the summary must stay short and must not repeat a value that could be a secret.
        "environment": {"env_keys": sorted(args.extra_env)} if args.extra_env else {},
        "start_notes": [f"took over a stale run lock from dead process {lock.took_over_pid}"]
        if lock.took_over_pid
        else [],
    }


def run_one(args: argparse.Namespace) -> int:
    try:
        check_variant_options(args)
        phases = build_phases(args)  # a wrong scenario name fails here, before any lock or folder
    except (ValueError, FixtureError, EnvOptionError, paks.PakError) as error:
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
