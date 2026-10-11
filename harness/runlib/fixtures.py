"""Save fixtures (spec 06, parts C and D).

A fixture is one saved game. Its manifest entry is in `harness/fixtures/fixtures.json` (hashes, description, tags; no save data in git).
Part D (2026-10-11): the files of a fixture are kept in `harness/fixtures/saves/<name>/` (git ignores that folder) under the stem
`slot`. A run installs them into the user's save folder under a free slot name (`runlib/saveslots.py`) and loads that slot.
The game lists and loads saves only from the user's REAL save folder; a copy in the run's private `LOCALAPPDATA` is never read
(docs/specs/06-dev-loop-and-fixtures/implementation-notes/fixture-load-bug.md). The private folder still holds the game's config,
logs and crash reports for the run.
An old entry with `source_slot` and no stored files is loaded from that slot of the user's folder by name, read only.

Safety rules, enforced here:
- The user's save folder is only read here. Its files must match the manifest before they are used.
- All files of the user's save folder are hashed before and after each operation. A difference raises `SaveFolderChanged`.
- The code deletes only a folder named `appdata` that holds `ManorLords/Saved`, and never the user's folder.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from .environment import sha256_of_file

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MANIFEST_PATH = REPO_ROOT / "harness" / "fixtures" / "fixtures.json"
STORE_DIR = REPO_ROOT / "harness" / "fixtures" / "saves"  # one folder per fixture; ignored by git
STORE_STEM = "slot"
DEFAULT_FIXTURE = "base"
APPDATA_NAME = "appdata"
FIXTURE_NAME = re.compile(r"^[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*$")
# The parts of a slot: the world, the descriptor, the thumbnail and the coat of arms images.
SLOT_SUFFIX = r"(?P<suffix>_descr\.sav|\.sav|\.png|_coat_\d+\.png)"
REQUIRED_SUFFIXES = (".sav", "_descr.sav")


class FixtureError(RuntimeError):
    """A fixture operation failed. The message says what to do."""


class SaveFolderChanged(FixtureError):
    """A file in the user's save folder changed during an operation."""


def check_name(fixture: str) -> str:
    if not FIXTURE_NAME.match(fixture):
        raise FixtureError(f"bad fixture name {fixture!r}: use letters, digits and '-' only")
    return fixture


# ---- the guard: hashes of every file in the user's save folder ----

def snapshot_user_files(save_dir: Path) -> dict[str, str]:
    """Name to SHA-256 for every entry. A folder entry gets the value 'dir'."""
    if not save_dir.is_dir():
        return {}
    return {p.name: sha256_of_file(p) if p.is_file() else "dir" for p in sorted(save_dir.iterdir())}


def describe_difference(before: dict[str, str], after: dict[str, str]) -> list[str]:
    problems = [f"changed: {name}" for name in before if name in after and before[name] != after[name]]
    problems += [f"deleted: {name}" for name in before if name not in after]
    problems += [f"new: {name}" for name in after if name not in before]
    return problems


def fingerprint(snapshot: dict[str, str]) -> str:
    return hashlib.sha256(json.dumps(snapshot, sort_keys=True).encode("utf-8")).hexdigest()


@contextmanager
def guarded(save_dir: Path):
    """Hash the user's save files before and after the block. Raise SaveFolderChanged if they differ.

    Yields a dict with the snapshot, the number of guarded files and a fingerprint, for the run record.
    """
    before = snapshot_user_files(save_dir)
    record = {"user_files": len(before), "user_files_sha256": fingerprint(before), "snapshot": before}
    yield record
    problems = describe_difference(before, snapshot_user_files(save_dir))
    if problems:
        raise SaveFolderChanged(f"ABORT: files in the user's save folder {save_dir} changed: {'; '.join(problems[:10])}")


# ---- manifest ----

def load_manifest(path: Path = MANIFEST_PATH) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise FixtureError(f"manifest not found: {path}") from error
    if not isinstance(data.get("fixtures"), dict):
        raise FixtureError(f"{path} has no 'fixtures' object")
    return data


def is_stored(entry: dict) -> bool:
    return bool(entry.get("stored"))


def get_entry(manifest: dict, fixture: str) -> dict:
    check_name(fixture)
    entry = manifest["fixtures"].get(fixture)
    if entry is None:
        raise FixtureError(f"unknown fixture {fixture!r}. Known: {sorted(manifest['fixtures'])}")
    return entry


def source_files(save_dir: Path, source_slot: str) -> dict[str, Path]:
    """The files of a slot, keyed by suffix: '.sav', '_descr.sav', '.png', '_coat_0.png', ..."""
    pattern = re.compile(rf"^{re.escape(source_slot)}{SLOT_SUFFIX}$")
    files = {}
    for path in sorted(save_dir.iterdir()) if save_dir.is_dir() else []:
        match = pattern.match(path.name)
        if match and path.is_file():
            files[match["suffix"]] = path
    return files


def source_hashes(save_dir: Path, source_slot: str) -> dict[str, str]:
    files = source_files(save_dir, source_slot)
    for needed in REQUIRED_SUFFIXES:
        if needed not in files:
            raise FixtureError(f"slot {source_slot!r} has no {source_slot}{needed} in {save_dir}")
    return {suffix: sha256_of_file(path) for suffix, path in files.items()}


def record_fixture(save_dir: Path, manifest_path: Path, fixture: str, source_slot: str,
                   description: str, tags: list[str]) -> dict:
    """Write or update a manifest entry from the current files of `source_slot`. Only reads the save folder."""
    check_name(fixture)
    with guarded(save_dir):
        sources = source_hashes(save_dir, source_slot)
    manifest = load_manifest(manifest_path) if manifest_path.exists() else {"fixtures": {}}
    manifest["fixtures"][fixture] = {
        "source_slot": source_slot, "description": description, "tags": tags, "sha256": sources,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest["fixtures"][fixture]


def files_of_save(path: Path) -> dict[str, Path]:
    """The files of the slot that `path` (a `<stem>.sav` file) belongs to, keyed by suffix."""
    if path.suffix != ".sav" or path.name.endswith("_descr.sav"):
        raise FixtureError(f"give the main save file (<slot>.sav), not {path.name}")
    stem = path.name[:-len(".sav")]
    files = source_files(path.parent, stem)
    for needed in REQUIRED_SUFFIXES:
        if needed not in files:
            raise FixtureError(f"{path.parent} has no {stem}{needed}")
    return files


def import_fixture(sources: dict[str, Path], manifest_path: Path, fixture: str, description: str, tags: list[str],
                   origin: str, store_root: Path | None = None) -> dict:
    """Copy the slot files `sources` into the store as `<store>/<fixture>/slot<suffix>` and write the manifest entry."""
    store_root = store_root or STORE_DIR  # looked up at call time, so tests can point it elsewhere
    check_name(fixture)
    for needed in REQUIRED_SUFFIXES:
        if needed not in sources:
            raise FixtureError(f"the save has no file for {needed}")
    target = store_root / fixture
    if target.exists():
        shutil.rmtree(target)  # the store belongs to the harness; a new import replaces the old files
    target.mkdir(parents=True)
    hashes = {}
    for suffix, path in sources.items():
        shutil.copy2(path, target / f"{STORE_STEM}{suffix}")
        hashes[suffix] = sha256_of_file(target / f"{STORE_STEM}{suffix}")
        if hashes[suffix] != sha256_of_file(path):
            raise FixtureError(f"the copy of {path.name} differs from its source")
    manifest = load_manifest(manifest_path) if manifest_path.exists() else {"fixtures": {}}
    manifest["fixtures"][fixture] = {"stored": True, "origin": origin, "description": description, "tags": tags,
                                     "sha256": hashes}
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest["fixtures"][fixture]


def fixture_files(entry: dict, fixture: str, user_saves: Path, store_root: Path | None = None) -> dict[str, Path]:
    """The files of a fixture (stored, or the old kind: the source slot in the user's folder), checked against the manifest."""
    store_root = store_root or STORE_DIR  # looked up at call time, so tests can point it elsewhere
    if is_stored(entry):
        files = source_files(store_root / fixture, STORE_STEM)
        fix = f"import the fixture again, or put its files back into {store_root / fixture}"
    else:
        files = source_files(user_saves, entry["source_slot"])
        fix = f"fixtures.py record {fixture} --source-slot {entry['source_slot']}"
    actual = {suffix: sha256_of_file(path) for suffix, path in files.items()}
    if actual != entry["sha256"]:
        raise FixtureError(f"the files of fixture {fixture!r} differ from the manifest. Check them, then {fix}")
    return files


def list_fixtures(manifest: dict) -> list[dict]:
    return [
        {"name": name, "stored": is_stored(entry), "source_slot": entry.get("source_slot"), "tags": entry.get("tags", []),
         "description": entry.get("description", "")}
        for name, entry in sorted(manifest["fixtures"].items())
    ]


# ---- the run's own appdata folder ----

@dataclass(frozen=True)
class AppdataResult:
    fixture: str
    stored: bool
    source_slot: str | None
    sources: dict
    sav_sha256: str
    user_files: int
    user_files_sha256: str
    user_snapshot: dict

    def as_dict(self) -> dict:
        """The record for config.json. The full snapshot and the paths stay out of it."""
        return {"fixture": self.fixture, "stored": self.stored, "source_slot": self.source_slot, "files": len(self.sources),
                "sav_sha256": self.sav_sha256, "user_files": self.user_files, "user_files_sha256": self.user_files_sha256}


def saved_dir_of(appdata_dir: Path) -> Path:
    return appdata_dir / "ManorLords" / "Saved"


def prepare_appdata(user_saved_dir: Path, appdata_dir: Path, manifest: dict, fixture: str,
                    store_root: Path | None = None) -> AppdataResult:
    """Check the fixture files and build the game's private `LOCALAPPDATA` (a copy of the user's Config folder).

    `user_saved_dir` is `%LOCALAPPDATA%/ManorLords/Saved`. It is only read. The fixture is not copied here: the game does not
    read saves from the private folder. The run installs it into the user's folder (`runlib/saveslots.py`).
    """
    store_root = store_root or STORE_DIR  # looked up at call time, so tests can point it elsewhere
    entry = get_entry(manifest, fixture)
    user_saves = user_saved_dir / "SaveGames"
    user_root = user_saved_dir.resolve()
    if appdata_dir.resolve() == user_root or user_root in appdata_dir.resolve().parents:
        raise FixtureError("the private appdata folder must not be inside the user's save folder")
    with guarded(user_saves) as record:
        sources = fixture_files(entry, fixture, user_saves, store_root)
        saved_dir_of(appdata_dir).joinpath("SaveGames").mkdir(parents=True, exist_ok=True)
        config = user_saved_dir / "Config"
        if config.is_dir():
            shutil.copytree(config, saved_dir_of(appdata_dir) / "Config", dirs_exist_ok=True)
    return AppdataResult(fixture, is_stored(entry), entry.get("source_slot"), sources, entry["sha256"][".sav"],
                         record["user_files"], record["user_files_sha256"], record["snapshot"])


def remove_appdata(appdata_dir: Path) -> int:
    """Delete a run's private appdata folder. Return the number of files. Refuses any other folder."""
    if appdata_dir.name != APPDATA_NAME:
        raise FixtureError(f"refused to delete {appdata_dir}: the folder is not named '{APPDATA_NAME}'")
    if not appdata_dir.exists():
        return 0
    if not saved_dir_of(appdata_dir).is_dir():
        raise FixtureError(f"refused to delete {appdata_dir}: it has no ManorLords/Saved folder")
    count = sum(1 for p in appdata_dir.rglob("*") if p.is_file())
    shutil.rmtree(appdata_dir)
    return count


def default_user_saved_dir() -> Path:
    return Path(os.environ["LOCALAPPDATA"]) / "ManorLords" / "Saved"
