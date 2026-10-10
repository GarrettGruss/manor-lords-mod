"""Install and remove harness paks in the game's ~mods folder, with a manifest (specs 09 and 10).

Shared by `harness/tools/pakmod.py` (command line) and `harness/run.py --pak` (a run installs a pak in preflight
and removes it in teardown). The manifest `~mods/.harness-paks.json` lists the files this code wrote.
The code never replaces or deletes a file that the manifest does not list.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from pathlib import Path

NAME_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,40}$")
PAK_SUFFIX = "_P.pak"
MANIFEST_NAME = ".harness-paks.json"
EXIT_ERROR = 1


class PakError(Exception):
    """A clear, expected failure. The message says what to do."""

    exit_code = EXIT_ERROR


# ---- names and paths ----

def check_name(name: str) -> str:
    if not isinstance(name, str) or not NAME_PATTERN.fullmatch(name):
        raise PakError(f"bad name {name!r}: use 1 to 40 characters from A-Z a-z 0-9 _ -")
    return name


def pak_file_name(name: str) -> str:
    return check_name(name) + PAK_SUFFIX


def is_inside(child: Path, parent: Path) -> bool:
    try:
        Path(child).resolve().relative_to(Path(parent).resolve())
    except ValueError:
        return False
    return True


def require_inside(child: Path, parent: Path, what: str) -> Path:
    if not is_inside(child, parent):
        raise PakError(f"{what} is outside {parent}: {child}")
    return child


def paks_dir_of(game_dir: Path) -> Path:
    return Path(game_dir) / "ManorLords" / "Content" / "Paks"


def mods_dir_of(game_dir: Path) -> Path:
    return paks_dir_of(game_dir) / "~mods"


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def built_pak_path(work_dir: Path, name: str) -> Path:
    """Where `pakmod.py build <name>` leaves the pak."""
    return Path(work_dir) / "out" / pak_file_name(name)


def work_dir_from_config(config_path: Path) -> Path:
    """The work folder named in pakmod.local.json. This reads one key only. It does not check the tools."""
    try:
        raw = json.loads(Path(config_path).read_text(encoding="utf-8"))
        return Path(raw["work_dir"])
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise PakError(f"cannot read work_dir from {config_path}: {error}. Copy harness/pakmod.local.example.json and fill it in.") from error


# ---- manifest ----

def read_manifest(mods_dir: Path) -> dict:
    path = mods_dir / MANIFEST_NAME
    if not path.is_file():
        return {"version": 1, "created_dir": False, "files": {}}
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
        files = manifest["files"]
    except (OSError, ValueError, KeyError) as error:
        raise PakError(f"manifest is broken, fix or delete it by hand: {path} ({error})") from error
    if not isinstance(files, dict):
        raise PakError(f"manifest 'files' must be an object: {path}")
    manifest.setdefault("created_dir", False)
    return manifest


def write_manifest(mods_dir: Path, manifest: dict) -> None:
    path = mods_dir / MANIFEST_NAME
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    temp.replace(path)


# ---- install and remove ----

def install_pak(source: Path, game_dir: Path, pak_name: str, dry_run: bool = False) -> Path:
    """Copy a built pak into ~mods and record its hash. Refuse to replace a file that is not in the manifest."""
    mods_dir = mods_dir_of(game_dir)
    target = mods_dir / pak_name
    manifest = read_manifest(mods_dir)
    if target.exists() and pak_name not in manifest["files"]:
        raise PakError(f"refusing to overwrite {target}: it is not in the harness manifest")
    print(f"{'[dry-run] ' if dry_run else ''}install {pak_name} -> {target}")
    if dry_run:
        return target
    created = not mods_dir.exists()
    mods_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    if sha256_of(target) != sha256_of(source):
        raise PakError(f"copy check failed for {target}")
    manifest["files"][pak_name] = sha256_of(target)
    manifest["created_dir"] = bool(manifest["created_dir"] or created)
    write_manifest(mods_dir, manifest)
    return target


def remove_one(mods_dir: Path, manifest: dict, pak_name: str, dry_run: bool) -> bool:
    """Delete one manifest-listed pak if its hash still matches. Return True if the manifest entry can go."""
    target = mods_dir / pak_name
    if Path(pak_name).name != pak_name or not pak_name.endswith(".pak"):
        raise PakError(f"manifest entry is not a plain pak file name: {pak_name!r}")
    require_inside(target, mods_dir, "pak")
    if not target.exists():
        print(f"missing (already gone): {pak_name}")
        return True
    if sha256_of(target) != manifest["files"][pak_name]:
        print(f"SKIPPED {pak_name}: the file changed since install, delete it by hand if you want")
        return False
    print(f"{'[dry-run] ' if dry_run else ''}deleted {pak_name}")
    if not dry_run:
        target.unlink()
    return True


def remove(game_dir: Path, names: list[str] | None, dry_run: bool = False) -> int:
    """Remove the named paks, or all manifest paks if `names` is None. Return the number of skipped files."""
    mods_dir = mods_dir_of(game_dir)
    manifest = read_manifest(mods_dir)
    wanted = list(manifest["files"]) if names is None else [pak_file_name(n) for n in names]
    unknown = [pak for pak in wanted if pak not in manifest["files"]]
    if unknown:
        raise PakError(f"not in the harness manifest, not touched: {', '.join(unknown)}")
    skipped = 0
    for pak_name in wanted:
        if remove_one(mods_dir, manifest, pak_name, dry_run):
            manifest["files"].pop(pak_name)
        else:
            skipped += 1
    if not dry_run:
        finish_remove(mods_dir, manifest)
    return skipped


def remove_listed(game_dir: Path, names: list[str]) -> int:
    """Remove those of `names` that the manifest lists. A name that is not listed is ignored.

    Teardown uses this, so a failed install (for example a manifest conflict) never deletes a foreign file.
    """
    listed = read_manifest(mods_dir_of(game_dir))["files"]
    wanted = [name for name in names if pak_file_name(name) in listed]
    return remove(game_dir, wanted) if wanted else 0


def finish_remove(mods_dir: Path, manifest: dict) -> None:
    manifest_path = mods_dir / MANIFEST_NAME
    if manifest["files"]:
        write_manifest(mods_dir, manifest)
        return
    manifest_path.unlink(missing_ok=True)
    if manifest["created_dir"] and mods_dir.is_dir() and not any(mods_dir.iterdir()):
        mods_dir.rmdir()
        print("removed empty ~mods folder")


def list_paks(game_dir: Path) -> list[str]:
    mods_dir = mods_dir_of(game_dir)
    manifest = read_manifest(mods_dir)
    lines = []
    for pak_name, expected in sorted(manifest["files"].items()):
        target = mods_dir / pak_name
        state = "missing" if not target.exists() else ("ok" if sha256_of(target) == expected else "CHANGED")
        lines.append(f"{pak_name}  {state}  {expected}")
    return lines
