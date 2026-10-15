"""Print the build-related fields of manor module rows from the extracted data tables (issue 90).

Usage: uv run python harness/tools/s90_row_goods.py <data folder> <row> [<row> ...]
The data folder holds buildingStats.json and the other extracted JSON tables.
"""
import json
import sys
from pathlib import Path

FIELDS = (
    "constructionGoods", "requiredTech", "constructionCost", "maxInRegion", "moduleCategory",
    "BlueprintPath", "assemblyBlueprintVariations", "constructionMeshAsset", "bVisibleInUi",
    "BuildingCategory", "buildingFunction",
)
OTHER_TABLES = ("DT_ConstructionBPs", "DT_BuildingMeshPathData", "DT_IndependentBuildingPartAssemblies")


def load_rows(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    return {str(row["Name"]): row for row in data["Exports"][0]["Table"]["Data"]}


def flatten(value):
    if isinstance(value, list):
        return [flatten(item) for item in value]
    if isinstance(value, dict):
        if "Name" in value and "Value" in value:
            return (value["Name"], flatten(value["Value"]))
        if "AssetPath" in value:
            return value["AssetPath"]["PackageName"]
        return {key: flatten(item) for key, item in value.items() if key != "$type"}
    return value


def main():
    folder = Path(sys.argv[1])
    names = sys.argv[2:]
    stats = load_rows(folder / "buildingStats.json")
    for name in names:
        if name not in stats:
            print(name, "missing in buildingStats")
            continue
        for prop in stats[name]["Value"]:
            if prop["Name"] in FIELDS:
                print(name, prop["Name"], json.dumps(flatten(prop["Value"]))[:500])
    for table in OTHER_TABLES:
        rows = load_rows(folder / (table + ".json"))
        print(table, "rows:", len(rows), "present:", [n for n in names if n in rows])
        for name in names:
            if name in rows:
                print("  ", name, json.dumps(flatten(rows[name]["Value"]))[:500])


if __name__ == "__main__":
    main()
