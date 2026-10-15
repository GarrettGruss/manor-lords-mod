"""Spec 21 spike A helper: print the world location of every master of the given types.

    uv run python harness/tools/s21_locate.py <run id> <type> [<type> ...]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import s94_drive  # noqa: E402


def main():
    bridge = s94_drive.make_bridge(sys.argv[1])
    wanted = {int(arg) for arg in sys.argv[2:]}
    for path in s94_drive.master_paths(bridge):
        state = s94_drive.master_state(bridge, path)
        if state["type"] in wanted:
            where = bridge.call_function(path, "K2_GetActorLocation")
            print(state["type"], path.rsplit(".", 1)[-1], round(where["X"]), round(where["Y"]), round(where["Z"]))


if __name__ == "__main__":
    main()
