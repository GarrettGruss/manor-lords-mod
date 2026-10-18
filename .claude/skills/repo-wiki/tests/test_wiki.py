"""Unit tests for the repo-wiki skill script scripts/wiki.py (spec 34). Each test builds a small git repo in a temp folder."""

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
import wiki  # noqa: E402

GENERATED = "generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-18T15:00:00Z }\n"


def page_text(title="Run launcher", sources=("repo://harness/run.py",), body="# Run launcher\n\nText.\n",
              extra="", generated=GENERATED):
    source_lines = "".join(f"  - resource: {s}\n" for s in sources)
    return (f"---\ntype: Workflow\ntitle: {title}\ndescription: How one run is made.\n"
            f"tags: [harness, runs]\n{generated}{extra}sources:\n{source_lines}---\n\n{body}")


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

    def errors(self):
        wiki.write_indexes(self.root)
        return "\n".join(wiki.check_wiki(self.root))


class FrontMatterTests(unittest.TestCase):
    def test_parses_okf_front_matter(self):
        text, body = wiki.split_front_matter(page_text(extra="resource: x\nowner: {team: core}\n"), "p.md")
        meta = wiki.parse_front_matter(text, "p.md")
        self.assertEqual(meta["title"], "Run launcher")
        self.assertEqual(meta["tags"], ["harness", "runs"])
        self.assertEqual(wiki.repo_paths(meta), ["harness/run.py"])
        self.assertEqual(meta["generated"]["by"], "claude-code/claude-sonnet-5-5")
        self.assertEqual(meta["owner"], {"team": "core"})
        self.assertTrue(body.strip().startswith("# Run launcher"))

    def test_rejects_invalid_yaml(self):
        with self.assertRaisesRegex(wiki.WikiError, "not valid YAML"):
            wiki.parse_front_matter("title: [a\n", "p.md")

    def test_rejects_page_without_front_matter(self):
        with self.assertRaisesRegex(wiki.WikiError, "must start with"):
            wiki.split_front_matter("# Title\n", "p.md")

    def test_heading_slug_matches_github(self):
        self.assertEqual(wiki.heading_slug("Run `run.py` (one run)"), "run-runpy-one-run")
        self.assertEqual(wiki.heading_slug("A/B tests"), "ab-tests")

    def test_datetime_needs_an_offset(self):
        self.assertTrue(wiki.is_datetime_with_offset("2026-10-18T15:00:00Z"))
        self.assertTrue(wiki.is_datetime_with_offset("2026-10-18T15:00:00+02:00"))
        self.assertFalse(wiki.is_datetime_with_offset("2026-10-18T15:00:00"))
        self.assertFalse(wiki.is_datetime_with_offset("2026-10-18"))


class IndexAndCheckTests(RepoCase):
    def test_index_writes_okf_root_and_folder_indexes(self):
        written = wiki.write_indexes(self.root)
        self.assertEqual(written, ["docs/wiki/index.md", "docs/wiki/workflows/index.md"])
        root_index = (self.root / "docs/wiki/index.md").read_text(encoding="utf-8")
        self.assertTrue(root_index.startswith('---\nokf_version: "0.2"\n---\n\n# Pages\n'))
        self.assertIn("* [Quickstart](quickstart.md) - How one run is made.", root_index)
        self.assertIn("* [workflows](workflows/) - Pages: Run launcher.", root_index)
        folder_index = (self.root / "docs/wiki/workflows/index.md").read_text(encoding="utf-8")
        self.assertTrue(folder_index.startswith("# Pages\n"))
        self.assertIn("* [Run launcher](runs.md)", folder_index)

    def test_check_passes_on_valid_wiki(self):
        self.assertEqual(self.errors(), "")

    def test_check_reports_missing_and_edited_indexes(self):
        self.assertIn("index.md: missing", "\n".join(wiki.check_wiki(self.root)))
        wiki.write_indexes(self.root)
        self.write("docs/wiki/index.md", "# hand made\n")
        self.assertIn("edited by hand", "\n".join(wiki.check_wiki(self.root)))

    def test_check_reports_bad_sources_and_links(self):
        body = ("# Runs\n\n[gone](../missing.md) [abs](/docs/x.md) [anchor](../quickstart.md#nope)\n"
                "`[code](skipped.md)`\n\n```\n[fenced](skipped.md)\n```\n[ok](https://example.com)\n")
        sources = ("repo://harness/gone.py", "repo://harness/runlib", "harness/run.py", "https://example.com/spec")
        self.write("docs/wiki/workflows/runs.md", page_text(sources=sources, body=body))
        errors = self.errors()
        self.assertIn("source file 'repo://harness/gone.py' does not exist", errors)
        self.assertIn("source file 'repo://harness/runlib' does not exist (end a folder with '/')", errors)
        self.assertIn("source 'harness/run.py' must start with repo://", errors)
        self.assertNotIn("example.com/spec", errors)
        self.assertIn("'../missing.md' points to a missing file", errors)
        self.assertIn("'/docs/x.md' is root-absolute", errors)
        self.assertIn("no heading '#nope'", errors)
        self.assertNotIn("skipped.md", errors)

    def test_check_reports_plain_string_sources(self):
        text = page_text().replace("  - resource: repo://harness/run.py", "  - harness/run.py")
        self.write("docs/wiki/workflows/runs.md", text)
        self.assertIn("sources entry 1 must be a mapping with a 'resource' text", self.errors())

    def test_check_reports_missing_required_keys(self):
        self.write("docs/wiki/workflows/runs.md", "---\ntype: Workflow\n---\n# Runs\n")
        errors = self.errors()
        self.assertIn("'title' must be a non-empty text", errors)
        self.assertIn("'tags' must be a non-empty list of texts", errors)
        self.assertIn("'sources' must be a non-empty list", errors)
        self.assertIn("'generated' must be a mapping", errors)

    def test_check_reports_bad_trust_fields(self):
        generated = "generated: { by: claude, at: 2026-10-18T15:00:00 }\n"
        extra = "verified: { by: human:garrett, at: 2026-10-18 }\nstatus: old\nstale_after: soon\n"
        self.write("docs/wiki/workflows/runs.md", page_text(generated=generated, extra=extra))
        errors = self.errors()
        self.assertIn("'generated.by' must be an actor", errors)
        self.assertIn("'generated.at' must be an ISO 8601 datetime", errors)
        self.assertIn("'verified.at' must be an ISO 8601 datetime", errors)
        self.assertIn("'status' must be one of draft, stable, deprecated", errors)
        self.assertIn("'stale_after' must be an ISO 8601 datetime", errors)

    def test_check_accepts_verified_list_and_bare_mapping(self):
        extra = ("verified:\n  - { by: human:garrett, at: 2026-10-18T16:00:00Z }\n"
                 "  - { by: process:nightly, at: 2026-10-18T17:00:00Z }\nstatus: draft\n")
        self.write("docs/wiki/workflows/runs.md", page_text(extra=extra))
        self.assertEqual(self.errors(), "")
        self.write("docs/wiki/workflows/runs.md", page_text(extra="verified: { by: human:garrett, at: 2026-10-18T16:00:00Z }\n"))
        self.assertEqual(self.errors(), "")

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


class LogTests(RepoCase):
    def test_log_is_reserved_and_not_indexed(self):
        self.write("docs/wiki/log.md", "# Wiki log\n\n## 2026-10-19\n* **Update**: x.\n\n## 2026-10-18\n* **Initialization**: y.\n")
        self.assertEqual(self.errors(), "")
        self.assertNotIn("log.md", (self.root / "docs/wiki/index.md").read_text(encoding="utf-8"))
        self.assertEqual(len(wiki.page_paths(self.root / "docs/wiki")), 2)

    def test_log_dates_must_be_iso_and_newest_first(self):
        self.write("docs/wiki/log.md", "# Wiki log\n\n## 2026-10-18\n* a\n\n## 2026-10-19\n* b\n\n## Oct 1\n* c\n")
        errors = self.errors()
        self.assertIn("date heading must be '## YYYY-MM-DD'", errors)
        self.assertIn("newest first", errors)

    def test_log_has_no_front_matter(self):
        self.write("docs/wiki/log.md", "---\ntype: Log\n---\n# Wiki log\n")
        self.assertIn("a log file has no front matter", self.errors())


class StaleTests(RepoCase):
    def test_stamp_then_stale_reports_nothing(self):
        record = wiki.stamp(self.root, "init")
        self.assertEqual(record["gitHead"], self.git("rev-parse", "HEAD"))
        self.assertEqual(record["pages"], 2)
        report = wiki.stale_report(self.root)
        self.assertEqual(report["stale"], {})
        self.assertEqual(report["uncovered"], [])

    def test_stale_lists_pages_for_committed_and_uncommitted_changes(self):
        self.write("docs/wiki/workflows/runs.md", page_text(sources=("repo://harness/runlib/",)))
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
        self.assertEqual(report["stale"]["docs/wiki/workflows/runs.md"]["missing_sources"], ["repo://harness/run.py"])

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
