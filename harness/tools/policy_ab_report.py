"""Print the food stock and approval per game day for the runs of the policy A/B probe (issue #60).

Usage: uv run python harness/tools/policy_ab_report.py runs/<off-run> runs/<on-run> [...]
"""

import json
import sys
from pathlib import Path

FOOD_GOODS = ("171", "172", "230")


def day_rows(run_dir: Path) -> list[dict]:
    rows = []
    for line in (run_dir / "probe.jsonl").read_text(encoding="utf-8").splitlines():
        entry = json.loads(line)
        result = entry.get("result")
        if entry["step"].startswith("day ") and isinstance(result, dict):
            goods = result["stock"]["by_good"]
            rows.append({"day": entry["step"], "approval": result["approval"], "signed": result["signed"],
                         "food": sum(goods.get(g, 0) for g in FOOD_GOODS), "supplies_food": result["supplies_food"],
                         "factors": sorted({f["name"] for f in result["factors"] if not f["past"]}),
                         "population": result["people"]["population"]})
    return rows


def main(paths: list[str]) -> None:
    if not paths:
        raise SystemExit("give at least one run folder")
    for path in paths:
        print(path)
        for row in day_rows(Path(path)):
            print("  ", row)


if __name__ == "__main__":
    main(sys.argv[1:])
