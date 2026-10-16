"""The mod manifest (mod/<Name>/mod.json) and its check (spec 19)."""

from __future__ import annotations

import json
import re
from pathlib import Path

SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(-[0-9A-Za-z.-]+)?$")
NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
PAK_NAME = re.compile(r"^[A-Za-z0-9_-]+$")
PAK_SOURCES = ("build", "file")
REQUIRED_KEYS = {"name", "version", "description", "shared", "tested", "gate_scenarios"}
OPTIONAL_KEYS = {"pak", "display_name", "features"}
KEYS = REQUIRED_KEYS | OPTIONAL_KEYS
FEATURE_KEYS = {"name", "requires", "ids"}
TESTED_KEYS = {"game", "game_build", "ue4ss"}
PAK_KEYS = {"name", "source", "path"}


class ManifestError(Exception):
    """The manifest is not valid. The message lists every problem."""


def _check_text(manifest: dict, key: str, problems: list[str]) -> None:
    value = manifest.get(key)
    if not isinstance(value, str) or not value.strip():
        problems.append(f"{key} must be a non-empty string")


def _check_name_list(manifest: dict, key: str, problems: list[str], *, allow_empty: bool) -> None:
    value = manifest.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        problems.append(f"{key} must be a list of names")
    elif not value and not allow_empty:
        problems.append(f"{key} must not be empty")
    elif len(set(value)) != len(value):
        problems.append(f"{key} has a duplicate")


def _check_ids(feature: str, ids: object, problems: list[str]) -> None:
    if not isinstance(ids, dict):
        problems.append(f"features[{feature}].ids must be an object of table name -> [first, last]")
        return
    for table, span in ids.items():
        valid = (isinstance(span, list) and len(span) == 2 and all(isinstance(n, int) and not isinstance(n, bool) and n >= 0 for n in span)
                 and span[0] <= span[1])
        if not valid:
            problems.append(f"features[{feature}].ids.{table} must be [first, last] with 0 <= first <= last")


def _check_feature(feature: object, index: int, problems: list[str]) -> str | None:
    """Check one entry of features. Return its name when it has a valid one."""
    if not isinstance(feature, dict):
        problems.append(f"features[{index}] must be an object with name, requires and ids")
        return None
    label = str(feature.get("name", index))
    for key in sorted(feature.keys() - FEATURE_KEYS):
        problems.append(f"features[{label}].{key} is not a known field")
    name = feature.get("name")
    if not isinstance(name, str) or not NAME.match(name):
        problems.append(f"features[{index}].name must be a word (letters, digits, _)")
        name = None
    requires = feature.get("requires", [])
    if not isinstance(requires, list) or not all(isinstance(item, str) and item for item in requires):
        problems.append(f"features[{label}].requires must be a list of feature names")
    if "ids" in feature:
        _check_ids(label, feature["ids"], problems)
    return name


def _check_features(manifest: dict, problems: list[str]) -> None:
    features = manifest.get("features")
    if not isinstance(features, list):
        problems.append("features must be a list of {name, requires, ids}")
        return
    names = [_check_feature(feature, index, problems) for index, feature in enumerate(features)]
    known = {name for name in names if name}
    if len(known) != len([name for name in names if name]):
        problems.append("features has a duplicate name")
    for feature in features:
        if isinstance(feature, dict) and isinstance(feature.get("requires"), list):
            problems += [f"features[{feature.get('name')}] requires {item!r}, which is not a feature" for item in feature["requires"]
                         if isinstance(item, str) and item not in known]


def _check_tested(manifest: dict, problems: list[str]) -> None:
    tested = manifest.get("tested")
    if not isinstance(tested, dict):
        problems.append("tested must be an object with game, game_build and ue4ss")
        return
    for key in sorted(TESTED_KEYS - tested.keys()):
        problems.append(f"tested.{key} is missing")
    for key in sorted(tested.keys() - TESTED_KEYS):
        problems.append(f"tested.{key} is not a known field")
    for key in TESTED_KEYS & tested.keys():
        if not isinstance(tested[key], str) or not tested[key].strip():
            problems.append(f"tested.{key} must be a non-empty string")


def _check_pak(manifest: dict, problems: list[str]) -> None:
    pak = manifest.get("pak")
    if pak is None:
        return
    if not isinstance(pak, dict):
        problems.append("pak must be null or an object with name, source and path")
        return
    for key in sorted(pak.keys() - PAK_KEYS):
        problems.append(f"pak.{key} is not a known field")
    if not isinstance(pak.get("name"), str) or not PAK_NAME.match(pak.get("name") or ""):
        problems.append("pak.name must use letters, digits, - and _ only (the file is <name>_P.pak)")
    if pak.get("source") not in PAK_SOURCES:
        problems.append(f"pak.source must be one of {', '.join(PAK_SOURCES)}")
    if pak.get("path") is not None and not (isinstance(pak["path"], str) and pak["path"]):
        problems.append("pak.path must be a path inside the repo")
    if pak.get("source") == "build" and pak.get("path") is not None:
        problems.append("pak.path must not be set when pak.source is build (the file comes from pakmod.py build)")


def check_manifest(manifest: object, folder_name: str) -> list[str]:
    """Return the list of problems. An empty list means the manifest is valid."""
    if not isinstance(manifest, dict):
        return ["the manifest must be a JSON object"]
    problems = [f"{key} is not a known field" for key in sorted(manifest.keys() - KEYS)]
    problems += [f"{key} is missing" for key in sorted(REQUIRED_KEYS - manifest.keys())]
    if "name" in manifest:
        if not isinstance(manifest["name"], str) or not NAME.match(manifest["name"]):
            problems.append("name must be a word (letters, digits, _)")
        elif manifest["name"] != folder_name:
            problems.append(f"name {manifest['name']!r} must equal the folder name {folder_name!r}")
    if "version" in manifest and not (isinstance(manifest["version"], str) and SEMVER.match(manifest["version"])):
        problems.append("version must be semver, for example 0.1.0")
    if "description" in manifest:
        _check_text(manifest, "description", problems)
    if "shared" in manifest:
        _check_name_list(manifest, "shared", problems, allow_empty=True)
    if "gate_scenarios" in manifest:
        # A mod with features may have no gate scenario yet (the features add them). A mod without features needs one.
        _check_name_list(manifest, "gate_scenarios", problems, allow_empty="features" in manifest)
    if "display_name" in manifest:
        _check_text(manifest, "display_name", problems)
    if "features" in manifest:
        _check_features(manifest, problems)
    if "tested" in manifest:
        _check_tested(manifest, problems)
    _check_pak(manifest, problems)
    return problems


def load_manifest(mod_dir: Path) -> dict:
    """Read and check mod_dir/mod.json. Raise ManifestError with a clear message."""
    path = mod_dir / "mod.json"
    if not path.is_file():
        raise ManifestError(f"{path} does not exist. Add a manifest to make the mod releasable.")
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ManifestError(f"{path} is not valid JSON: {error}") from error
    problems = check_manifest(manifest, mod_dir.name)
    if problems:
        raise ManifestError(f"{path} is not valid:\n  - " + "\n  - ".join(problems))
    return manifest
