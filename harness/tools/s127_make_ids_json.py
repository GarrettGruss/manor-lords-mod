"""Spec 23: write the edited JSON for the `ids` pak (buildingStats, DT_Upgrades, building names).

Usage: uv run python harness/tools/s127_make_ids_json.py <work json folder> <output folder>
The input folder is `<work_dir>/json`. The output folder has the same layout and holds only the three
edited tables. The caller copies them into `<work_dir>/json`, runs `pakmod.py fromjson`, and puts the old files back.
"""
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import s65_edit_json as edit

STATS = "ManorLords/Content/NotStronghold/Data/buildingStats.json"
UPGRADES = "ManorLords/Content/NotStronghold/Data/DT_Upgrades.json"
NAMES = "ManorLords/Content/Translation/HoodedHorse/DT_Translation_BuildingNames.json"
SOURCE_ROW = "30"
NEW_IDS = ["126", "486", "1000", "2000", "32767", "65536"]
# New upgrade row -> (building that offers it, building it upgrades into).
NEW_UPGRADES = {"117": ("486", "126"), "118": ("2000", "1000")}


def set_int_array(row, field, values):
    prop = [p for p in row["Value"] if p["Name"] == field][0]
    template = prop["Value"][0]
    prop["Value"] = []
    for index, number in enumerate(values):
        item = copy.deepcopy(template)
        item["Name"] = str(index)
        item["Value"] = number
        prop["Value"].append(item)


def set_int_field(row, field, number):
    prop = [p for p in row["Value"] if p["Name"] == field][0]
    prop["IsZero"] = False
    prop["Value"] = number


def edit_stats(path):
    for new_id in NEW_IDS:
        edit.clone_stats_row(path, SOURCE_ROW, new_id)
        edit.make_row_visible(path, new_id)
    data = edit.load(path)
    rows = data["Exports"][0]["Table"]["Data"]
    for upgrade, (offered_by, _) in NEW_UPGRADES.items():
        set_int_array(edit.find_row(rows, offered_by), "upgrades", [int(upgrade)])
    edit.save(path, data)


def edit_upgrades(path):
    for upgrade, (_, target) in NEW_UPGRADES.items():
        edit.clone_stats_row(path, "2", upgrade)
        data = edit.load(path)
        set_int_field(edit.find_row(data["Exports"][0]["Table"]["Data"], upgrade), "upgradesInto", int(target))
        edit.save(path, data)


def edit_names(path):
    for new_id in NEW_IDS:
        key = f"buildingID_{new_id}"
        edit.clone_stats_row(path, "buildingID_97", key)
        data = edit.load(path)
        row = edit.find_row(data["Exports"][0]["Table"]["Data"], key)
        for prop in row["Value"]:
            prop["Value"] = f"Test {new_id}"
        edit.save(path, data)


def main():
    source, output = Path(sys.argv[1]), Path(sys.argv[2])
    for relative, editor in ((STATS, edit_stats), (UPGRADES, edit_upgrades), (NAMES, edit_names)):
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        text = (source / relative).read_text(encoding="utf-8")
        target.write_text(text, encoding="utf-8")
        editor(target)


if __name__ == "__main__":
    main()
