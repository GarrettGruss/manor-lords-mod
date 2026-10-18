"""Spec 31: clone the tailor extension row (DT_Upgrades 106) into a new extension row, for a pak.

Usage: uv run python harness/tools/s31_make_extension_json.py <DT_Upgrades.json> <new row> <descr> <regional wealth> <plank cost>
The new row key is 100 + the extension number. If the row key is the source row (106), the row is edited in place
instead of cloned (a reskin of the tailor extension). The file is edited in place (it is a git-ignored work file).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import s65_edit_json as edit

SOURCE_ROW = "106"  # tailor, the closest vanilla artisan extension
PLANKS = 17


def set_field(row, name, value):
    prop = [p for p in row["Value"] if p["Name"] == name][0]
    prop["IsZero"] = False
    prop["Value"] = value


def set_plank_cost(row, amount):
    cost = [p for p in row["Value"] if p["Name"] == "cost"][0]
    entry = cost["Value"][0]
    for field in entry["Value"]:
        if field["Name"] == "Type":
            if field["Value"] != PLANKS:
                raise SystemExit(f"error: cost 0 of row {SOURCE_ROW} is item {field['Value']}, not planks")
        if field["Name"] == "amt":
            field["Value"] = amount


def main():
    if len(sys.argv) != 6:
        raise SystemExit(__doc__)
    path, new_row, descr, wealth, planks = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
    if new_row != SOURCE_ROW:
        edit.clone_stats_row(path, SOURCE_ROW, new_row)
    data = edit.load(path)
    row = edit.find_row(data["Exports"][0]["Table"]["Data"], new_row)
    set_field(row, "Name", f"extension{int(new_row) - 100}")
    set_field(row, "descr", descr)
    set_field(row, "regionalWealth", wealth)
    set_field(row, "minimumHouseLv", 0)
    set_plank_cost(row, planks)
    edit.save(path, data)
    print(f"row {new_row} written: {descr}, wealth {wealth}, planks {planks}")


main()
