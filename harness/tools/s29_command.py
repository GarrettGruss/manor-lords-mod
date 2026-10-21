"""Spike helper (spec 29): send named commands to a `--keep-open` run and print the answers.

    uv run python harness/tools/s29_command.py <run id> '<json list of {"command": ..., fields}>'

Why: the MCP bridge points to another folder than a private run, and a named command is a file in runs/<id>/commands.
The helper picks the next free command number. It stops at the first refused command.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "harness"))
from runlib.commands import CommandChannel, CommandError  # noqa: E402


def next_number(folder: Path) -> int:
    numbers = [int(path.name[:4]) for path in folder.glob("[0-9][0-9][0-9][0-9].json")]
    return max(numbers, default=0)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    run_dir = ROOT / "runs" / argv[0]
    if not run_dir.is_dir():
        raise SystemExit(f"run folder not found: {run_dir}")
    # The channel makes the commands folder on the first send: a run with no command yet has none (#312).
    folder = run_dir / "commands"
    channel = CommandChannel(folder, timeout_s=30.0)
    channel._number = next_number(folder)
    for item in json.loads(argv[1]):
        fields = dict(item)
        try:
            answer = channel.send(fields.pop("command"), **fields)
        except CommandError as error:
            print(json.dumps({"error": str(error)}))
            return 1
        print(json.dumps(answer))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
