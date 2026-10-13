"""Check, build and publish a mod release (spec 19).

  uv run python harness/release.py --mod RefugeeWaves --dry-run
  uv run python harness/release.py --mod RefugeeWaves --publish

Steps: manifest, version not tagged, changelog section, fake tests, real-game gate, zip, zip scan, then (with --publish)
tag and GitHub pre-release. Without --publish nothing leaves this PC. Exit code: 0 ok, 1 a check failed.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from releaselib import build, changelog, gate, scan
from releaselib.files import ClosureError, shared_closure
from releaselib.manifest import ManifestError, load_manifest

REPO_ROOT = Path(__file__).resolve().parent.parent
GH_CANDIDATES = ("gh", r"C:\Program Files\GitHub CLI\gh.exe")
TEST_COMMAND = [sys.executable, "-m", "unittest", "discover", "-s", "harness/tests", "-p", "test_*.py"]


class ReleaseError(Exception):
    """A release check failed. The message says what to do."""


def _run(command: list[str], *, cwd: Path = REPO_ROOT) -> subprocess.CompletedProcess:
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True)


def main_checkout() -> Path:
    """The folder of the main checkout. A worktree shares its git directory, so the common dir tells."""
    result = _run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"])
    if result.returncode != 0:
        return REPO_ROOT
    return Path(result.stdout.strip()).parent


def find_gh() -> str:
    for candidate in GH_CANDIDATES:
        try:
            if subprocess.run([candidate, "--version"], capture_output=True).returncode == 0:
                return candidate
        except OSError:
            continue
    raise ReleaseError("the GitHub CLI (gh) was not found")


def check_not_tagged(tag: str, *, offline: bool) -> None:
    if _run(["git", "tag", "--list", tag]).stdout.strip():
        raise ReleaseError(f"tag {tag} exists already. Raise the version in mod.json and add a changelog section.")
    remote = _run(["git", "ls-remote", "--tags", "origin", f"refs/tags/{tag}"])
    if remote.returncode != 0:
        if offline:
            print(f"warning: could not ask origin for tag {tag} ({remote.stderr.strip()[:100]})")
            return
        raise ReleaseError(f"could not ask origin for tags: {remote.stderr.strip()[:200]}. Use --offline to skip this check.")
    if remote.stdout.strip():
        raise ReleaseError(f"tag {tag} exists on origin. Raise the version in mod.json and add a changelog section.")


def run_fake_tests() -> None:
    result = _run(TEST_COMMAND)
    if result.returncode != 0:
        raise ReleaseError("the fake tests failed:\n" + (result.stderr or result.stdout)[-1500:])


def find_key_file(given: Path | None) -> Path:
    return given or main_checkout() / "modtools" / "work" / "aes_key.txt"


def read_key_or_fail(given: Path | None) -> str:
    path = find_key_file(given)
    try:
        return scan.read_key(path)
    except (FileNotFoundError, ValueError) as error:
        raise ReleaseError(f"{error}. The scan needs the key to prove it is not in the zip. Give --aes-key-file.") from error


def check_committed_paks(mod_dir: Path, key_file: Path | None) -> None:
    """The key must not be in a pak that is in the repo (CLAUDE.md Safety). The zip scan checks it again."""
    paks = sorted((mod_dir / build.PAK_FOLDER).glob("*.pak"))
    if not paks:
        return
    key = read_key_or_fail(key_file)
    problems = [p for pak in paks for p in scan.scan_bytes(pak.name, pak.read_bytes(), key)]
    if problems:
        raise ReleaseError("a committed pak holds the AES key. Do not commit it:\n  - " + "\n  - ".join(problems))
    print(f"ok: {len(paks)} committed pak(s) hold no AES key text")


def run_gate(manifest: dict, runs_root: Path, shared: list[str]) -> list[gate.GateResult]:
    wanted = gate.current_hashes(REPO_ROOT / "mod", manifest["name"], shared)
    runs = gate.real_runs(runs_root)
    results = []
    for scenario in manifest["gate_scenarios"]:
        try:
            results.append(gate.check_scenario(scenario, runs, wanted, manifest["tested"]["game_build"]))
        except gate.GateError as error:
            raise ReleaseError(str(error)) from error
    return results


def check_publish_state() -> None:
    if _run(["git", "status", "--porcelain"]).stdout.strip():
        raise ReleaseError("the working tree is not clean. Commit first; a release must come from committed files.")
    on_main = _run(["git", "merge-base", "--is-ancestor", "HEAD", "origin/main"])
    if on_main.returncode != 0:
        raise ReleaseError("HEAD is not in origin/main. Merge the work first, then release from main.")


def publish(manifest: dict, zip_path: Path, notes: str, tag: str) -> None:
    gh = find_gh()
    notes_file = zip_path.with_suffix(".notes.md")
    notes_file.write_text(notes, encoding="utf-8")
    for command in (["git", "tag", tag], ["git", "push", "origin", tag]):
        result = _run(command)
        if result.returncode != 0:
            raise ReleaseError(f"{' '.join(command)} failed: {result.stderr.strip()}")
    title = f"{manifest['name']} {manifest['version']}"
    result = _run([gh, "release", "create", tag, str(zip_path), "--prerelease", "--title", title, "--notes-file", str(notes_file)])
    if result.returncode != 0:
        raise ReleaseError(f"gh release create failed: {result.stderr.strip()}")
    print(result.stdout.strip())


def release(args: argparse.Namespace) -> None:
    mod_root = REPO_ROOT / "mod"
    mod_dir = mod_root / args.mod
    try:
        manifest = load_manifest(mod_dir)
        shared = shared_closure(mod_dir, mod_root / "shared", manifest["shared"])
    except (ManifestError, ClosureError) as error:
        raise ReleaseError(str(error)) from error
    tag = build.tag_name(manifest)
    print(f"ok: manifest {manifest['name']} {manifest['version']}; shared modules: {', '.join(shared) or 'none'}")
    check_not_tagged(tag, offline=args.offline)
    print(f"ok: tag {tag} is free")
    try:
        notes = changelog.release_notes(mod_dir / "CHANGELOG.md", manifest["version"])
    except changelog.ChangelogError as error:
        raise ReleaseError(str(error)) from error
    print("ok: changelog section found")
    if args.skip_tests:
        print("warning: fake tests skipped (--skip-tests)")
    else:
        run_fake_tests()
        print("ok: fake tests pass")
    for result in run_gate(manifest, Path(args.runs_root), shared):
        print(f"ok: gate '{result.scenario}' passed in real run {result.run_id} ({result.started}) with the current mod files")
    check_committed_paks(mod_dir, args.aes_key_file)
    for pak_file in sorted((mod_dir / build.PAK_FOLDER).glob("*.pak")):
        warning = build.pak_size_warning(pak_file.name, pak_file.stat().st_size)
        if warning:
            print(warning)
    zip_path = build.build_zip(manifest, mod_root, shared, Path(args.out_dir), REPO_ROOT, Path(args.pak_dir) if args.pak_dir else None)
    print(f"ok: built {zip_path}")
    problems = scan.scan_zip(zip_path, read_key_or_fail(args.aes_key_file))
    if problems:
        zip_path.unlink()
        raise ReleaseError("the zip scan failed (the zip was deleted):\n  - " + "\n  - ".join(problems))
    print("ok: scan clean (no harness-only module, no AES key text)")
    if not args.publish:
        print("dry run: no tag and no release were made" if args.dry_run else "no --publish: no tag and no release were made")
        return
    check_publish_state()
    publish(manifest, zip_path, notes, tag)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--mod", required=True, help="mod folder name under mod/")
    parser.add_argument("--dry-run", action="store_true", help="run every check and build the zip, but make no tag and no release")
    parser.add_argument("--publish", action="store_true", help="tag and create a GitHub pre-release")
    parser.add_argument("--runs-root", default=str(REPO_ROOT / "runs"), help="folder of the run results")
    parser.add_argument("--out-dir", default=str(REPO_ROOT / "dist"))
    parser.add_argument("--pak-dir", help="folder that holds <pak>_P.pak when mod.json pak.source is build")
    parser.add_argument("--aes-key-file", type=Path, help="default: modtools/work/aes_key.txt of the main checkout")
    parser.add_argument("--skip-tests", action="store_true", help="skip the fake tests (not for a real release)")
    parser.add_argument("--offline", action="store_true", help="do not fail when origin cannot be reached for the tag check")
    args = parser.parse_args(argv)
    if args.dry_run and args.publish:
        parser.error("--dry-run and --publish exclude each other")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        release(args)
    except ReleaseError as error:
        print(f"FAILED: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
