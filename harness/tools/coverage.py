"""Coverage of the Invasion Mode criteria (spec 10, upgrade U8).

Reads criteria.json and the scenario files (with ast, never imported) and prints how many
automatable criteria have a verified test method. Stdlib only.

Exit codes: 0 ok, 1 a check failed (--min-verified or --check-spec), 2 bad input.
"""

import argparse
import ast
import json
import re
import sys
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent.parent
SPEC_DIR = REPO_DIR / "docs" / "harness" / "10-invasion-testability"
DEFAULT_CRITERIA = SPEC_DIR / "criteria.json"
DEFAULT_SPEC = SPEC_DIR / "README.md"
DEFAULT_SCENARIOS = REPO_DIR / "harness" / "scenarios"
DEFAULT_RUNS_ROOT = REPO_DIR / "runs"

MARKS = ("A", "P", "H")
TARGET = 0.9
FIELDS = ("id", "title", "pillar", "mark", "method", "blocked_by", "spikes", "upgrades",
          "method_verified", "verified_by", "reason_human")

# A table row of the spec: | T1 | title | A (note) | method |
SPEC_ROW = re.compile(r"^\|\s*([A-Z]\d+)\s*\|\s*(.*?)\s*\|\s*([APH])\b[^|]*\|\s*(.*?)\s*\|\s*$")


class InputError(Exception):
    """Bad input file. The command line turns it into exit code 2."""


# ---------- criteria ----------

def load_criteria(path: Path) -> list[dict]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise InputError(f"Cannot read criteria file {path}: {error}") from error
    if not isinstance(data, list):
        raise InputError(f"{path}: the top level must be a list of criteria.")
    problems = validate_criteria(data)
    if problems:
        raise InputError(f"{path} is not valid:\n  " + "\n  ".join(problems))
    return data


def validate_criteria(criteria: list) -> list[str]:
    problems: list[str] = []
    seen: set = set()
    for index, item in enumerate(criteria):
        if not isinstance(item, dict):
            problems.append(f"entry {index} is not an object")
            continue
        name = item.get("id", f"entry {index}")
        missing = [field for field in FIELDS if field not in item]
        if missing:
            problems.append(f"{name}: missing fields {missing}")
            continue
        if item["id"] in seen:
            problems.append(f"{name}: duplicate id")
        seen.add(item["id"])
        if item["mark"] not in MARKS:
            problems.append(f"{name}: mark must be one of {MARKS}, not {item['mark']!r}")
        if item["mark"] == "H" and not item["reason_human"]:
            problems.append(f"{name}: a human (H) criterion needs reason_human")
        if item["mark"] in ("A", "P") and not item["method"]:
            problems.append(f"{name}: an A or P criterion needs a method")
    return problems


# ---------- scenarios ----------

def read_scenario_metadata(path: Path) -> dict:
    """Return {"name": str, "covers": list} from a scenario file. The file is parsed, not run."""
    try:
        tree = ast.parse(Path(path).read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError, ValueError) as error:
        raise InputError(f"Cannot parse scenario {path} (it is read with ast, never run): {error}") from error
    name = _module_constant(tree, "NAME", str, path)
    covers = _module_constant(tree, "COVERS", list, path)
    return {"name": name if name else Path(path).stem, "covers": covers or []}


def _module_constant(tree: ast.Module, wanted: str, kind: type, path: Path):
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == wanted for t in node.targets):
            try:
                value = ast.literal_eval(node.value)
            except ValueError as error:
                raise InputError(f"{path}: {wanted} must be a plain literal: {error}") from error
            if not isinstance(value, kind) or (kind is list and not all(isinstance(v, str) for v in value)):
                raise InputError(f"{path}: {wanted} must be a {kind.__name__}" + (" of strings" if kind is list else ""))
            return value
    return None


def read_scenarios(scenarios_dir: Path) -> list[dict]:
    scenarios = []
    for path in sorted(Path(scenarios_dir).glob("*.py")):
        info = read_scenario_metadata(path)
        info["file"] = path.name
        scenarios.append(info)
    return scenarios


# ---------- run results ----------

def last_passing_runs(runs_root: Path) -> dict:
    """Map scenario name to the id of its newest run with verdict pass. Newer failing runs do not count."""
    best: dict = {}
    for summary_path in Path(runs_root).glob("*/summary.json"):
        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue  # one broken run folder must not hide the others
        if not isinstance(summary, dict) or summary.get("verdict") != "pass" or not summary.get("scenario"):
            continue
        stamp = str(summary.get("started") or summary_path.parent.name)
        run_id = str(summary.get("run_id") or summary_path.parent.name)
        name = summary["scenario"]
        if name not in best or stamp > best[name][0]:
            best[name] = (stamp, run_id)
    return {name: run_id for name, (_, run_id) in best.items()}


# ---------- computation ----------

def compute(criteria: list[dict], scenarios: list[dict], passing: dict) -> dict:
    known = {item["id"] for item in criteria}
    unknown = sorted({(s["file"], cid) for s in scenarios for cid in s["covers"] if cid not in known})
    proven_by_run = {cid for s in scenarios if s["name"] in passing for cid in s["covers"] if cid in known}
    covered_by_scenario = {cid for s in scenarios for cid in s["covers"] if cid in known}

    automatable = [c for c in criteria if c["mark"] in ("A", "P")]
    verified = [c for c in automatable if c["method_verified"] or c["id"] in proven_by_run]
    verified_ids = {c["id"] for c in verified}
    blocked = [c for c in automatable if c["blocked_by"]]
    human = [c for c in criteria if c["mark"] == "H"]
    gaps = [c for c in automatable if c["id"] not in verified_ids and c["id"] not in covered_by_scenario]
    return {
        "total": len(criteria),
        "by_mark": {mark: sum(1 for c in criteria if c["mark"] == mark) for mark in MARKS},
        "automatable": len(automatable),
        "automatable_share": _share(len(automatable), len(criteria)),
        "verified": len(verified),
        "verified_share": _share(len(verified), len(automatable)),
        "verified_ids": sorted(verified_ids),
        "blocked": [{"id": c["id"], "blocked_by": c["blocked_by"]} for c in blocked],
        "human": [{"id": c["id"], "reason_human": c["reason_human"]} for c in human],
        "unknown_covers": [{"scenario": f, "id": cid} for f, cid in unknown],
        "gaps": [c["id"] for c in gaps],
        "scenarios": [{"name": s["name"], "covers": s["covers"], "last_passing_run": passing.get(s["name"])}
                      for s in scenarios],
        "target": TARGET,
    }


def _share(part: int, whole: int) -> float:
    return part / whole if whole else 0.0


# ---------- spec check ----------

def read_spec_table(spec_path: Path) -> dict:
    """Map criterion id to {"title", "mark"} from the tables of the spec README."""
    try:
        lines = Path(spec_path).read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise InputError(f"Cannot read spec {spec_path}: {error}") from error
    rows = {}
    for line in lines:
        match = SPEC_ROW.match(line)
        if match:
            rows[match.group(1)] = {"title": match.group(2), "mark": match.group(3)}
    return rows


def check_spec(criteria: list[dict], spec_rows: dict) -> list[str]:
    """Return differences between criteria.json and the spec tables. Empty means they agree."""
    differences = []
    by_id = {c["id"]: c for c in criteria}
    for cid, item in by_id.items():
        row = spec_rows.get(cid)
        if row is None:
            differences.append(f"{cid}: in criteria.json but not in the spec")
            continue
        if row["mark"] != item["mark"]:
            differences.append(f"{cid}: mark is {item['mark']} in criteria.json but {row['mark']} in the spec")
        if row["title"] != item["title"]:
            differences.append(f"{cid}: title differs from the spec")
    for cid in spec_rows:
        if cid not in by_id:
            differences.append(f"{cid}: in the spec but not in criteria.json")
    return differences


# ---------- output ----------

def format_report(result: dict) -> str:
    marks = result["by_mark"]
    lines = [
        f"criteria total: {result['total']}  (A {marks['A']}, P {marks['P']}, H {marks['H']})",
        f"automatable share (A+P) / total = {result['automatable_share']:.0%}",
        f"A and P criteria with a verified method: {result['verified']} of {result['automatable']}",
        f"verified share of A and P criteria = {result['verified_share']:.0%} (target {result['target']:.0%})",
        f"blocked criteria count against the target: {len(result['blocked'])}",
    ]
    lines += [f"  {item['id']}: {item['blocked_by']}" for item in result["blocked"]]
    lines.append(f"human criteria with a reason: {len(result['human'])}")
    lines += [f"  {item['id']}: {item['reason_human']}" for item in result["human"]]
    lines.append(f"scenarios read: {len(result['scenarios'])}")
    for item in result["scenarios"]:
        if item["covers"]:
            lines.append(f"  {item['name']}: covers {', '.join(item['covers'])}; "
                         f"last passing run: {item['last_passing_run'] or 'none'}")
    for item in result["unknown_covers"]:
        lines.append(f"ERROR unknown id {item['id']} in COVERS of {item['scenario']}")
    lines.append(f"gap list (no scenario, not verified): {len(result['gaps'])}")
    if result["gaps"]:
        lines.append("  " + " ".join(result["gaps"]))
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Coverage of the Invasion Mode criteria.")
    parser.add_argument("--criteria", type=Path, default=DEFAULT_CRITERIA)
    parser.add_argument("--scenarios", type=Path, default=DEFAULT_SCENARIOS, help="folder with scenario files")
    parser.add_argument("--runs-root", type=Path, default=DEFAULT_RUNS_ROOT)
    parser.add_argument("--spec", type=Path, default=DEFAULT_SPEC, help="spec README for --check-spec")
    parser.add_argument("--json", action="store_true", help="print machine readable output")
    parser.add_argument("--min-verified", type=float, default=None, help="exit 1 if the verified share is lower")
    parser.add_argument("--check-spec", action="store_true", help="compare criteria.json with the spec tables")
    return parser


def run(args) -> int:
    criteria = load_criteria(args.criteria)
    if args.check_spec:
        differences = check_spec(criteria, read_spec_table(args.spec))
        print("\n".join(differences) if differences else "criteria.json and the spec tables agree")
        return 1 if differences else 0
    result = compute(criteria, read_scenarios(args.scenarios), last_passing_runs(args.runs_root))
    print(json.dumps(result, indent=2) if args.json else format_report(result))
    if result["unknown_covers"]:
        return 2
    if args.min_verified is not None and result["verified_share"] < args.min_verified:
        print(f"verified share {result['verified_share']:.0%} is below the minimum {args.min_verified:.0%}",
              file=sys.stderr)
        return 1
    return 0


def main(argv=None) -> int:
    try:
        return run(build_parser().parse_args(argv))
    except InputError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
