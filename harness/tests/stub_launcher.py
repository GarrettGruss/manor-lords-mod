"""A stand-in for harness/run.py. It writes fake runs/<id>/summary.json files.

HARNESS_STUB_PLAN is a JSON file: {"scenario": [step, ...]}. A step is an object with
"verdict", "duration_s", "asserts", or "mode": "no_summary" | "iteration_cap" | "unknown" | "hang".
The last step repeats. HARNESS_STUB_STATE (a JSON file) counts the calls per scenario.
HARNESS_STUB_BAD_SLOT: a --slot value that fails before a summary, like a game slot that is not installed.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

EXIT_FOR_VERDICT = {"pass": 0, "fail": 1, "crash": 2, "timeout": 3}


def state_lock(state_path):
    """Parallel suites start several stubs at once. They must not read the state file half written."""
    lock = state_path.with_suffix(".lock")
    deadline = time.monotonic() + 20
    while True:
        try:
            return os.open(lock, os.O_CREAT | os.O_EXCL), lock
        except FileExistsError:
            if time.monotonic() > deadline:
                raise
            time.sleep(0.01)


def next_step(scenario):
    state_path = Path(os.environ["HARNESS_STUB_STATE"])
    handle, lock = state_lock(state_path)
    try:
        return _next_step(scenario, state_path)
    finally:
        os.close(handle)
        os.remove(lock)


def _next_step(scenario, state_path):
    plan = json.loads(Path(os.environ["HARNESS_STUB_PLAN"]).read_text())
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    index = state.get(scenario, 0)
    state[scenario] = index + 1
    state_path.write_text(json.dumps(state))
    steps = plan.get(scenario, [{"verdict": "pass"}])
    return steps[min(index, len(steps) - 1)]


def write_summary(args, step):
    folder = Path(args.runs_root) / args.run_id
    folder.mkdir(parents=True)
    data = {
        "run_id": args.run_id,
        "verdict": step.get("verdict", "pass"),
        "reason": None,
        "scenario": args.scenario,
        "started": "2026-01-01T00:00:00Z",
        "duration_s": step.get("duration_s", 50.0),
        "phases": [],
        "scenario_result": {"asserts": step.get("asserts", [])},
        "stub_args": {"pak": args.pak, "env": args.env, **({"slot": args.slot} if args.slot is not None else {})},
    }
    (folder / "summary.json").write_text(json.dumps(data))
    if "metrics" in step:
        (folder / "metrics.json").write_text(json.dumps(step["metrics"]))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario")
    parser.add_argument("--run-id")
    parser.add_argument("--runs-root")
    parser.add_argument("--fixture")
    parser.add_argument("--pak", action="append", default=[])
    parser.add_argument("--env", action="append", default=[])
    parser.add_argument("--slot")
    args = parser.parse_args()
    if args.slot is not None and args.slot == os.environ.get("HARNESS_STUB_BAD_SLOT"):
        print(f"harness_error: game slot {args.slot} is not installed.", file=sys.stderr)
        return 4
    step = next_step(args.scenario)
    mode = step.get("mode")
    if mode == "unknown":
        print("harness_error: Unknown scenario 'x'.", file=sys.stderr)
        return 4
    if mode == "iteration_cap":
        print("harness_error: Iteration limit reached: 20 runs done.", file=sys.stderr)
        return 4
    if mode == "hang":
        time.sleep(60)
    if mode != "no_summary":
        write_summary(args, step)
    return EXIT_FOR_VERDICT.get(step.get("verdict", "pass"), 4)


if __name__ == "__main__":
    sys.exit(main())
