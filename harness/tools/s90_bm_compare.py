"""List the components of manor module Blueprints from UAssetGUI JSON (issue #90).

Usage: uv run python harness/tools/s90_bm_compare.py <json> [<json> ...]
Prints component names (SCS nodes) and mesh references. Reads files only.
"""
import json
import re
import sys


def component_names(asset: dict) -> list[str]:
    names = [n for n in asset["NameMap"] if n.endswith("_GEN_VARIABLE")]
    return [n[: -len("_GEN_VARIABLE")] for n in names]


def mesh_refs(asset: dict) -> list[str]:
    return [n for n in asset["NameMap"] if n.startswith("/Game/")]


def summarize(path: str) -> None:
    with open(path, encoding="utf-8") as handle:
        asset = json.load(handle)
    exports = asset["Exports"]
    print(f"== {path.split('/')[-1].split(chr(92))[-1]}  exports={len(exports)}")
    comps = component_names(asset)
    prefixes: dict[str, int] = {}
    for name in comps:
        key = re.sub(r"[_0-9]+$", "", name) or name
        prefixes[key] = prefixes.get(key, 0) + 1
    print(f"components ({len(comps)}):", ", ".join(comps[:60]))
    print("prefix counts:", prefixes)
    print("asset refs:", [r for r in mesh_refs(asset)][:12])


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: s90_bm_compare.py <json> [<json> ...]")
    for arg in sys.argv[1:]:
        summarize(arg)
