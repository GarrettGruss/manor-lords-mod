"""Write the pak AES key from the key file into the gitignored `.env` at the root of the main checkout.

Usage: uv run python harness/tools/aes_env.py [--key-file <path>]

Why: pakmod.py reads `MANORLORDS_AES_KEY` from the environment, and falls back to this `.env` file,
so a shell does not need the variable. The key is never printed. `.env` must stay in .gitignore.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from releaselib import scan  # noqa: E402

ENV_NAME = "MANORLORDS_AES_KEY"
REPO_ROOT = Path(__file__).resolve().parents[2]


def main_checkout() -> Path:
    """A worktree shares the git directory of the main checkout, so the common dir names it."""
    result = subprocess.run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
                            cwd=REPO_ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        return REPO_ROOT
    return Path(result.stdout.strip()).parent


def env_file() -> Path:
    return main_checkout() / ".env"


def read_env_key(path: Path) -> str | None:
    """The key from a `.env` file, or None when the file or the line is missing."""
    if not path.is_file():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        name, sep, value = line.partition("=")
        if sep and name.strip() == ENV_NAME and value.strip():
            return value.strip()
    return None


def write_env_key(path: Path, key: str) -> None:
    """Replace the key line and keep the other lines. Write `.tmp`, then rename."""
    lines = []
    if path.is_file():
        lines = [line for line in path.read_text(encoding="utf-8").splitlines()
                 if line.partition("=")[0].strip() != ENV_NAME]
    lines.append(f"{ENV_NAME}={key}")
    temp = path.with_name(path.name + ".tmp")
    temp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.replace(temp, path)


def is_ignored(path: Path) -> bool:
    result = subprocess.run(["git", "check-ignore", "-q", str(path)], cwd=path.parent)
    return result.returncode == 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--key-file", type=Path, help="default: modtools/work/aes_key.txt of the main checkout")
    args = parser.parse_args(argv)
    key_file = args.key_file or main_checkout() / "modtools" / "work" / "aes_key.txt"
    target = env_file()
    if not is_ignored(target):
        raise SystemExit(f"{target} is not ignored by git; add .env to .gitignore first")
    write_env_key(target, scan.read_key(key_file))
    print(f"wrote {ENV_NAME} to {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
