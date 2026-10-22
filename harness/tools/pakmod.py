"""Find, extract, convert, build, install and remove asset mod paks (spec 09).

Tools: repak (pak files) and the UAssetGUI command line (one asset to JSON and back).
Commands: check [--pin], find <text>, extract <asset>, tojson <asset>, fromjson <json> [--to <name>],
roundtrip <asset>, build <name>, install <name>, remove <name>|--all, list.
Every command accepts --dry-run and --game-dir.

The tools are NOT part of this repo. Their paths and pinned SHA-256 hashes come from the local file
`harness/pakmod.local.json` (not committed). See `harness/pakmod.local.example.json`.

Exit codes: 0 ok, 1 error, 3 a tool does not match its pinned hash, 4 the built pak does not list the expected files.

Safety:
- A name must match NAME_PATTERN. A path that leaves the work folder is refused. Symlinks are refused.
- A tool runs as a list (no shell) with a time limit, and only when its SHA-256 matches the pinned value.
- The AES key is read from an environment variable. It is never stored, printed or logged.
- `install` writes only into <game>\\ManorLords\\Content\\Paks\\~mods and never replaces a file that is not in the manifest.
- `remove` deletes only files that the manifest lists, and only when their SHA-256 still matches.
- The tool never touches saves. It only reads the game's own paks.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import modpak  # noqa: E402
from tools import aes_env  # noqa: E402
from runlib.paks import (  # noqa: E402,F401 - the install code is shared with run.py --pak
    EXIT_ERROR, MANIFEST_NAME, NAME_PATTERN, PAK_SUFFIX, PakError, built_pak_path, check_name, install_pak, is_inside,
    list_paks, mods_dir_of, pak_file_name, paks_dir_of, read_manifest, remove, require_inside, sha256_of, write_manifest,
)

DEFAULT_GAME_DIR = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Manor Lords")
MODS_DIR = Path(__file__).resolve().parents[2] / "mod"
DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "pakmod.local.json"
ENV_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
PLACEHOLDER_PATTERN = re.compile(r"\{[a-z_]+\}")
RESERVED_FOLDERS = ("out", "extracted", "json", "fromjson", "roundtrip", ".index-cache")
ASSET_EXTENSIONS = (".uasset", ".uexp", ".ubulk", ".uptnl")
TOOLS = ("repak", "uassetgui")
TOOL_LAUNCHERS = {".py": [sys.executable]}  # tests use Python scripts as fake tools
DEFAULT_MOUNT_POINT = "../../../"
DEFAULT_PAK_VERSION = "V11"
FIND_LIMIT = 50
REPAK_TIMEOUT_S = 300
PACK_TIMEOUT_S = 300
UASSETGUI_TIMEOUT_S = 120
VERSION_TIMEOUT_S = 10
EXIT_HASH_MISMATCH = 3
EXIT_PAK_MISMATCH = 4

# Argument templates, without the tool path. A config key "templates" can replace any of them,
# because the real tools may differ by version. Facts: implementation-notes/cli-reference.md.
DEFAULT_TEMPLATES = {
    "list": ["list", "-s", "{mount_point}", "{pak}"],
    "get": ["get", "-s", "{mount_point}", "{pak}", "{file}"],
    "pack": ["pack", "--mount-point", "{mount_point}", "--version", "{pak_version}", "{input}", "{output}"],
    "tojson": ["tojson", "{source}", "{destination}", "{engine_version}", "{usmap}"],
    "fromjson": ["fromjson", "{source}", "{destination}", "{usmap}"],
}
DEFAULT_VERSION_ARGS = {"repak": ["--version"]}  # UAssetGUI has no documented version flag
CONFIG_EXAMPLE = {
    "repak": {"path": "C:/tools/repak.exe", "sha256": ""},
    "uassetgui": {"path": "C:/tools/UAssetGUI.exe", "sha256": ""},
    "usmap": "C:/modwork/ManorLords.usmap",
    "usmap_name": "ManorLords",
    "engine_version": "VER_UE5_5",
    "work_dir": "C:/modwork",
}


PakModError = PakError  # one error type for the library and the command line


class ToolHashMismatch(PakModError):
    exit_code = EXIT_HASH_MISMATCH


class PakListMismatch(PakModError):
    exit_code = EXIT_PAK_MISMATCH


# ---- names and paths ----

def check_mod_name(name: str) -> str:
    """A mod name also must not clash with a work folder that has another job."""
    if check_name(name).lower() in RESERVED_FOLDERS:
        raise PakModError(f"name {name!r} is reserved for a work folder")
    return name


def clean_internal_path(text: str) -> str:
    """Normalize a game-internal asset path (no extension) and refuse anything that could leave the work folder."""
    path = text.strip().replace("\\", "/")
    for extension in ASSET_EXTENSIONS:
        if path.lower().endswith(extension):
            path = path[: -len(extension)]
    parts = path.split("/")
    bad = (not path or path.startswith("/") or ":" in path or any(part in ("", ".", "..") for part in parts))
    if bad:
        raise PakModError(f"bad asset path {text!r}: use a relative path like ManorLords/Content/Folder/Asset, without '..'")
    return path


# ---- config ----

def read_raw_config(path: Path) -> dict:
    path = Path(path)
    if not path.is_file():
        raise PakModError(f"config file missing: {path}. Copy harness/pakmod.local.example.json and fill it in.")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise PakModError(f"config file is not valid JSON: {error}") from error
    if not isinstance(raw, dict):
        raise PakModError("config must be a JSON object")
    return raw


def tool_problems(raw: dict, name: str) -> list[str]:
    entry = raw.get(name)
    if not isinstance(entry, dict) or not isinstance(entry.get("path"), str) or not entry["path"]:
        return [f"config key '{name}' must be an object with a 'path'"]
    pin = entry.get("sha256", "")
    if not isinstance(pin, str) or (pin and not re.fullmatch(r"[0-9A-Fa-f]{64}", pin)):
        return [f"config '{name}.sha256' must be empty or 64 hex characters"]
    return []


def text_problems(raw: dict, key: str) -> list[str]:
    value = raw.get(key)
    return [] if isinstance(value, str) and value else [f"config key '{key}' is missing"]


def option_problems(raw: dict) -> list[str]:
    problems = []
    env_name = raw.get("aes_key_env")
    if env_name is not None:
        # Do not echo the value: a user may have pasted the key here by mistake.
        if not isinstance(env_name, str) or not ENV_NAME_PATTERN.fullmatch(env_name) or len(env_name) >= 32:
            problems.append("config 'aes_key_env' must be the NAME of an environment variable, not the key")
    name = raw.get("usmap_name")
    if name is not None and (not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,40}", name)):
        problems.append("config 'usmap_name' must be a plain file name without extension (letters, digits, _ and -)")
    templates = raw.get("templates", {})
    if not isinstance(templates, dict) or not all(
        isinstance(value, list) and all(isinstance(item, str) for item in value) for value in templates.values()
    ):
        problems.append("config 'templates' must map a command name to a list of strings")
    return problems


def config_problems(path: Path) -> list[str]:
    """All problems of the config file itself. Tool and mapping files are checked later."""
    try:
        raw = read_raw_config(path)
    except PakModError as error:
        return [str(error)]
    problems = []
    for name in TOOLS:
        problems += tool_problems(raw, name)
    for key in ("usmap", "engine_version", "work_dir"):
        problems += text_problems(raw, key)
    problems += option_problems(raw)
    work_dir = raw.get("work_dir")
    if isinstance(work_dir, str) and work_dir and not Path(work_dir).is_dir():
        problems.append(f"work_dir is not a folder: {work_dir}")
    return problems


def load_config(path: Path) -> dict:
    """Read and validate the local config. Raise PakModError with all problems."""
    problems = config_problems(path)
    if problems:
        raise PakModError("; ".join(problems))
    raw = read_raw_config(path)
    templates = {**DEFAULT_TEMPLATES, **raw.get("templates", {})}
    config = {
        "config_path": Path(path),
        "usmap": Path(raw["usmap"]),
        "usmap_name": raw.get("usmap_name"),
        "engine_version": raw["engine_version"],
        "work_dir": Path(raw["work_dir"]),
        "pak_version": raw.get("pak_version") or DEFAULT_PAK_VERSION,
        "mount_point": raw.get("mount_point") or DEFAULT_MOUNT_POINT,
        "aes_key_env": raw.get("aes_key_env"),
        "templates": templates,
    }
    for name in TOOLS:
        config[name] = {"path": Path(raw[name]["path"]), "sha256": raw[name].get("sha256", "").upper()}
    return config


def write_pins(config_path: Path, pins: dict[str, str]) -> None:
    """Store tool hashes in the config. This is an explicit action (`check --pin`)."""
    raw = read_raw_config(config_path)
    for name, digest in pins.items():
        raw[name]["sha256"] = digest
    temp = Path(config_path).with_name(Path(config_path).name + ".tmp")
    temp.write_text(json.dumps(raw, indent=2) + "\n", encoding="utf-8")
    temp.replace(config_path)


# ---- running the tools ----

_HASH_MEMO: dict[tuple, str] = {}


def tool_hash(path: Path) -> str:
    """Hash a tool file. The result is remembered per file state, so many calls stay fast."""
    stat = Path(path).stat()
    key = (str(path), stat.st_size, stat.st_mtime_ns)
    if key not in _HASH_MEMO:
        _HASH_MEMO[key] = sha256_of(path)
    return _HASH_MEMO[key]


def verify_tool(config: dict, name: str) -> None:
    tool = config[name]
    if not tool["path"].is_file():
        raise PakModError(f"{name} not found: {tool['path']}")
    if not tool["sha256"]:
        raise PakModError(f"{name} has no pinned hash. Run 'check --pin' after you reviewed the file {tool['path']}")
    actual = tool_hash(tool["path"])
    if actual != tool["sha256"]:
        raise ToolHashMismatch(f"{name} does not match its pinned SHA-256 and is NOT run: {tool['path']} has {actual}")


def aes_key_args(config: dict) -> list[str]:
    env_name = config["aes_key_env"]
    if not env_name:
        return []
    key = read_key(env_name)
    if not key:
        raise PakModError(f"environment variable {env_name} is not set and {aes_env.env_file()} has no key "
                          "(run harness/tools/aes_env.py)")
    return ["--aes-key", key]


def read_key(env_name: str) -> str | None:
    """The environment wins. The gitignored `.env` of the main checkout is the fallback."""
    key = os.environ.get(env_name)
    if key:
        return key
    if env_name == aes_env.ENV_NAME:
        return aes_env.read_env_key(aes_env.env_file())
    return None


def secret_values(config: dict) -> list[str]:
    key = read_key(config["aes_key_env"] or "")
    return [key] if key else []


def redact(text: str, secrets: list[str]) -> str:
    for secret in secrets:
        text = text.replace(secret, "***")
    return text


def launcher_of(path: Path) -> list[str]:
    return TOOL_LAUNCHERS.get(Path(path).suffix.lower(), []) + [str(path)]


def fill_template(template: list[str], values: dict[str, str]) -> list[str]:
    args = []
    for item in template:
        for key, value in values.items():
            item = item.replace("{" + key + "}", value)
        left = PLACEHOLDER_PATTERN.search(item)
        if left:
            raise PakModError(f"command template has an unknown placeholder {left.group(0)}: {item}")
        args.append(item)
    return args


def tool_command(config: dict, tool: str, command_name: str, values: dict[str, str], show_key: bool = False) -> list[str]:
    """The full command as a list. Only `repak` gets the AES key. The key is masked unless `show_key`."""
    key_args = aes_key_args(config) if tool == "repak" else []
    if key_args and not show_key:
        key_args[1] = "***"
    values = {**values, "mount_point": config["mount_point"], "pak_version": config["pak_version"],
              "engine_version": config["engine_version"], "usmap": config.get("usmap_name") or str(config["usmap"])}
    return launcher_of(config[tool]["path"]) + key_args + fill_template(config["templates"][command_name], values)


def run_tool(config: dict, tool: str, command_name: str, values: dict[str, str], timeout_s: float) -> bytes:
    """Run one tool command after the hash check. Return stdout bytes. Raise PakModError on any failure."""
    verify_tool(config, tool)
    command = tool_command(config, tool, command_name, values, show_key=True)
    secrets = secret_values(config)
    try:
        done = subprocess.run(command, capture_output=True, timeout=timeout_s, shell=False)
    except subprocess.TimeoutExpired as error:
        raise PakModError(f"{tool} {command_name} did not finish in {timeout_s:.0f} s and was stopped") from error
    except OSError as error:
        raise PakModError(f"{tool} could not start: {error}") from error
    if done.returncode != 0:
        tail = redact((done.stdout + done.stderr).decode("utf-8", "replace").strip()[-500:], secrets)
        raise PakModError(f"{tool} {command_name} failed with exit code {done.returncode}: {tail}")
    return done.stdout


def print_command(config: dict, tool: str, command_name: str, values: dict[str, str]) -> None:
    print(f"  command: {tool_command(config, tool, command_name, values)}")


# ---- check ----

def tool_version_line(config: dict, name: str) -> str | None:
    version_args = DEFAULT_VERSION_ARGS.get(name)
    if not version_args:
        return None
    command = launcher_of(config[name]["path"]) + version_args
    try:
        done = subprocess.run(command, capture_output=True, timeout=VERSION_TIMEOUT_S, shell=False)
    except (subprocess.TimeoutExpired, OSError):
        return None
    lines = done.stdout.decode("utf-8", "replace").strip().splitlines()
    return lines[0] if done.returncode == 0 and lines else None


def check_tool(config: dict, name: str, pin: bool, dry_run: bool, pins: dict[str, str]) -> list[str]:
    """Report one tool. Raise ToolHashMismatch on a wrong hash. Return the problems found."""
    tool = config[name]
    if not tool["path"].is_file():
        return [f"{name} not found: {tool['path']}"]
    actual = tool_hash(tool["path"])
    if pin:
        pins[name] = actual
        tool["sha256"] = actual
        print(f"{name}: sha256 {actual} {'would be pinned (dry-run)' if dry_run else 'pinned'}")
    if not tool["sha256"]:
        return [f"{name} has no pinned hash. Review the file, then run 'check --pin'"]
    if actual != tool["sha256"]:
        raise ToolHashMismatch(f"{name} does not match its pinned SHA-256: {tool['path']} has {actual}, config has {tool['sha256']}")
    version = tool_version_line(config, name)
    print(f"{name}: ok, sha256 matches. Version: {version or 'unknown (no version flag known)'}")
    return []


def uassetgui_mappings_file(config: dict) -> Path | None:
    """UAssetGUI 1.1.0 takes a mapping NAME and reads `<LOCALAPPDATA>/UAssetGUI/Mappings/<name>.usmap`. It ignores a path."""
    if not config.get("usmap_name"):
        return None
    return Path(os.environ.get("LOCALAPPDATA", "")) / "UAssetGUI" / "Mappings" / f"{config['usmap_name']}.usmap"


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mapping_problem(config: dict) -> str | None:
    """Without the right mapping, UAssetGUI 1.1.0 exits with 0 and writes raw bytes. So this is checked before each run."""
    target = uassetgui_mappings_file(config)
    if target is None:
        return None
    if not target.is_file():
        return f"mapping not installed for UAssetGUI: copy {config['usmap']} to {target}"
    if file_sha256(target) != file_sha256(config["usmap"]):
        return f"mapping {target} differs from {config['usmap']}: copy the newer file"
    return None


def check(config_path: Path, game_dir: Path, pin: bool = False, dry_run: bool = False) -> int:
    problems = config_problems(config_path)
    if problems:
        for problem in problems:
            print(f"PROBLEM: {problem}")
        return EXIT_ERROR
    config = load_config(config_path)
    pins: dict[str, str] = {}
    for name in TOOLS:
        problems += check_tool(config, name, pin, dry_run, pins)
    if not config["usmap"].is_file():
        problems.append(f"usmap file not found: {config['usmap']}. Make it with the UE4SS dumper (see harness/README.md).")
    if config["usmap"].is_file() and mapping_problem(config):
        problems.append(mapping_problem(config))
    if not paks_dir_of(game_dir).is_dir():
        problems.append(f"game Paks folder not found: {paks_dir_of(game_dir)}")
    if pins and not dry_run:
        write_pins(config_path, pins)
    for problem in problems:
        print(f"PROBLEM: {problem}")
    if not problems:
        print(f"ok: config {config_path} is valid. Work folder {config['work_dir']}.")
        print("note: this does not run a conversion or a pack. Real tool behavior is not verified by this check.")
    return EXIT_ERROR if problems else 0


# ---- atomic file writes ----

def write_bytes_atomic(target: Path, data: bytes) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_name(target.name + ".tmp")
    temp.write_bytes(data)
    temp.replace(target)


# ---- find and extract ----

def game_paks(game_dir: Path) -> list[Path]:
    """The game's own paks. The ~mods folder is a subfolder and is not searched."""
    folder = paks_dir_of(game_dir)
    if not folder.is_dir():
        raise PakModError(f"game Paks folder not found: {folder}")
    return sorted(path for path in folder.glob("*.pak") if path.is_file())


def cache_file_of(config: dict, pak: Path) -> Path:
    return config["work_dir"] / ".index-cache" / (pak.name + ".json")


def read_cached_index(cache_file: Path, pak: Path) -> list[str] | None:
    """Return the cached entries if the pak has the same size and mtime. Return None otherwise."""
    try:
        cached = json.loads(cache_file.read_text(encoding="utf-8"))
        stat = pak.stat()
        if cached["size"] == stat.st_size and cached["mtime_ns"] == stat.st_mtime_ns:
            return list(cached["entries"])
    except (OSError, ValueError, KeyError):
        pass
    return None


def pak_index(config: dict, pak: Path) -> list[str]:
    cache_file = cache_file_of(config, pak)
    entries = read_cached_index(cache_file, pak)
    if entries is not None:
        return entries
    output = run_tool(config, "repak", "list", {"pak": str(pak)}, REPAK_TIMEOUT_S)
    entries = [line.strip() for line in output.decode("utf-8", "replace").splitlines() if line.strip()]
    stat = pak.stat()
    document = {"size": stat.st_size, "mtime_ns": stat.st_mtime_ns, "entries": entries}
    write_bytes_atomic(cache_file, json.dumps(document).encode("utf-8"))
    return entries


def find(config: dict, game_dir: Path, text: str, dry_run: bool = False) -> list[tuple[str, str]]:
    """Case-insensitive substring search in the index of every game pak. Return (pak name, path), at most FIND_LIMIT."""
    if not text:
        raise PakModError("find needs a search text")
    paks = game_paks(game_dir)
    if dry_run:
        print(f"[dry-run] find {text!r} in {len(paks)} paks of {paks_dir_of(game_dir)}")
        return []
    needle = text.lower()
    matches: list[tuple[str, str]] = []
    for pak in paks:
        for entry in pak_index(config, pak):
            if needle in entry.lower():
                matches.append((pak.name, entry))
    for pak_name, entry in matches[:FIND_LIMIT]:
        print(f"{pak_name}  {entry}")
    more = f" (first {FIND_LIMIT} shown)" if len(matches) > FIND_LIMIT else ""
    print(f"{len(matches)} matches in {len(paks)} paks{more}")
    return matches[:FIND_LIMIT]


def locate_asset(config: dict, game_dir: Path, internal: str) -> tuple[Path, dict[str, str]]:
    """Find the pak that holds `<internal>.uasset`. Return it and the entries of the asset's files by extension.
    If several paks hold it, the last one by name wins, because patch paks sort after the base paks."""
    wanted = {internal.lower() + extension: extension for extension in ASSET_EXTENSIONS}
    holders = []
    for pak in game_paks(game_dir):
        found = {wanted[entry.lower()]: entry for entry in pak_index(config, pak) if entry.lower() in wanted}
        if ".uasset" in found:
            holders.append((pak, found))
    if not holders:
        raise PakModError(f"asset not found in any game pak: {internal}.uasset. Use 'find' to search.")
    if len(holders) > 1:
        print(f"note: {len(holders)} paks hold this asset, using the last: {holders[-1][0].name}")
    return holders[-1]


def extracted_dir(config: dict) -> Path:
    return config["work_dir"] / "extracted"


def extract(config: dict, game_dir: Path, asset: str, dry_run: bool = False) -> list[Path]:
    internal = clean_internal_path(asset)
    folder = extracted_dir(config)
    print(f"{'[dry-run] ' if dry_run else ''}extract {internal} -> {folder / internal}.*")
    if dry_run:
        return []
    pak, entries = locate_asset(config, game_dir, internal)
    written = []
    for extension, entry in sorted(entries.items()):
        target = require_inside(folder / (entry[: -len(extension)] + extension), folder, "extracted file")
        data = run_tool(config, "repak", "get", {"pak": str(pak), "file": entry}, REPAK_TIMEOUT_S)
        if not data:
            raise PakModError(f"repak get returned no data for {entry} in {pak.name}")
        write_bytes_atomic(target, data)
        written.append(target)
        print(f"  {target} ({len(data)} bytes)")
    if ".uexp" not in entries:
        print("note: the pak has no .uexp for this asset (it may be a single-file asset)")
    return written


# ---- UAssetGUI: tojson, fromjson, roundtrip ----

def resolve_work_file(config: dict, argument: str, what: str, first_folder: Path | None = None) -> Path:
    """A file in the work folder. A relative path is tried under `first_folder` (default: extracted), then under the work folder."""
    given = Path(argument)
    first_folder = first_folder or extracted_dir(config)
    candidates = [given] if given.is_absolute() else [first_folder / given, config["work_dir"] / given]
    for candidate in candidates:
        if candidate.is_file():
            return require_inside(candidate, config["work_dir"], what)
    raise PakModError(f"{what} not found: {argument}. Run extract or tojson first, or give a path inside {config['work_dir']}.")


def relative_to_any(path: Path, folders: list[Path]) -> Path:
    """The path below the first folder that holds it. Fall back to the file name."""
    for folder in folders:
        if is_inside(path, folder):
            return path.resolve().relative_to(folder.resolve())
    return Path(path.name)


def run_uassetgui(config: dict, command_name: str, source: Path, destination: Path) -> None:
    if not config["usmap"].is_file():
        raise PakModError(f"usmap file not found: {config['usmap']}")
    if mapping_problem(config):
        raise PakModError(mapping_problem(config))
    require_inside(destination, config["work_dir"], "output file")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.unlink(missing_ok=True)  # an old file must not pass the output check
    values = {"source": str(source), "destination": str(destination)}
    run_tool(config, "uassetgui", command_name, values, UASSETGUI_TIMEOUT_S)
    if not destination.is_file() or destination.stat().st_size == 0:
        raise PakModError(f"uassetgui {command_name} ended without an error but wrote no usable file: {destination}")
    if command_name == "tojson" and b"UAssetAPI.ExportTypes.RawExport" in destination.read_bytes():
        raise PakModError(f"tojson wrote a RawExport (the mapping was not used, so no field can be edited): {destination}")
    print(f"  {destination} ({destination.stat().st_size} bytes)")


def json_path_of(config: dict, asset: Path) -> Path:
    below = relative_to_any(asset, [extracted_dir(config), config["work_dir"]])
    return config["work_dir"] / "json" / below.with_suffix(".json")


def tojson(config: dict, asset_argument: str, dry_run: bool = False) -> Path:
    asset = resolve_work_file(config, asset_argument, "asset")
    destination = json_path_of(config, asset)
    print(f"{'[dry-run] ' if dry_run else ''}tojson {asset} -> {destination}")
    if dry_run:
        print_command(config, "uassetgui", "tojson", {"source": str(asset), "destination": str(destination)})
        return destination
    run_uassetgui(config, "tojson", asset, destination)
    return destination


def asset_path_of_json(config: dict, json_file: Path, to_name: str | None) -> Path:
    below = relative_to_any(json_file, [config["work_dir"] / "json"]).with_suffix(".uasset")
    folder = config["work_dir"] / (check_mod_name(to_name) if to_name else "fromjson")
    return folder / below


def fromjson(config: dict, json_argument: str, to_name: str | None = None, dry_run: bool = False) -> Path:
    json_file = resolve_work_file(config, json_argument, "json file", config["work_dir"] / "json")
    destination = asset_path_of_json(config, json_file, to_name)
    print(f"{'[dry-run] ' if dry_run else ''}fromjson {json_file} -> {destination}")
    if dry_run:
        print_command(config, "uassetgui", "fromjson", {"source": str(json_file), "destination": str(destination)})
        return destination
    run_uassetgui(config, "fromjson", json_file, destination)
    return destination


def compare_files(original: Path, other: Path) -> dict:
    """Compare two files byte by byte. `first_diff` is the first differing offset (or the shorter size)."""
    a, b = original.read_bytes(), other.read_bytes()
    first = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), None)
    if first is None and len(a) != len(b):
        first = min(len(a), len(b))
    return {"equal": a == b, "size_original": len(a), "size_new": len(b), "first_diff": first}


def report_comparison(extension: str, result: dict) -> None:
    if result["equal"]:
        print(f"  {extension}: equal ({result['size_original']} bytes)")
        return
    print(f"  {extension}: DIFFERENT, original {result['size_original']} bytes, new {result['size_new']} bytes, "
          f"first difference at offset {result['first_diff']}")


def roundtrip(config: dict, game_dir: Path, asset_argument: str, dry_run: bool = False) -> dict:
    """tojson then fromjson, then compare with the original. A difference is a result, not an error."""
    if dry_run:
        print(f"[dry-run] roundtrip {asset_argument}: would extract (if needed), tojson, fromjson, compare")
        return {}
    try:
        asset = resolve_work_file(config, asset_argument, "asset")
    except PakModError:
        asset = next(path for path in extract(config, game_dir, asset_argument) if path.suffix == ".uasset")
    json_file = tojson(config, str(asset))
    below = relative_to_any(asset, [extracted_dir(config), config["work_dir"]])
    second = config["work_dir"] / "roundtrip" / below
    run_uassetgui(config, "fromjson", json_file, second)
    results = {}
    for extension in (".uasset", ".uexp"):
        original = asset.with_suffix(extension)
        if not original.is_file():
            print(f"  {extension}: not in the original, skipped")
            continue
        new = second.with_suffix(extension)
        if not new.is_file():
            results[extension] = {"equal": False, "size_original": original.stat().st_size, "size_new": 0, "first_diff": 0}
        else:
            results[extension] = compare_files(original, new)
        report_comparison(extension, results[extension])
    print("roundtrip: " + ("equal" if results and all(r["equal"] for r in results.values()) else "different"))
    return results


# ---- build ----

def asset_folder(config: dict, name: str) -> Path:
    folder = config["work_dir"] / check_mod_name(name)
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


def expected_entries(folder: Path, files: list[Path]) -> set[str]:
    return {file.relative_to(folder).as_posix() for file in files}


def pak_list_difference(expected: set[str], actual: set[str]) -> list[str]:
    lines = [f"missing in the pak: {entry}" for entry in sorted(expected - actual)]
    return lines + [f"unexpected in the pak: {entry}" for entry in sorted(actual - expected)]


def build(config: dict, name: str, dry_run: bool = False) -> Path:
    folder = asset_folder(config, name)
    files = list_asset_files(folder, config["work_dir"])
    output = config["work_dir"] / "out" / pak_file_name(name)
    print(f"{'[dry-run] ' if dry_run else ''}build {name}: {len(files)} files -> {output}")
    values = {"input": str(folder), "output": str(output), "pak": str(output)}
    print_command(config, "repak", "pack", values)
    if dry_run:
        return output
    output.parent.mkdir(exist_ok=True)
    output.unlink(missing_ok=True)
    run_tool(config, "repak", "pack", values, PACK_TIMEOUT_S)
    if not output.is_file():
        raise PakModError(f"repak ended without an error but wrote no pak: {output}")
    print(f"built {output} ({output.stat().st_size} bytes)")
    verify_pak_list(config, output, expected_entries(folder, files))
    return output


def verify_pak_list(config: dict, pak: Path, expected: set[str]) -> None:
    listing = run_tool(config, "repak", "list", {"pak": str(pak)}, REPAK_TIMEOUT_S)
    actual = {line.strip() for line in listing.decode("utf-8", "replace").splitlines() if line.strip()}
    differences = pak_list_difference(expected, actual)
    if differences:
        raise PakListMismatch("the built pak does not list the folder's files:\n  " + "\n  ".join(differences))
    print(f"verified: the pak lists the same {len(actual)} files as the folder")


def buildmod(config: dict, game_dir: Path, name: str, mods_dir: Path = MODS_DIR, dry_run: bool = False) -> Path:
    """Build mod/<name>/paks/<name>_P.pak from the row patches of all features (spec 22). Starts from the current game paks."""
    mod_dir = mods_dir / check_mod_name(name)
    folder = config["work_dir"] / name
    print(f"{'[dry-run] ' if dry_run else ''}buildmod {name}: {mod_dir} -> {pak_file_name(name)}")
    if dry_run:
        return mod_dir / "paks" / pak_file_name(name)
    require_inside(folder, config["work_dir"], "asset folder")
    shutil.rmtree(folder, ignore_errors=True)  # no stale file from an earlier build
    folder.mkdir(parents=True)

    def fetch(asset: str) -> Path:
        extract(config, game_dir, asset)
        return tojson(config, asset + ".uasset")

    try:
        return modpak.build_mod(mod_dir, folder, fetch, lambda json_file: fromjson(config, str(json_file), name),
                                lambda: build(config, name))
    except modpak.ModPakError as error:
        raise PakModError(str(error)) from error


# ---- manifest, install, remove ----

def install(work_dir: Path, game_dir: Path, name: str, dry_run: bool = False) -> Path:
    pak_name = pak_file_name(name)
    source = built_pak_path(work_dir, name)
    require_inside(source, work_dir, "pak")
    if not source.is_file():
        raise PakModError(f"pak not built yet: {source}. Run build {name} first.")
    return install_pak(source, game_dir, pak_name, dry_run)


# ---- command line ----

def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help="local config file (default: harness/pakmod.local.json)")
    parser.add_argument("--game-dir", type=Path, default=DEFAULT_GAME_DIR)
    parser.add_argument("--dry-run", action="store_true", help="report what would happen; change nothing")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("check", help="check the config, the tools and their hashes").add_argument(
        "--pin", action="store_true", help="write the current tool hashes into the config")
    commands.add_parser("list", help="list the paks in the harness manifest")
    commands.add_parser("find", help="find <text> in the game's pak indexes").add_argument("text")
    for name in ("extract", "tojson", "roundtrip", "build", "install"):
        commands.add_parser(name, help=f"{name} <asset or name>").add_argument("target")
    commands.add_parser("buildmod", help="buildmod <mod name>: build mod/<name>/paks from the row patches").add_argument("target")
    fromjson_parser = commands.add_parser("fromjson", help="fromjson <json file> [--to <mod name>]")
    fromjson_parser.add_argument("target")
    fromjson_parser.add_argument("--to", help="write the asset into the build folder of this mod name")
    remove_parser = commands.add_parser("remove", help="remove <name> or --all")
    remove_parser.add_argument("name", nargs="?")
    remove_parser.add_argument("--all", action="store_true")
    return parser


def dispatch(args: argparse.Namespace) -> int:
    if args.command == "check":
        return check(args.config, args.game_dir, args.pin, args.dry_run)
    if args.command == "list":
        print("\n".join(list_paks(args.game_dir)) or "no harness paks installed")
        return 0
    if args.command == "remove":
        if bool(args.name) == bool(args.all):
            raise PakModError("remove needs exactly one of <name> and --all")
        return 1 if remove(args.game_dir, None if args.all else [args.name], args.dry_run) else 0
    config = load_config(args.config)
    handlers = {
        "find": lambda: find(config, args.game_dir, args.text, args.dry_run),
        "extract": lambda: extract(config, args.game_dir, args.target, args.dry_run),
        "tojson": lambda: tojson(config, args.target, args.dry_run),
        "fromjson": lambda: fromjson(config, args.target, getattr(args, "to", None), args.dry_run),
        "roundtrip": lambda: roundtrip(config, args.game_dir, args.target, args.dry_run),
        "build": lambda: build(config, args.target, args.dry_run),
        "buildmod": lambda: buildmod(config, args.game_dir, args.target, dry_run=args.dry_run),
        "install": lambda: install(config["work_dir"], args.game_dir, args.target, args.dry_run),
    }
    handlers[args.command]()
    return 0


def main(argv: list[str] | None = None) -> int:
    args = make_parser().parse_args(argv)
    try:
        return dispatch(args)
    except PakModError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return error.exit_code


if __name__ == "__main__":
    sys.exit(main())
