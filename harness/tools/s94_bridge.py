"""Send a batch of bridge ops to a `--keep-open` run from a JSON file and print the answers (issue 94 spike helper).

    uv run python harness/tools/s94_bridge.py <run id> <ops.json>

The file holds a JSON list of bridge ops, for example [{"op": "world"}]. The MCP bridge tools point to another folder than a
private run, so this tool sets UE4SS_BRIDGE_DATA_DIR to runs/<run id>/bridge. Ops are listed in mcp/ue4ss_bridge/server.py.
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    run_id, ops_file = argv
    bridge_dir = ROOT / "runs" / run_id / "bridge"
    if not bridge_dir.is_dir():
        raise SystemExit(f"bridge folder not found: {bridge_dir}")
    os.environ["UE4SS_BRIDGE_DATA_DIR"] = str(bridge_dir)
    sys.path.insert(0, str(ROOT / "mcp"))
    from ue4ss_bridge import server  # noqa: E402 - needs the environment variable first

    ops = json.loads(Path(ops_file).read_text(encoding="utf-8"))
    answers = server.batch(ops)
    print(json.dumps(answers, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
