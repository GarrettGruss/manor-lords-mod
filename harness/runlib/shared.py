"""State that all checkouts of the repo share: the main checkout and its git worktrees (spec 11).

Parallel sessions often run in git worktrees. They use one machine, one game folder and one user save folder,
so the game slots, the locks, the run counter and the fixture ledger must be the same files for all of them.
Run folders stay in each checkout.
"""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SHARED_ROOT_ENV = "HARNESS_SHARED_ROOT"  # for tests, and for a checkout that is not under git


def main_checkout(repo_root: Path) -> Path:
    """The main checkout of a git worktree, or repo_root itself.

    A worktree has a `.git` file with `gitdir: <main>/.git/worktrees/<name>`. Reading it needs no git process.
    """
    git_path = Path(repo_root) / ".git"
    if not git_path.is_file():
        return Path(repo_root)
    text = git_path.read_text(encoding="utf-8").strip()
    if not text.startswith("gitdir:"):
        raise RuntimeError(f"{git_path} is not a git worktree file: {text[:80]!r}")
    git_dir = Path(text.removeprefix("gitdir:").strip())
    if git_dir.parent.name != "worktrees" or git_dir.parent.parent.name != ".git":
        raise RuntimeError(f"{git_path} points to {git_dir}, which is not <main>/.git/worktrees/<name>.")
    return git_dir.parent.parent.parent


def shared_root() -> Path:
    override = os.environ.get(SHARED_ROOT_ENV, "").strip()
    return Path(override) if override else main_checkout(REPO_ROOT)


SHARED_ROOT = shared_root()
SHARED_RUNS = SHARED_ROOT / "runs"


def lock_root(runs_root: Path) -> Path:
    """Where the run locks, start claims and the run counter of `runs_root` live.

    The default runs folder of any checkout maps to the shared one. Another folder (tests, --runs-root) keeps its own.
    """
    if Path(runs_root).resolve() == (REPO_ROOT / "runs").resolve():
        return SHARED_RUNS
    return Path(runs_root)
