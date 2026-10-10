"""Manage save fixtures (spec 06, part C).

    .venv\\Scripts\\python.exe harness\\tools\\fixtures.py list
    .venv\\Scripts\\python.exe harness\\tools\\fixtures.py record base --source-slot saveGame_0 --description "..."
    .venv\\Scripts\\python.exe harness\\tools\\fixtures.py install base --appdata DIR
    .venv\\Scripts\\python.exe harness\\tools\\fixtures.py remove --appdata DIR

A fixture is installed into a private appdata folder (DIR must be named `appdata`), never next to the user's saves.
`run.py` does this for every run. `install` and `remove` are for manual tests.
The user's save folder is only read, and all its files are hashed before and after each command.
Exit code: 0 done, 1 a fixture error, 3 a file in the user's save folder changed (the tool says so).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from runlib import fixtures  # noqa: E402


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manage save fixtures.")
    parser.add_argument("--user-saved-dir", type=Path, default=None,
                        help="the game's Saved folder (default: %%LOCALAPPDATA%%/ManorLords/Saved)")
    parser.add_argument("--manifest", type=Path, default=fixtures.MANIFEST_PATH)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list", help="show the fixtures")
    install = commands.add_parser("install", help="copy a fixture and the config into a private appdata folder")
    install.add_argument("name")
    install.add_argument("--appdata", type=Path, required=True, help="target folder, named 'appdata'")
    remove = commands.add_parser("remove", help="delete a private appdata folder")
    remove.add_argument("--appdata", type=Path, required=True)
    record = commands.add_parser("record", help="write or update a manifest entry from the files of a slot")
    record.add_argument("name")
    record.add_argument("--source-slot", required=True)
    record.add_argument("--description", default="")
    record.add_argument("--tags", default="", help="comma separated")
    return parser.parse_args(argv)


def run(args: argparse.Namespace) -> dict:
    saved_dir = args.user_saved_dir or fixtures.default_user_saved_dir()
    if args.command == "record":
        tags = [tag for tag in args.tags.split(",") if tag]
        return fixtures.record_fixture(saved_dir / "SaveGames", args.manifest, args.name, args.source_slot,
                                       args.description, tags)
    if args.command == "remove":
        return {"removed_files": fixtures.remove_appdata(args.appdata)}
    manifest = fixtures.load_manifest(args.manifest)
    if args.command == "list":
        return {"fixtures": fixtures.list_fixtures(manifest)}
    if args.appdata.name != fixtures.APPDATA_NAME:
        raise fixtures.FixtureError(f"the target folder must be named '{fixtures.APPDATA_NAME}'")
    return fixtures.prepare_appdata(saved_dir, args.appdata, manifest, args.name).as_dict()


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        print(json.dumps(run(args), indent=2))
    except fixtures.SaveFolderChanged as error:
        print(f"{error}", file=sys.stderr)
        return 3
    except fixtures.FixtureError as error:
        print(f"fixture_error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
