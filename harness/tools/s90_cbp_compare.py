"""Summarize a construction Blueprint JSON from UAssetGUI (issue #90).

Usage: uv run python harness/tools/s90_cbp_compare.py <json> [<json> ...]
Prints the class, parent class, the top-level default properties, the count of
components by class, and the tags and property names used on components.
"""
import collections
import json
import sys


def export_class(asset: dict, export: dict) -> str:
    index = export.get("ClassIndex", 0)
    if index < 0:
        return asset["Imports"][-index - 1]["ObjectName"]
    return f"export#{index}"


def summarize(path: str) -> None:
    with open(path, encoding="utf-8") as handle:
        asset = json.load(handle)
    exports = asset["Exports"]
    print("==", path.replace("\\", "/").split("/")[-1], "exports", len(exports))
    classes = collections.Counter(export_class(asset, e) for e in exports)
    print("classes:", dict(classes.most_common(12)))
    tags = collections.Counter()
    props = collections.Counter()
    for export in exports:
        for prop in export.get("Data", []):
            props[prop["Name"]] += 1
            if prop["Name"] == "ComponentTags":
                for tag in prop.get("Value", []):
                    tags[tag.get("Value")] += 1
    print("tags:", dict(tags.most_common(20)))
    print("property names:", dict(props.most_common(25)))
    for export in exports:
        if export["ObjectName"].startswith("Default__"):
            names = [p["Name"] for p in export.get("Data", [])]
            print("CDO", export["ObjectName"], "props:", names[:40])
        if export.get("$type", "").endswith("ClassExport, UAssetAPI"):
            print("ClassExport", export["ObjectName"], "super",
                  export.get("SuperIndex"), "funcs", len(export.get("FuncMap", [])))
    funcs = [e["ObjectName"] for e in exports if "Function" in e.get("$type", "")]
    print("functions:", funcs[:20])


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: s90_cbp_compare.py <json> [<json> ...]")
    for arg in sys.argv[1:]:
        summarize(arg)
