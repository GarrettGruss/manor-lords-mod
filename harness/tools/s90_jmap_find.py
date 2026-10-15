"""Find objects in the UE4SS jmap by name regex (issue #90). Reads the file only.

Usage: uv run python harness/tools/s90_jmap_find.py <jmap> <path-regex> [--raw]
Prints path, type and class of each match. With --raw, prints the JSON of the
object without its large lists (the keys that hold functions or properties).
"""
import json
import re
import sys


def main() -> None:
    if len(sys.argv) < 3:
        sys.exit("usage: s90_jmap_find.py <jmap> <path-regex> [--raw]")
    jmap_path, pattern = sys.argv[1], re.compile(sys.argv[2])
    show_raw = "--raw" in sys.argv
    with open(jmap_path, encoding="utf-8") as handle:
        objects = json.load(handle)["objects"]
    for path, obj in objects.items():
        if not pattern.search(path):
            continue
        print(f"{obj.get('type')}\t{obj.get('class')}\t{path}")
        if "--props" in sys.argv:
            for prop in obj.get("properties", []) or []:
                detail = prop.get("struct") or (prop.get("inner") or {}).get("struct") or ""
                print("    ", prop["name"], prop["type"], detail)
        if show_raw:
            print(json.dumps(obj, indent=1)[:6000])


if __name__ == "__main__":
    main()
