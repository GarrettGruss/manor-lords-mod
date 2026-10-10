"""Build, install and remove asset mod paks (spec 09).

Commands: check, build <name>, install <name>, remove <name>|--all, list.
Every command accepts --dry-run and --game-dir.

The pak tool is NOT part of this repo. Its path comes from the local file `harness/pakmod.local.json`
(not committed). The tool reads no AES key and no game export; the user supplies the tool and the edited assets.

Safety:
- A name must match NAME_PATTERN. A path that leaves the work folder is refused. Symlinks are refused.
- The packer runs as a list (no shell) with a time limit.
- `install` writes only into <game>\\ManorLords\\Content\\Paks\\~mods and never replaces a file that is not in the manifest.
- `remove` deletes only files that the manifest lists, and only when their SHA-256 still matches.
- The tool never touches saves or other game folders.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_GAME_DIR = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Manor Lords")
DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "pakmod.local.json"
NAME_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,40}$")
PAK_SUFFIX = "_P.pak"
MANIFEST_NAME = ".harness-paks.json"
OUT_DIR_NAME = "out"
MOUNT_PREFIX = "../../../"
PACKER_TIMEOUT_S = 300
REQUIRED_PLACEHOLDERS = ("{response}", "{output}")
CONFIG_EXAMPLE = {
    "packer": "C:/tools/UnrealPak/UnrealPak.exe",
    "packer_args": ["-Create={response}", "{output}"],
    "work_dir": "C:/modwork",
}


class PakModError(Exception):
    """A clear, expected failure. The message says what to do."""


# ---- names and paths ----

def check_name(name: str) -> str:
    if not isinstance(name, str) or not NAME_PATTERN.fullmatch(name):
        raise PakModError(f"bad name {name!r}: use 1 to 40 characters from A-Z a-z 0-9 _ -")
    return name


def pak_file_name(name: str) -> str:
    return check_name(name) + PAK_SUFFIX


def is_inside(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def require_inside(child: Path, parent: Path, what: str) -> Path:
    if not is_inside(child, parent):
        raise PakModError(f"{what} is outside {parent}: {child}")
    return child


def mods_dir_of(game_dir: Path) -> Path:
    return Path(game_dir) / "ManorLords" / "Content" / "Paks" / "~mods"


# ---- config ----

def load_config(path: Path) -> dict:
    """Read and validate the local config. Raise PakModError with the first problem."""
    problems = config_problems(path)
    if problems:
        raise PakModError("; ".join(problems))
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return {"packer": Path(raw["packer"]), "packer_args": list(raw["packer_args"]), "work_dir": Path(raw["work_dir"])}


def config_problems(path: Path) -> list[str]:
    path = Path(path)
    if not path.is_file():
        return [f"config file missing: {path}. Example content: {json.dumps(CONFIG_EXAMPLE)}"]
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        return [f"config file is not valid JSON: {error}"]
    if not isinstance(raw, dict):
        return ["config must be a JSON object"]
    return packer_problems(raw) + args_problems(raw) + work_dir_problems(raw)


def packer_problems(raw: dict) -> list[str]:
    packer = raw.get("packer")
    if not isinstance(packer, str) or not packer:
        return ["config key 'packer' is missing (path to UnrealPak or similar)"]
    if not Path(packer).is_file():
        return [f"packer not found: {packer}"]
    return []


def args_problems(raw: dict) -> list[str]:
    args = raw.get("packer_args")
    if not isinstance(args, list) or not all(isinstance(item, str) for item in args):
        return ["config key 'packer_args' must be a list of strings"]
    joined = "\n".join(args)
    missing = [token for token in REQUIRED_PLACEHOLDERS if token not in joined]
    return [f"packer_args must contain {', '.join(missing)}"] if missing else []


def work_dir_problems(raw: dict) -> list[str]:
    work_dir = raw.get("work_dir")
    if not isinstance(work_dir, str) or not work_dir:
        return ["config key 'work_dir' is missing"]
    if not Path(work_dir).is_dir():
        return [f"work_dir is not a folder: {work_dir}"]
    return []


# ---- build ----

def asset_folder(config: dict, name: str) -> Path:
    folder = config["work_dir"] / check_name(name)
    require_inside(folder, config["work_dir"], "asset folder")
    if not folder.is_dir():
        raise PakModError(f"asset folder not found: {folder}. Put the edited asset files there.")
    return folder


def list_asset_files(folder: Path, work_dir: Path) -> list[Path]:
    """All files under the folder. Symlinks and paths that leave the work folder are refused."""
    files = []
    for path in sorted(folder.rglob("*")):
        if path.is_symlink():
            raise PakModError(f"symlinks are not allowed: {path}")
        require_inside(path, work_dir, "asset file")
        if path.is_file():
            files.append(path)
    if not files:
        raise PakModError(f"no files in {folder}")
    return files


def mount_path(folder: Path, file: Path) -> str:
    return MOUNT_PREFIX + file.relative_to(folder).as_posix()


def response_text(folder: Path, files: list[Path]) -> str:
    """One line per file: "<full path>" "<mount path in the pak>"."""
    lines = [f'"{file.resolve()}" "{mount_path(folder, file)}"' for file in files]
    return "\n".join(lines) + "\n"


def packer_command(config: dict, response: Path, output: Path) -> list[str]:
    args = [arg.replace("{response}", str(response)).replace("{output}", str(output)) for arg in config["packer_args"]]
    return [str(config["packer"])] + args


def run_packer(command: list[str], timeout_s: float) -> None:
    try:
        done = subprocess.run(command, capture_output=True, text=True, timeout=timeout_s, shell=False)
    except subprocess.TimeoutExpired as error:
        raise PakModError(f"packer did not finish in {timeout_s:.0f} s and was stopped") from error
    except OSError as error:
        raise PakModError(f"packer could not start: {error}") from error
    if done.returncode != 0:
        tail = (done.stdout + done.stderr).strip()[-500:]
        raise PakModError(f"packer failed with exit code {done.returncode}: {tail}")


def build(config: dict, name: str, dry_run: bool = False, timeout_s: float = PACKER_TIMEOUT_S) -> Path:
    work_dir = config["work_dir"]
    folder = asset_folder(config, name)
    files = list_asset_files(folder, work_dir)
    out_dir = work_dir / OUT_DIR_NAME
    output = out_dir / pak_file_name(name)
    response = out_dir / f"{name}.response.txt"
    command = packer_command(config, response, output)
    print(f"{'[dry-run] ' if dry_run else ''}build {name}: {len(files)} files -> {output}")
    print(f"  command: {command}")
    if dry_run:
        return output
    out_dir.mkdir(exist_ok=True)
    response.write_text(response_text(folder, files), encoding="utf-8")
    output.unlink(missing_ok=True)
    run_packer(command, timeout_s)
    if not output.is_file():
        raise PakModError(f"packer ended without an error but wrote no pak: {output}")
    print(f"built {output} ({output.stat().st_size} bytes)")
    return output


# ---- manifest, install, remove ----

def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def read_manifest(mods_dir: Path) -> dict:
    path = mods_dir / MANIFEST_NAME
    if not path.is_file():
        return {"version": 1, "created_dir": False, "files": {}}
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
        files = manifest["files"]
    except (OSError, ValueError, KeyError) as error:
        raise PakModError(f"manifest is broken, fix or delete it by hand: {path} ({error})") from error
    if not isinstance(files, dict):
        raise PakModError(f"manifest 'files' must be an object: {path}")
    manifest.setdefault("created_dir", False)
    return manifest


def write_manifest(mods_dir: Path, manifest: dict) -> None:
    path = mods_dir / MANIFEST_NAME
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    temp.replace(path)


def install(config_work_dir: Path, game_dir: Path, name: str, dry_run: bool = False) -> Path:
    pak_name = pak_file_name(name)
    source = config_work_dir / OUT_DIR_NAME / pak_name
    require_inside(source, config_work_dir, "pak")
    if not source.is_file():
        raise PakModError(f"pak not built yet: {source}. Run build {name} first.")
    mods_dir = mods_dir_of(game_dir)
    target = mods_dir / pak_name
    manifest = read_manifest(mods_dir)
    if target.exists() and pak_name not in manifest["files"]:
        raise PakModError(f"refusing to overwrite {target}: it is not in the harness manifest")
    print(f"{'[dry-run] ' if dry_run else ''}install {pak_name} -> {target}")
    if dry_run:
        return target
    created = not mods_dir.exists()
    mods_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    if sha256_of(target) != sha256_of(source):
        raise PakModError(f"copy check failed for {target}")
    manifest["files"][pak_name] = sha256_of(target)
    manifest["created_dir"] = bool(manifest["created_dir"] or created)
    write_manifest(mods_dir, manifest)
    return target


def remove_one(mods_dir: Path, manifest: dict, pak_name: str, dry_run: bool) -> bool:
    """Delete one manifest-listed pak if its hash still matches. Return True if the manifest entry can go."""
    target = mods_dir / pak_name
    if Path(pak_name).name != pak_name or not pak_name.endswith(".pak"):
        raise PakModError(f"manifest entry is not a plain pak file name: {pak_name!r}")
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
        raise PakModError(f"not in the harness manifest, not touched: {', '.join(unknown)}")
    skipped = 0
    for pak_name in wanted:
        if remove_one(mods_dir, manifest, pak_name, dry_run):
            manifest["files"].pop(pak_name)
        else:
            skipped += 1
    if not dry_run:
        finish_remove(mods_dir, manifest)
    return skipped


def finish_remove(mods_dir: Path, manifest: dict) -> None:
    manifest_path = mods_dir / MANIFEST_NAME
    if manifest["files"]:
        write_manifest(mods_dir, manifest)
        return
    manifest_path.unlink(missing_ok=True)
    if manifest["created_dir"] and mods_dir.is_dir() and not any(mods_dir.iterdir()):
        mods_dir.rmdir()
        print("removed empty ~mods folder")


# ---- list, check ----

def list_paks(game_dir: Path) -> list[str]:
    mods_dir = mods_dir_of(game_dir)
    manifest = read_manifest(mods_dir)
    lines = []
    for pak_name, expected in sorted(manifest["files"].items()):
        target = mods_dir / pak_name
        state = "missing" if not target.exists() else ("ok" if sha256_of(target) == expected else "CHANGED")
        lines.append(f"{pak_name}  {state}  {expected}")
    return lines


def check(config_path: Path, game_dir: Path) -> int:
    problems = config_problems(config_path)
    for problem in problems:
        print(f"MISSING: {problem}")
    if not (game_dir / "ManorLords").is_dir():
        problems.append("game folder")
        print(f"MISSING: game folder with ManorLords\\ not found: {game_dir}")
    if not problems:
        print(f"ok: config {config_path} is valid, game folder found")
        print("note: this does not run the packer. A real pak build is not verified by this check.")
    return 1 if problems else 0


# ---- command line ----

def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help="local config file (default: harness/pakmod.local.json)")
    parser.add_argument("--game-dir", type=Path, default=DEFAULT_GAME_DIR)
    parser.add_argument("--dry-run", action="store_true", help="report what would happen; change nothing")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("check", help="check the local config and the game folder")
    commands.add_parser("list", help="list the paks in the harness manifest")
    for name in ("build", "install"):
        commands.add_parser(name, help=f"{name} <name>").add_argument("name")
    remove_parser = commands.add_parser("remove", help="remove <name> or --all")
    remove_parser.add_argument("name", nargs="?")
    remove_parser.add_argument("--all", action="store_true")
    return parser


def dispatch(args: argparse.Namespace) -> int:
    if args.command == "check":
        return check(args.config, args.game_dir)
    if args.command == "list":
        print("\n".join(list_paks(args.game_dir)) or "no harness paks installed")
        return 0
    if args.command == "remove":
        if bool(args.name) == bool(args.all):
            raise PakModError("remove needs exactly one of <name> and --all")
        return 1 if remove(args.game_dir, None if args.all else [args.name], args.dry_run) else 0
    config = load_config(args.config)
    if args.command == "build":
        build(config, args.name, args.dry_run)
    else:
        install(config["work_dir"], args.game_dir, args.name, args.dry_run)
    return 0


def main(argv: list[str] | None = None) -> int:
    args = make_parser().parse_args(argv)
    try:
        return dispatch(args)
    except PakModError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
