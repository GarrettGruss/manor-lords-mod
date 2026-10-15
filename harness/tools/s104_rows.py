"""Print compact buildingStats rows (spec 18, issue #104). Static read of the exported JSON.

Usage: s104_rows.py list | s104_rows.py find <text or row id>...
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import s104_rows_lib as lib  # noqa: E402


def main():
    with open(lib.JSON_PATH, encoding="utf8") as handle:
        rows = json.load(handle)["Exports"][0]["Table"]["Data"]
    mode = sys.argv[1]
    patterns = sys.argv[2:]
    for raw_row in rows:
        row = lib.row_of(raw_row)
        text = json.dumps(row).lower()
        if mode == "list":
            print(raw_row["Name"], row["DisplayName"], row["buildingFunction"], "stable", row["stableSpace"], "pasture", row["pastureSpace"],
                  "up", row["upgrades"], "from", row["upgradedFrom"], "ui", row["bVisibleInUi"], row["BlueprintPath"])
        elif any(p == str(raw_row["Name"]) or (not p.isdigit() and p.lower() in text) for p in patterns):
            print("ROW", raw_row["Name"], json.dumps(row))


main()
