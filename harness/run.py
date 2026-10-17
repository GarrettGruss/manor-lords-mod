"""Run one test iteration and write runs/<id>/summary.json (spec 03).

--scenario <name> runs the real game. --fake <outcome> runs fake phases without a game.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from runlib import gameslots, paks
from runlib.extra_env import EnvOptionError, masked_for_config, parse_env_options
from runlib.fake_phases import OUTCOMES, build_fake_phases
from runlib.runfolder import (
    IterationLimitError,
    LockTimeoutError,
    RunLock,
    RunLockedError,
    bump_iterations,
    create_run_folder,
    default_max_runs,
    write_config,
)
from runlib.fixtures import DEFAULT_FIXTURE, FixtureError
from runlib.game import DEFAULT_TELEMETRY_INTERVAL_S
from runlib.phases import build_real_phases
from runlib.runner import Phase, execute_run
from runlib.scenario import list_scenarios
from runlib.summary import EXIT_CODES

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_NEW_GAME_MAP = "Jagged_Cliffs"
MAP_NAME = re.compile(r"^[A-Za-z0-9_]{1,64}$")
DEFAULT_PAK_CONFIG = Path(__file__).resolve().parent / "pakmod.local.json"


def parse_slot(text: str) -> int | None:
    """A slot number, or None for auto."""
    if text == "auto":
        return None
    if not text.isdigit() or not 0 <= int(text) <= gameslots.MAX_SLOT:
        raise argparse.ArgumentTypeError(f"slot must be 0 to {gameslots.MAX_SLOT} or auto, not {text!r}")
    return int(text)


def parse_args(argv: list[str]) -> argparse.Namespace:
    max_runs_default = default_max_runs()  # a bad HARNESS_MAX_RUNS stops here, with a clear message
    parser = argparse.ArgumentParser(description="Run one test iteration.")
    parser.add_argument("--fake", choices=OUTCOMES, help="use fake phases with this outcome (no game)")
    parser.add_argument("--scenario", help=f"run the real game with this scenario. Known: {sorted(list_scenarios())}")
    parser.add_argument("--list-scenarios", action="store_true", help="print the scenarios and their time limits, then exit")
    parser.add_argument("--include-test-scenarios", action="store_true", help="with --list-scenarios: also list the hidden selftest scenarios")
    parser.add_argument("--fixture", default=DEFAULT_FIXTURE,
                        help="save fixture to start from (harness/fixtures/fixtures.json, default %(default)s). A stored fixture "
                             "is installed into the user's save folder under a free slot name and removed at the end (spec 06, part D)")
    parser.add_argument("--save", type=Path,
                        help="start from this save file (<slot>.sav, with its <slot>_descr.sav next to it) instead of a fixture. "
                             "It is installed like a stored fixture and removed at the end")
    parser.add_argument("--new-game", action="store_true",
                        help="start a NEW game with no save (spec 06, part E). No fixture is installed. Not with --save")
    parser.add_argument("--map", default=None, metavar="NAME",
                        help=f"with --new-game: the map to start on (default {DEFAULT_NEW_GAME_MAP})")
    parser.add_argument("--pak", action="append", default=[], metavar="NAME",
                        help="install the built harness pak NAME (from the pakmod work folder) before the game starts and "
                             "remove it at the end, also after a crash. Repeatable (spec 10, A/B variants)")
    parser.add_argument("--pak-config", type=Path, default=DEFAULT_PAK_CONFIG,
                        help="pakmod config that names the work folder of the paks (default %(default)s)")
    parser.add_argument("--env", action="append", default=[], metavar="KEY=VALUE",
                        help="extra environment variable for the game process. Name: ^[A-Z][A-Z0-9_]{0,63}$, not starting with "
                             "HARNESS_RUN_DIR, LOCALAPPDATA, PATH or UE4SS_BRIDGE. Value: printable, no newline. Repeatable")
    parser.add_argument("--slot", default="0", type=parse_slot, metavar="N|auto",
                        help="game slot (spec 11): 0 is the game folder, 1 to 3 are the folders of harness/install.ps1, "
                             "auto takes the first free installed slot (default %(default)s)")
    parser.add_argument("--keep-open", action="store_true", help="do not stop the game at the end")
    parser.add_argument("--telemetry-interval", type=float, default=DEFAULT_TELEMETRY_INTERVAL_S,
                        help="seconds between telemetry samples in the game (0 = off, default %(default)s)")
    parser.add_argument("--run-id", help="use this run id instead of a generated one")
    parser.add_argument("--runs-root", type=Path, default=REPO_ROOT / "runs")
    parser.add_argument("--max-runs", type=int, default=max_runs_default,
                        help="cap on runs in this runs folder (default %(default)s: 400, or the environment variable HARNESS_MAX_RUNS)")
    return parser.parse_args(argv)


def fail_before_run(message: str) -> int:
    # No run folder exists yet, so there is no summary.json to write.
    print(f"harness_error: {message}", file=sys.stderr)
    return EXIT_CODES["harness_error"]


def check_new_game_options(args: argparse.Namespace) -> None:
    """Check --new-game and --map. Store the map name (or None) on args.new_game_map."""
    if args.map is not None and not args.new_game:
        raise ValueError("--map needs --new-game")
    args.new_game_map = None
    if not args.new_game:
        return
    if args.fake or args.save is not None or args.fixture != DEFAULT_FIXTURE:
        raise ValueError("--new-game needs --scenario and cannot be used with --save or --fixture")
    args.new_game_map = args.map or DEFAULT_NEW_GAME_MAP
    if not MAP_NAME.fullmatch(args.new_game_map):
        raise ValueError(f"bad map name {args.new_game_map!r}: use letters, digits and '_' only")


def check_variant_options(args: argparse.Namespace) -> None:
    """Check --pak and --env before any lock or folder exists. Store the parsed env on args."""
    args.extra_env = parse_env_options(args.env)
    args.pak_names = [paks.check_name(name) for name in args.pak]
    if len(set(args.pak_names)) != len(args.pak_names):
        raise paks.PakError("a --pak name is given twice")
    if args.save is not None and (args.fake or not args.save.is_file()):
        raise ValueError(f"--save needs --scenario and an existing file: {args.save}")
    check_new_game_options(args)
    if args.fake and (args.pak_names or args.extra_env):
        raise ValueError("--pak and --env need --scenario. A fake run has no game.")


def build_phases(args: argparse.Namespace, slot: gameslots.GameSlot | None = None) -> list[Phase]:
    if args.fake:
        return build_fake_phases(args.fake)
    work_dir = paks.work_dir_from_config(args.pak_config) if args.pak_names else None
    return build_real_phases(args.scenario, keep_open=args.keep_open,
                             telemetry_interval_s=args.telemetry_interval, fixture=args.fixture,
                             pak_names=args.pak_names, pak_work_dir=work_dir, extra_env=args.extra_env, save_path=args.save,
                             new_game_map=args.new_game_map, slot=slot)


def take_slot_lock(args: argparse.Namespace) -> tuple[RunLock, gameslots.GameSlot | None]:
    """Take the run lock of the asked slot, or of the first free installed slot. A fake run has no game, so no slot."""
    if args.fake:
        lock = RunLock(args.runs_root, 0)
        lock.acquire()
        return lock, None
    candidates = gameslots.installed_slots()
    if args.slot is not None:
        candidates = [gameslots.get_slot(args.slot)]
    busy = []
    for slot in candidates:
        lock = RunLock(args.runs_root, slot.number)
        try:
            lock.acquire()
        except RunLockedError as error:
            busy.append(error)
            continue
        return lock, slot
    if len(busy) == 1:
        raise busy[0]
    holders = ", ".join(str(error.holder_pid) for error in busy)
    raise gameslots.SlotError(f"all {len(busy)} installed game slots are busy (lock holders: {holders}). Wait for a run to end.")


def build_config(args: argparse.Namespace, run, phases: list[Phase], lock) -> dict:
    return {
        "run_id": run.run_id,
        "scenario": f"fake-{args.fake}" if args.fake else args.scenario,
        "fake_outcome": args.fake,
        "test_save": None,  # chosen in preflight: an installed slot or the fixture's source slot
        "save_file": str(args.save) if args.save else None,
        "fixture": None if args.fake or args.new_game_map else args.fixture,
        "new_game_map": args.new_game_map,
        "private_appdata": not args.fake,
        "keep_open": args.keep_open,
        "slot": lock.slot if not args.fake else None,
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
        build_phases(args)  # a wrong scenario name fails here, before any lock or folder
        if args.slot is not None and not args.fake:
            gameslots.get_slot(args.slot)  # an uninstalled slot fails here too
    except (ValueError, FixtureError, EnvOptionError, paks.PakError, gameslots.SlotError) as error:
        return fail_before_run(str(error))
    try:
        lock, slot = take_slot_lock(args)
    except (RunLockedError, gameslots.SlotError) as error:
        return fail_before_run(str(error))
    try:
        with lock:
            phases = build_phases(args, slot)
            bump_iterations(args.runs_root, args.max_runs)
            run = create_run_folder(args.runs_root, args.run_id)
            config = build_config(args, run, phases, lock)
            write_config(run, config)
            summary = execute_run(run, config, phases)
    except (IterationLimitError, LockTimeoutError, FileExistsError) as error:
        return fail_before_run(str(error))
    print(f"{summary.run_id} {summary.verdict} reason={summary.reason or '-'} summary={run.summary_path}")
    return EXIT_CODES[summary.verdict]


def print_scenarios(include_hidden: bool) -> int:
    for name, info in list_scenarios(include_hidden).items():
        print(f"{name:<20} limit {info.limit_s:>5.0f} s  {info.summary}")
    return 0


def main(argv: list[str]) -> int:
    try:
        args = parse_args(argv)
    except ValueError as error:
        return fail_before_run(str(error))
    if args.list_scenarios:
        return print_scenarios(args.include_test_scenarios)
    if (args.fake is None) == (args.scenario is None):
        return fail_before_run("exactly one of --fake <outcome> and --scenario <name> is required.")
    return run_one(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
