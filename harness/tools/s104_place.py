"""Send mod commands to a `--keep-open` run and print the answers (issue 104 spike helper). Research tool, not a test.

    uv run python harness/tools/s104_place.py <run id> <step> [<step> ...]

A step is `Mod.command` or `Mod.command={"json":"args"}` or `sleep=<seconds>`.
Or give one file `steps.json` that holds a list of steps, for example [["HarnessPlace.arm", {"x": 1}], ["sleep", 2]].
Example: uv run python harness/tools/s104_place.py s104h-1 HarnessPlace.state sleep=2 HarnessPlace.state
It calls no save function.
"""

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "harness"))

from runlib.commands import ModCommandChannel  # noqa: E402


def parse_step(step):
    name, _, text = step.partition("=")
    return name, (json.loads(text) if text and name != "sleep" else text)


def load_steps(path):
    return [(step[0], step[1] if len(step) > 1 else {}) for step in json.loads(Path(path).read_text(encoding="utf-8"))]


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    channel = ModCommandChannel(ROOT / "runs" / argv[0] / "modcmd", timeout_s=20.0)
    steps = load_steps(argv[1]) if argv[1].endswith(".json") else [parse_step(step) for step in argv[1:]]
    for name, value in steps:
        if name == "sleep":
            time.sleep(float(value))
            continue
        mod = name.split(".", 1)[0]
        answer = channel.send(mod, name, value if isinstance(value, dict) else {})
        print(name, json.dumps(answer.get("result"), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
