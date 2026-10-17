"""Run a regression suite and write runs/suite-<id>/report.json and report.md (spec 08).

  suite.py --suite core [--slots N|all] [--max-minutes N] [--runs-root DIR] [--list]
  suite.py --update-baseline <scenario> [--from-last N]

Exit code: 0 pass, 1 fail or strict drift, 2 unresolved crash or timeout,
3 budget or iteration cap ended the suite early, 4 harness error.
"""

from __future__ import annotations

import argparse
import functools
import json
import os
import sys
from pathlib import Path

from runlib import gameslots
from runlib.runfolder import new_run_id
from runlib.scenario import is_exclusive
from suitelib import baselines, history, report as report_module
from suitelib.launcher import SubprocessLauncher, LAUNCHER_ENV, close_game, close_slot_game, resolve_command
from suitelib.pool import run_suite_parallel
from suitelib.runner import run_suite
from suitelib.suitefile import SUITES_DIR, SuiteFileError, load_suite

REPO_ROOT = Path(__file__).resolve().parent.parent
EXIT_HARNESS_ERROR = 4
DEFAULT_FROM_LAST = 5


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a regression suite.")
    parser.add_argument("--suite", help="suite name: harness/suites/<name>.json")
    parser.add_argument("--list", action="store_true", help="list the suites and stop")
    parser.add_argument("--max-minutes", type=float, help="lower the time budget of the suite")
    parser.add_argument("--runs-root", type=Path, default=REPO_ROOT / "runs")
    parser.add_argument("--update-baseline", metavar="SCENARIO", help="write a proposed baseline file for human review")
    parser.add_argument("--from-last", type=int, default=DEFAULT_FROM_LAST, help="use the last N passing runs")
    parser.add_argument("--baselines-dir", type=Path, default=baselines.BASELINES_DIR)
    parser.add_argument("--suites-dir", type=Path, default=SUITES_DIR)
    parser.add_argument("--launcher-command", help="replace run.py (default: env HARNESS_SUITE_LAUNCHER, else run.py)")
    parser.add_argument("--slots", default="1",
                        help="game slots to run on at once: a number or 'all' (the installed slots, harness/install.ps1). Default 1")
    parser.add_argument("--run-timeout-s", type=float, default=None,
                        help="fixed time limit of one run. Default: the scenario LIMIT_S plus 600 s, at least 900 s")
    return parser.parse_args(argv)


def fail(message: str) -> int:
    print(f"harness_error: {message}", file=sys.stderr)
    return EXIT_HARNESS_ERROR


def list_suites(suites_dir: Path) -> int:
    for path in sorted(Path(suites_dir).glob("*.json")):
        suite = load_suite(path.stem, suites_dir)
        scenarios = ", ".join(
            f"{e.scenario}x{e.repeat}{'?' if e.optional else ''}" + (f" [{'/'.join(v.name for v in e.variants)}]" if e.variants else "")
            for e in suite.entries)
        print(f"{suite.name}: {scenarios} (budget {suite.time_budget_s:.0f} s, retries {suite.flake_retries})")
    return 0


def passing_summaries(runs_root: Path, scenario: str, count: int) -> list[dict]:
    """The newest `count` passing summaries of a scenario."""
    found = []
    for path in Path(runs_root).glob("*/summary.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue  # a broken old summary must not block a baseline
        if data.get("scenario") == scenario and data.get("verdict") == "pass":
            found.append(data)
    found.sort(key=lambda data: data.get("started", ""), reverse=True)
    return found[:count]


def update_baseline(args: argparse.Namespace) -> int:
    summaries = passing_summaries(args.runs_root, args.update_baseline, args.from_last)
    if not summaries:
        return fail(f"no passing run of {args.update_baseline!r} in {args.runs_root}. Run the scenario first.")
    proposal = baselines.propose_baseline(summaries, scenario=args.update_baseline)
    path = baselines.write_baseline(args.update_baseline, proposal, args.baselines_dir)
    print(f"wrote {path} from {len(summaries)} passing run(s). Review it before you commit it.")
    print(json.dumps(proposal["metrics"], indent=2))
    return 0


def slot_numbers(text: str, using_run_py: bool) -> list[int]:
    """The game slots of a parallel suite. A custom launcher (tests) gets the numbers 0 to N-1 without a check."""
    installed = [slot.number for slot in gameslots.installed_slots()] if using_run_py else None
    if text == "all":
        if installed is None:
            raise ValueError("--slots all needs the real run.py. Give a number with a custom launcher.")
        return installed
    if not text.isdigit() or int(text) < 1:
        raise ValueError(f"--slots must be a number of 1 or more, or 'all', not {text!r}.")
    count = int(text)
    if installed is not None and count > len(installed):
        raise ValueError(f"--slots {count}: only {len(installed)} game slot(s) are installed ({installed}). Run harness/install.ps1 -Slots {count - 1}.")
    return installed[:count] if installed is not None else list(range(count))


def run_with_slots(args: argparse.Namespace, suite, suite_id: str, max_seconds: float | None):
    # A custom launcher (tests) may not start a game, so only the real run.py gets the game cleanup.
    using_run_py = not (args.launcher_command or os.environ.get(LAUNCHER_ENV, "").strip())
    command = resolve_command(args.launcher_command)
    slots = slot_numbers(args.slots, using_run_py)
    if len(slots) == 1 and args.slots != "all":
        launcher = SubprocessLauncher(args.runs_root, command, args.run_timeout_s, close_game if using_run_py else None)
        return run_suite(suite, launcher, suite_id, max_seconds)
    launchers = {
        slot: SubprocessLauncher(args.runs_root, command, args.run_timeout_s,
                                 functools.partial(close_slot_game, slot) if using_run_py else None, slot=slot)
        for slot in slots
    }
    print(f"suite {suite.name}: running on game slots {slots}")
    return run_suite_parallel(suite, launchers, suite_id, max_seconds, is_exclusive=is_exclusive)


def run_named_suite(args: argparse.Namespace) -> int:
    suite = load_suite(args.suite, args.suites_dir)
    suite_id = new_run_id()
    max_seconds = args.max_minutes * 60 if args.max_minutes else None
    outcome = run_with_slots(args, suite, suite_id, max_seconds)

    history_path = args.runs_root / "suite-history.jsonl"
    history.append_history(history_path, outcome)
    rows = history.read_history(history_path)
    flake_rates = {item.entry.scenario: history.flake_rate(rows, item.entry.scenario) for item in outcome.entries}
    findings = report_module.evaluate_baselines(outcome, args.baselines_dir)

    report = report_module.build_report(outcome, findings, flake_rates)
    json_path, markdown_path = report_module.write_report(report, args.runs_root / f"suite-{suite_id}")
    print(f"suite {suite.name} {report['verdict']} exit={report['exit_code']} report={json_path} table={markdown_path}")
    return report["exit_code"]


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        if args.list:
            return list_suites(args.suites_dir)
        if args.update_baseline:
            return update_baseline(args)
        if not args.suite:
            return fail("one of --suite, --list and --update-baseline is required.")
        return run_named_suite(args)
    except (SuiteFileError, baselines.BaselineError, gameslots.SlotError, ValueError) as error:
        return fail(str(error))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
