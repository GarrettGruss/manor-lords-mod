"""Print compact rows of any exported data table (spec 18, issue #104).

Usage: s104_table.py <table file name without .json> <row name>...   (no row name: list all names)
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

DATA_DIR = Path("C:/Users/garre/development/manor-lords-mod/modtools/work/json/ManorLords/Content")


def find_table(name):
    matches = list(DATA_DIR.rglob(name + ".json"))
    if not matches:
        raise SystemExit(f"table not found: {name}")
    return matches[0]


def main():
    import s104_rows_lib as lib
    path = find_table(sys.argv[1])
    with open(path, encoding="utf8") as handle:
        rows = json.load(handle)["Exports"][0]["Table"]["Data"]
    wanted = sys.argv[2:]
    for raw_row in rows:
        name = str(raw_row["Name"])
        if wanted[:1] == ["--grep"]:
            if wanted[1].lower() in json.dumps(raw_row).lower():
                print("MATCH", name, json.dumps({i["Name"]: lib.short(lib.value_of(i)) for i in raw_row["Value"]})[:600])
        elif not wanted:
            print(name)
        elif name in wanted:
            print("ROW", name, json.dumps({i["Name"]: lib.short(lib.value_of(i)) for i in raw_row["Value"]}))


main()
