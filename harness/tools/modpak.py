"""Build the data part of a mod from row patches (spec 22, plan step 5).

This module holds the pure logic: read patches, check them, apply them to table JSON, copy assets.
The tools (extract, UAssetGUI, repak) are passed in as functions, so tests run without the game.
Patch format: docs/harness/22-mod-pack-layout/README.md, section "Row patches".
"""

from __future__ import annotations

import copy
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

# Patch table name -> game asset path (no extension). Only tables with numeric row ids are supported.
TABLES = {
    "buildingStats": "ManorLords/Content/NotStronghold/Data/buildingStats",
    "DT_Upgrades": "ManorLords/Content/NotStronghold/Data/DT_Upgrades",
}
OPS = ("add", "set")
PATCH_KEYS = {"table", "row", "op", "from", "set"}


class ModPakError(Exception):
    exit_code = 1


@dataclass(frozen=True)
class Patch:
    file: str  # path shown in messages, relative to the mod folder
    feature: str
    table: str
    row: str
    op: str
    source: str | None
    fields: dict


# ---- read and validate ----

def read_manifest(mod_dir: Path) -> dict:
    path = mod_dir / "mod.json"
    if not path.is_file():
        raise ModPakError(f"mod.json not found: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ModPakError(f"{path}: not valid JSON: {error}") from error


def feature_list(manifest: dict) -> list[dict]:
    features = manifest.get("features")
    if not isinstance(features, list) or not features:
        raise ModPakError("mod.json has no 'features' list")
    return features


def check_patch_format(data: object, file: str) -> None:
    if not isinstance(data, dict):
        raise ModPakError(f"{file}: a patch must be a JSON object")
    unknown = sorted(set(data) - PATCH_KEYS)
    if unknown:
        raise ModPakError(f"{file}: unknown keys {unknown}. Allowed: {sorted(PATCH_KEYS)}")
    if data.get("table") not in TABLES:
        raise ModPakError(f"{file}: 'table' must be one of {sorted(TABLES)}, got {data.get('table')!r}")
    row = data.get("row")
    if not isinstance(row, str) or not row.isdigit():
        raise ModPakError(f"{file}: 'row' must be a string of digits, got {row!r}")
    if data.get("op") not in OPS:
        raise ModPakError(f"{file}: 'op' must be one of {list(OPS)}, got {data.get('op')!r}")
    fields = data.get("set", {})
    if not isinstance(fields, dict):
        raise ModPakError(f"{file}: 'set' must be an object of field values")
    if data["op"] == "set" and not fields:
        raise ModPakError(f"{file}: op 'set' needs a non-empty 'set'")
    if data["op"] == "set" and "from" in data:
        raise ModPakError(f"{file}: 'from' is only allowed with op 'add'")
    if data["op"] == "add" and not (isinstance(data.get("from"), str) and data["from"].isdigit()):
        raise ModPakError(f"{file}: op 'add' needs 'from', the row to clone (a string of digits)")


def read_patch(path: Path, mod_dir: Path, feature: str) -> Patch:
    shown = path.relative_to(mod_dir).as_posix()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ModPakError(f"{shown}: not valid JSON: {error}") from error
    check_patch_format(data, shown)
    return Patch(shown, feature, data["table"], data["row"], data["op"], data.get("from"), data.get("set", {}))


def load_patches(mod_dir: Path, manifest: dict) -> list[Patch]:
    """All patches in apply order: feature order of mod.json, then file name."""
    patches = []
    for feature in feature_list(manifest):
        folder = mod_dir / "data" / feature["name"] / "patches"
        for path in sorted(folder.glob("*.json")) if folder.is_dir() else []:
            patches.append(read_patch(path, mod_dir, feature["name"]))
    return patches


# ---- checks ----

def check_conflicts(patches: list[Patch]) -> None:
    added: dict[tuple, Patch] = {}
    fields: dict[tuple, Patch] = {}
    for patch in patches:
        key = (patch.table, patch.row)
        if patch.op == "add":
            if key in added:
                raise ModPakError(f"conflict: row {patch.table}/{patch.row} is added by {added[key].file} and by {patch.file}")
            added[key] = patch
        for field in patch.fields:
            first = fields.get(key + (field,))
            if first and first.feature != patch.feature:
                raise ModPakError(f"conflict: field {field} of {patch.table}/{patch.row} is set by {first.file} and by {patch.file}")
            fields.setdefault(key + (field,), patch)


def check_id_ranges(patches: list[Patch], manifest: dict) -> None:
    ranges = {f["name"]: f.get("ids", {}) for f in feature_list(manifest)}
    for patch in patches:
        if patch.op != "add":
            continue
        span = ranges[patch.feature].get(patch.table)
        if not span:
            raise ModPakError(f"{patch.file}: feature {patch.feature} has no 'ids' range for table {patch.table} in mod.json")
        low, high = span
        if not low <= int(patch.row) <= high:
            raise ModPakError(f"{patch.file}: new row {patch.row} is outside the range [{low}, {high}] of feature {patch.feature} for {patch.table}")


# ---- apply ----

def table_rows(data: dict) -> list:
    return data["Exports"][0]["Table"]["Data"]


def find_row(rows: list, name: str, patch: Patch, what: str) -> dict:
    hits = [row for row in rows if row["Name"] == name]
    if len(hits) != 1:
        raise ModPakError(f"{patch.file}: expected one {what} {patch.table}/{name}, found {len(hits)}")
    return hits[0]


def set_field(row: dict, field: str, value: object, patch: Patch) -> None:
    hits = [prop for prop in row["Value"] if prop["Name"] == field]
    if len(hits) != 1:
        raise ModPakError(f"{patch.file}: row {patch.table}/{row['Name']} has no single field {field!r}")
    prop = hits[0]
    if isinstance(value, list):
        if not prop["Value"]:
            raise ModPakError(f"{patch.file}: array field {field} is empty, no element to copy")
        template = prop["Value"][0]
        prop["Value"] = []
        for index, item in enumerate(value):
            element = copy.deepcopy(template)
            element["Name"] = str(index)
            element["Value"] = item
            prop["Value"].append(element)
    else:
        prop["Value"] = value
    if "IsZero" in prop:
        prop["IsZero"] = False


def apply_patch(data: dict, patch: Patch) -> None:
    rows = table_rows(data)
    if patch.op == "add":
        if any(row["Name"] == patch.row for row in rows):
            raise ModPakError(f"{patch.file}: row {patch.table}/{patch.row} already exists in the game table")
        row = copy.deepcopy(find_row(rows, patch.source, patch, "source row"))
        row["Name"] = patch.row
        rows.append(row)
        # UAssetGUI wrote no file when a new row name was missing in the name map (spike #65).
        if patch.row not in data["NameMap"]:
            data["NameMap"].append(patch.row)
    else:
        row = find_row(rows, patch.row, patch, "row")
    for field, value in patch.fields.items():
        set_field(row, field, value, patch)


def apply_patches(tables: dict[str, dict], patches: list[Patch]) -> None:
    for patch in patches:
        apply_patch(tables[patch.table], patch)


# ---- assets and the build ----

def copy_assets(mod_dir: Path, manifest: dict, target: Path) -> list[str]:
    """Copy data/<feature>/assets/** into the pak folder. Two features may not write the same file."""
    owners: dict[str, str] = {}
    for feature in feature_list(manifest):
        base = mod_dir / "data" / feature["name"] / "assets"
        for source in sorted(base.rglob("*")) if base.is_dir() else []:
            if source.is_symlink():
                raise ModPakError(f"symlinks are not allowed: {source}")
            if not source.is_file():
                continue
            relative = source.relative_to(base).as_posix()
            if relative in owners:
                raise ModPakError(f"conflict: asset {relative} is in features {owners[relative]} and {feature['name']}")
            owners[relative] = feature["name"]
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
    return sorted(owners)


def build_mod(
    mod_dir: Path,
    pak_folder: Path,
    fetch_table_json: Callable[[str], Path],
    pack_table_json: Callable[[Path], None],
    build_pak: Callable[[], Path],
) -> Path:
    """Apply the patches, write the tables, copy the assets, build the pak and copy it to mod/<Name>/paks/.

    fetch_table_json(asset path) returns the JSON file of the original table from the current game.
    pack_table_json(json file) writes the edited asset into pak_folder.
    """
    manifest = read_manifest(mod_dir)
    patches = load_patches(mod_dir, manifest)
    check_conflicts(patches)
    check_id_ranges(patches, manifest)
    used = sorted({patch.table for patch in patches})
    tables, paths = {}, {}
    for table in used:
        paths[table] = fetch_table_json(TABLES[table])
        tables[table] = json.loads(paths[table].read_text(encoding="utf-8"))
    apply_patches(tables, patches)
    for table in used:
        paths[table].write_text(json.dumps(tables[table], indent=2), encoding="utf-8")
        pack_table_json(paths[table])
    copy_assets(mod_dir, manifest, pak_folder)
    built = build_pak()
    target = mod_dir / "paks" / built.name
    target.parent.mkdir(exist_ok=True)
    shutil.copyfile(built, target)
    return target
