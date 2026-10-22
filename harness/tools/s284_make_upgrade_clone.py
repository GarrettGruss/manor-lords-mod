"""Spike #284 task 1.2 control: add DT_Upgrades row 119 (clone of vanilla row 14, upgradesInto 126) and offer it from building row 486.

Usage: uv run python harness/tools/s284_make_upgrade_clone.py <buildingStats.json> <DT_Upgrades.json>
Both files are already edited by s127_make_ids_json.py (rows 126 and 486 exist). Edits them in place.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import s127_make_ids_json as ids
import s65_edit_json as edit

NEW_UPGRADE, SOURCE_UPGRADE, OFFERED_BY, TARGET = "119", "14", "486", 126


def main() -> None:
    stats, upgrades = Path(sys.argv[1]), Path(sys.argv[2])
    edit.clone_stats_row(upgrades, SOURCE_UPGRADE, NEW_UPGRADE)
    data = edit.load(upgrades)
    ids.set_int_field(edit.find_row(data["Exports"][0]["Table"]["Data"], NEW_UPGRADE), "upgradesInto", TARGET)
    edit.save(upgrades, data)
    data = edit.load(stats)
    ids.set_int_array(edit.find_row(data["Exports"][0]["Table"]["Data"], OFFERED_BY), "upgrades", [int(NEW_UPGRADE)])
    edit.save(stats, data)


if __name__ == "__main__":
    main()
