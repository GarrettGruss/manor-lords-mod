"""Hold the game speed on a `--keep-open` run and report which hooks fired (issue 104 spike helper). Research tool, not a test.

    uv run python harness/tools/s104_ai_watch.py <run id> <seconds>

It sets the speed every 5 seconds, then prints the hook events and the AI construction log. It calls no save function.
"""

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SPEED_CALL = {"op": "call", "ref": "first:MyPawnCPP_BP3_C", "function": "changeGameSpeed", "args": [3, False]}


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    os.environ["UE4SS_BRIDGE_DATA_DIR"] = str(ROOT / "runs" / argv[0] / "bridge")
    sys.path.insert(0, str(ROOT / "mcp"))
    from ue4ss_bridge import server  # noqa: E402 - needs the environment variable first

    deadline = time.time() + float(argv[1])
    while time.time() < deadline:
        server.batch([SPEED_CALL])
        time.sleep(5)
    streams = server.batch([{"op": "streams"}])[0]["result"]
    counts = {row["label"]: row["events"] for row in streams if row["events"] > 0}
    print("event counts:", json.dumps(counts))
    # One query per label: a noisy hook must not hide the others.
    queries = [{"op": "events", "since": 0, "limit": 5, "label": label} for label in counts]
    queries.append({"op": "get", "ref": "first:RTSMultiEngineCPP", "name": "debugLog_AI_construction"})
    print(json.dumps(server.batch(queries), indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
