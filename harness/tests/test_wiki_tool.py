"""Unit tests for harness/tools/wiki.py (spec 34). Each test builds a small git repo in a temp folder."""

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))
import wiki  # noqa: E402


def page_text(title="Run launcher", sources=("harness/run.py",), body="# Run launcher\n\nText.\n", extra=""):
    source_lines = "".join(f"  - {s}\n" for s in sources)
    return (f"---\ntype: Workflow\ntitle: {title}\ndescription: How one run is made.\n"
            f"tags: [harness, runs]\n{extra}sources:\n{source_lines}---\n\n{body}")


class RepoCase(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.git("init", "-q")
        self.git("config", "user.email", "test@example.com")
        self.git("config", "user.name", "Test")
        self.write("harness/run.py", "print('run')\n")
        self.write("harness/runlib/phases.py", "PHASES = []\n")
        self.write("docs/wiki/quickstart.md", page_text("Quickstart", body="# Quickstart\n\nSee [runs](workflows/runs.md#run-launcher).\n"))
        self.write("docs/wiki/workflows/runs.md", page_text())
        self.commit("base")

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.root), *args], check=True,
                              capture_output=True, text=True).stdout.strip()

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def commit(self, message):
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)
        return self.git("rev-parse", "HEAD")


class FrontMatterTests(unittest.TestCase):
    def test_parses_scalars_inline_lists_and_block_lists(self):
        lines, body = wiki.split_front_matter(page_text(extra='resource: "x"\n'), "p.md")
        meta = wiki.parse_front_matter(lines, "p.md")
        self.assertEqual(meta["title"], "Run launcher")
        self.assertEqual(meta["tags"], ["harness", "runs"])
        self.assertEqual(meta["sources"], ["harness/run.py"])
        self.assertEqual(meta["resource"], "x")
        self.assertTrue(body.strip().startswith("# Run launcher"))

    def test_rejects_unsupported_yaml(self):
        with self.assertRaisesRegex(wiki.WikiError, "unsupported front matter line"):
            wiki.parse_front_matter(["title: a", "  nested: b"], "p.md")

    def test_rejects_page_without_front_matter(self):
        with self.assertRaisesRegex(wiki.WikiError, "must start with"):
            wiki.split_front_matter("# Title\n", "p.md")

    def test_heading_slug_matches_github(self):
        self.assertEqual(wiki.heading_slug("Run `run.py` (one run)"), "run-runpy-one-run")
        self.assertEqual(wiki.heading_slug("A/B tests"), "ab-tests")


class IndexAndCheckTests(RepoCase):
    def test_index_writes_root_and_folder_indexes(self):
        written = wiki.write_indexes(self.root)
        self.assertEqual(written, ["docs/wiki/index.md", "docs/wiki/workflows/index.md"])
        root_index = (self.root / "docs/wiki/index.md").read_text(encoding="utf-8")
        self.assertTrue(root_index.startswith('---\nokf_version: "0.2"\n---\n'))
        self.assertIn("- [Quickstart](quickstart.md) - How one run is made.", root_index)
        self.assertIn("- [workflows](workflows/)", root_index)
        folder_index = (self.root / "docs/wiki/workflows/index.md").read_text(encoding="utf-8")
        self.assertIn("- [Run launcher](runs.md)", folder_index)

    def test_check_passes_on_valid_wiki(self):
        wiki.write_indexes(self.root)
        self.assertEqual(wiki.check_wiki(self.root), [])

    def test_check_reports_missing_and_edited_indexes(self):
        errors = wiki.check_wiki(self.root)
        self.assertTrue(any("index.md: missing" in e for e in errors))
        wiki.write_indexes(self.root)
        self.write("docs/wiki/index.md", "# hand made\n")
        self.assertTrue(any("edited by hand" in e for e in wiki.check_wiki(self.root)))

    def test_check_reports_missing_source_and_bad_links(self):
        body = ("# Runs\n\n[gone](../missing.md) [abs](/docs/x.md) [anchor](../quickstart.md#nope)\n"
                "`[code](skipped.md)`\n\n```\n[fenced](skipped.md)\n```\n[ok](https://example.com)\n")
        self.write("docs/wiki/workflows/runs.md", page_text(sources=("harness/gone.py", "harness/runlib"), body=body))
        wiki.write_indexes(self.root)
        errors = "\n".join(wiki.check_wiki(self.root))
        self.assertIn("source file 'harness/gone.py' does not exist", errors)
        self.assertIn("source file 'harness/runlib' does not exist (end a folder with '/')", errors)
        self.assertIn("'../missing.md' points to a missing file", errors)
        self.assertIn("'/docs/x.md' is root-absolute", errors)
        self.assertIn("no heading '#nope'", errors)
        self.assertNotIn("skipped.md", errors)

    def test_check_reports_missing_required_keys(self):
        self.write("docs/wiki/workflows/runs.md", "---\ntype: Workflow\n---\n# Runs\n")
        wiki.write_indexes(self.root)
        errors = "\n".join(wiki.check_wiki(self.root))
        self.assertIn("'title' must be a non-empty text", errors)
        self.assertIn("'sources' must be a non-empty list", errors)

    def test_check_skips_index_compare_when_a_page_does_not_parse(self):
        self.write("docs/wiki/workflows/runs.md", "no front matter\n")
        errors = "\n".join(wiki.check_wiki(self.root))
        self.assertIn("must start with", errors)
        self.assertNotIn("index.md", errors)

    def test_index_removes_index_of_empty_folder(self):
        wiki.write_indexes(self.root)
        (self.root / "docs/wiki/workflows/runs.md").unlink()
        wiki.write_indexes(self.root)
        self.assertFalse((self.root / "docs/wiki/workflows/index.md").exists())


class StaleTests(RepoCase):
    def test_stamp_then_stale_reports_nothing(self):
        record = wiki.stamp(self.root, "init")
        self.assertEqual(record["gitHead"], self.git("rev-parse", "HEAD"))
        self.assertEqual(record["pages"], 2)
        report = wiki.stale_report(self.root)
        self.assertEqual(report["stale"], {})
        self.assertEqual(report["uncovered"], [])

    def test_stale_lists_pages_for_committed_and_uncommitted_changes(self):
        self.write("docs/wiki/workflows/runs.md", page_text(sources=("harness/runlib/",)))
        wiki.stamp(self.root, "init")
        self.commit("wiki")
        self.write("harness/runlib/phases.py", "PHASES = [1]\n")
        self.commit("change phases")
        self.write("harness/run.py", "print('changed')\n")
        self.write("mod/New/main.lua", "-- new\n")
        report = wiki.stale_report(self.root)
        self.assertEqual(report["stale"]["docs/wiki/workflows/runs.md"]["changed"], ["harness/runlib/phases.py"])
        self.assertEqual(report["stale"]["docs/wiki/quickstart.md"]["changed"], ["harness/run.py"])
        self.assertEqual(report["uncovered"], ["mod/New/main.lua"])
        self.assertNotIn("docs/wiki/.last-update.json", report["changed"])

    def test_stale_reports_deleted_sources(self):
        wiki.stamp(self.root, "init")
        (self.root / "harness/run.py").unlink()
        report = wiki.stale_report(self.root)
        self.assertEqual(report["stale"]["docs/wiki/workflows/runs.md"]["missing_sources"], ["harness/run.py"])

    def test_stale_without_stamp_fails_loudly(self):
        with self.assertRaisesRegex(wiki.WikiError, "last-update.json is missing"):
            wiki.stale_report(self.root)

    def test_cli_check_exit_codes(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(wiki.main(["--repo", str(self.root), "check"]), 1)
            self.assertEqual(wiki.main(["--repo", str(self.root), "index"]), 0)
            self.assertEqual(wiki.main(["--repo", str(self.root), "check"]), 0)
            self.assertEqual(wiki.main(["--repo", str(self.root), "stamp", "--command", "init"]), 0)
        self.assertIn("wiki check: ok", out.getvalue())
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(wiki.main(["--repo", str(self.root), "stale"]), 0)
        self.assertEqual(json.loads(out.getvalue())["stale"], {})


if __name__ == "__main__":
    unittest.main()
