"""Facts about the setup of a run. They go into summary.environment, so a result can be traced."""

from __future__ import annotations

import hashlib
import platform
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from .game import GameInstall

GIT_TIMEOUT_S = 15


def sha256_of_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as source:  # read only
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_of_folder(folder: Path) -> str:
    """One hash for all files of a folder. File names count, so a rename changes the hash."""
    digest = hashlib.sha256()
    for path in sorted(p for p in folder.rglob("*") if p.is_file()):
        digest.update(path.relative_to(folder).as_posix().encode("utf-8") + b"\0")
        digest.update(sha256_of_file(path).encode("ascii"))
    return digest.hexdigest()


def hash_mods(mod_dir: Path) -> dict[str, str]:
    return {folder.name: sha256_of_folder(folder) for folder in sorted(mod_dir.iterdir()) if folder.is_dir()}


def read_build_id(appmanifest: Path) -> str:
    match = re.search(r'"buildid"\s+"(\d+)"', appmanifest.read_text(encoding="utf-8", errors="replace"))
    if not match:
        raise RuntimeError(f"no buildid in {appmanifest}")
    return match.group(1)


def _git(repo_root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repo_root, capture_output=True, text=True, timeout=GIT_TIMEOUT_S, check=True
    )
    return result.stdout.strip()


def git_state(repo_root: Path) -> dict:
    return {
        "commit": _git(repo_root, "rev-parse", "HEAD"),
        "dirty": bool(_git(repo_root, "status", "--porcelain")),
    }


def gather_environment(install: GameInstall, repo_root: Path, run_path: Path, test_save: str) -> dict:
    exe_stat = install.exe.stat()
    return {
        "game_build": read_build_id(install.appmanifest),
        "game_exe": {
            "size": exe_stat.st_size,
            "modified": datetime.fromtimestamp(exe_stat.st_mtime, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        "test_save": test_save,
        "test_save_sha256": sha256_of_file(install.save_file(test_save)) if test_save else None,  # "" is a fresh start
        "python": platform.python_version(),
        "run_dir": str(run_path.resolve()),
        "harness_git": git_state(repo_root),
    }
