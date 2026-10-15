"""Print a flat trace of the Kismet bytecode of one function in a UAssetGUI JSON (issue #90).

Usage: uv run python harness/tools/s90_bytecode_trace.py <json> <function-name>
Each line is one token type with the names it uses (functions, properties,
literals). Reads the file only.
"""
import json
import sys


def resolve(asset: dict, index: int) -> str:
    if index < 0:
        return asset["Imports"][-index - 1]["ObjectName"]
    if index > 0:
        return asset["Exports"][index - 1]["ObjectName"]
    return "null"


def property_path(node: dict) -> str | None:
    pointer = node.get("Variable") or node.get("AssignmentExpression") or node.get("Property")
    if isinstance(pointer, dict):
        path = pointer.get("New", {}).get("Path") or pointer.get("Path")
        if path:
            return ".".join(path)
    return None


def trace(asset: dict, node, depth: int, out: list[str]) -> None:
    if isinstance(node, list):
        for item in node:
            trace(asset, item, depth, out)
        return
    if not isinstance(node, dict):
        return
    kind = node.get("$type", "").split(".")[-1].split(",")[0]
    if kind.startswith("EX_"):
        detail = []
        for key in ("VirtualFunctionName", "FunctionName"):
            if key in node:
                detail.append(str(node[key]))
        if "StackNode" in node and isinstance(node["StackNode"], int):
            detail.append(resolve(asset, node["StackNode"]))
        path = property_path(node)
        if path:
            detail.append(path)
        if "Value" in node and not isinstance(node["Value"], (dict, list)):
            detail.append(repr(node["Value"]))
        out.append("  " * depth + kind[3:] + " " + " ".join(detail))
    for key, value in node.items():
        if isinstance(value, (dict, list)):
            trace(asset, value, depth + 1, out)


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit("usage: s90_bytecode_trace.py <json> <function-name>")
    with open(sys.argv[1], encoding="utf-8") as handle:
        asset = json.load(handle)
    for export in asset["Exports"]:
        if export["ObjectName"] == sys.argv[2] and export.get("ScriptBytecode"):
            lines: list[str] = []
            trace(asset, export["ScriptBytecode"], 0, lines)
            print("\n".join(lines))
            return
    sys.exit(f"function not found: {sys.argv[2]}")


if __name__ == "__main__":
    main()
