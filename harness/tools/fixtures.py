"""Manage save fixtures (spec 06, parts C and D).

    .venv\\Scripts\\python.exe harness\\tools\\fixtures.py list
    .venv\\Scripts\\python.exe harness\\tools\\fixtures.py import manor-bailey --source-slot saveGame_28 --description "..." --tags a,b
    .venv\\Scripts\\python.exe harness\\tools\\fixtures.py import my-test --from D:\\saves\\saveGame_5.sav --description "..."
    .venv\\Scripts\\python.exe harness\\tools\\fixtures.py uninstall
    .venv\\Scripts\\python.exe harness\\tools\\fixtures.py remove --appdata DIR
    .venv\\Scripts\\python.exe harness\\tools\\fixtures.py record base --source-slot saveGame_0   (old kind, no stored files)

`import` copies the files of a save into `harness/fixtures/saves/<name>/` (git ignores that folder) and writes the manifest entry.
A run installs a stored fixture into the user's save folder under a free slot name and removes it at the end (`runlib/saveslots.py`).
`uninstall` removes slots that a run left in the user's save folder (for example after `--keep-open`); only files with the hash in the
ledger are deleted. `remove` deletes a run's private appdata folder (DIR must be named `appdata`).
Exit code: 0 done, 1 a fixture or slot error, 3 a file in the user's save folder changed during a read (the tool says so).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from runlib import fixtures, saveslots  # noqa: E402


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manage save fixtures.")
    parser.add_argument("--user-saved-dir", type=Path, default=None,
                        help="the game's Saved folder (default: %%LOCALAPPDATA%%/ManorLords/Saved)")
    parser.add_argument("--manifest", type=Path, default=fixtures.MANIFEST_PATH)
    parser.add_argument("--store", type=Path, default=fixtures.STORE_DIR, help="folder of the stored fixture files")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list", help="show the fixtures")
    imported = commands.add_parser("import", help="copy a save into the fixture store and write its manifest entry")
    imported.add_argument("name")
    source = imported.add_mutually_exclusive_group(required=True)
    source.add_argument("--source-slot", help="a slot of the user's save folder, for example saveGame_28")
    source.add_argument("--from", dest="from_file", type=Path, help="a <slot>.sav file in any folder")
    imported.add_argument("--description", default="")
    imported.add_argument("--tags", default="", help="comma separated")
    commands.add_parser("uninstall", help="remove the slots that runs installed into the user's save folder")
    remove = commands.add_parser("remove", help="delete a private appdata folder")
    remove.add_argument("--appdata", type=Path, required=True)
    record = commands.add_parser("record", help="old kind: a manifest entry that points to a slot of the user's folder")
    record.add_argument("name")
    record.add_argument("--source-slot", required=True)
    record.add_argument("--description", default="")
    record.add_argument("--tags", default="", help="comma separated")
    return parser.parse_args(argv)


def tags_of(text: str) -> list[str]:
    return [tag for tag in text.split(",") if tag]


def import_save(args: argparse.Namespace, saved_dir: Path) -> dict:
    if args.from_file is not None:
        sources, origin = fixtures.files_of_save(args.from_file), f"file {args.from_file.name}"
        return fixtures.import_fixture(sources, args.manifest, args.name, args.description, tags_of(args.tags), origin, args.store)
    saves = saved_dir / "SaveGames"
    with fixtures.guarded(saves):  # the user's folder is only read
        sources = fixtures.files_of_save(saves / f"{args.source_slot}.sav")
        return fixtures.import_fixture(sources, args.manifest, args.name, args.description, tags_of(args.tags),
                                       f"user slot {args.source_slot}", args.store)


def run(args: argparse.Namespace) -> dict:
    saved_dir = args.user_saved_dir or fixtures.default_user_saved_dir()
    if args.command == "import":
        return import_save(args, saved_dir)
    if args.command == "uninstall":
        return {"uninstalled": saveslots.uninstall_all(saved_dir / "SaveGames")}
    if args.command == "record":
        return fixtures.record_fixture(saved_dir / "SaveGames", args.manifest, args.name, args.source_slot,
                                       args.description, tags_of(args.tags))
    if args.command == "remove":
        return {"removed_files": fixtures.remove_appdata(args.appdata)}
    return {"fixtures": fixtures.list_fixtures(fixtures.load_manifest(args.manifest))}


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        print(json.dumps(run(args), indent=2))
    except fixtures.SaveFolderChanged as error:
        print(f"{error}", file=sys.stderr)
        return 3
    except (fixtures.FixtureError, saveslots.SlotError) as error:
        print(f"fixture_error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
