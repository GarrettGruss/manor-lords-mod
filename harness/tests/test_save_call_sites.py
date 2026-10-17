"""Safety test (CLAUDE.md, Safety): only the Lua command save_game may call a game save function.

Every code file of the repo is scanned. Docs and notes (.md) may name the functions. This test file names them on purpose.
"""

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SAVE_CALLS = re.compile(r"requestSaveFile|SaveGameToSlot|SaveToDiskWithThumbnail|RequestMenuSave|Request Autosave")
CODE_SUFFIXES = {".lua", ".py", ".ps1", ".json", ".ini", ".cfg", ".toml", ".js"}
SKIP_DIRS = {".git", ".venv", ".claude", "runs", "node_modules", "__pycache__", "vendor", "modtools"}
ALLOWED = {
    "mod/shared/HarnessSave/HarnessSave.lua",  # the one guarded call
    "harness/tests/test_save_call_sites.py",   # this test
}
# Files that only name a function in a comment or as test data for "no save function is called" checks.
COMMENT_ONLY = {
    "mod/shared/HarnessAutosave/HarnessAutosave.lua",
    "harness/tests/test_fakegame_harnesssack.py",
    "harness/tests/test_fakegame_harnesssave.py",
}
# Observe-only hook files. They name the functions as hook paths and must never call one.
HOOK_ONLY: set[str] = set()
CALL_SYNTAX = re.compile(r"[:.](requestSaveFile|SaveGameToSlot|SaveDataToSlot|SaveToDiskWithThumbnail|RequestMenuSave|Request Autosave)\s*\(")


def code_files():
    for path in REPO.rglob("*"):
        relative = path.relative_to(REPO)
        if path.is_file() and path.suffix in CODE_SUFFIXES and not SKIP_DIRS & set(relative.parts):
            yield path, relative.as_posix()


def is_comment(line: str) -> bool:
    return line.lstrip().startswith(("--", "#"))


class SaveCallSiteTests(unittest.TestCase):
    def test_only_the_save_game_command_names_a_save_function(self):
        offenders = []
        for path, relative in code_files():
            if relative in ALLOWED or relative in COMMENT_ONLY or relative in HOOK_ONLY:
                continue
            for number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
                if SAVE_CALLS.search(line) and not is_comment(line):
                    offenders.append(f"{relative}:{number}: {line.strip()[:100]}")
        self.assertEqual(offenders, [], "a save function is named outside the allow-list")

    def test_files_that_may_only_name_a_save_function_in_a_comment_do_not_call_one(self):
        for relative in sorted(COMMENT_ONLY - {"harness/tests/test_fakegame_harnesssack.py", "harness/tests/test_fakegame_harnesssave.py"}):
            for line in (REPO / relative).read_text(encoding="utf-8").splitlines():
                if SAVE_CALLS.search(line):
                    self.assertTrue(is_comment(line), f"{relative}: {line}")

    def test_hook_only_files_do_not_call_a_save_function(self):
        for relative in sorted(HOOK_ONLY):
            text = (REPO / relative).read_text(encoding="utf-8")
            self.assertIsNone(CALL_SYNTAX.search(text), f"{relative} calls a save function")

    def test_the_allow_listed_lua_file_has_exactly_one_call(self):
        text = (REPO / "mod/shared/HarnessSave/HarnessSave.lua").read_text(encoding="utf-8")
        calls = [line for line in text.splitlines() if re.search(r":requestSaveFile\(", line) and not is_comment(line)]
        self.assertEqual(len(calls), 1)
        self.assertEqual(len(re.findall(r"SaveGameToSlot|SaveToDiskWithThumbnail|RequestMenuSave|Request Autosave", text)), 0)

    def test_the_command_is_registered_only_in_the_helper_mod(self):
        users = [relative for path, relative in code_files()
                 if relative.endswith(".lua") and 'require("HarnessSave")' in path.read_text(encoding="utf-8", errors="replace")]
        self.assertEqual(users, ["mod/HarnessActions/Scripts/main.lua"])


if __name__ == "__main__":
    unittest.main()
