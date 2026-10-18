import json
import unittest

from support import TempRepo, config

from reliability import build_git_report, build_runs_report, write_assessment
from reliabilitylib import report


class RunsReportTests(unittest.TestCase):
    def setUp(self):
        self.repo = TempRepo()
        self.repo.write("features/a/tests/payout.py", 'NAME = "a-payout"\n')
        self.repo.write("features/b/tests/load_check.py", "# no NAME\n")

    def tearDown(self):
        self.repo.cleanup()

    def report(self, cfg=None):
        return build_runs_report(self.repo.root, cfg or config())

    def test_failure_and_repair_times(self):
        self.repo.run("r1", "a-payout", "pass", hour=0, commit="A0")
        self.repo.run("r2", "a-payout", "fail", hour=10, commit="A")
        self.repo.run("r3", "a-payout", "pass", hour=14, commit="B")
        entry = self.report()["domains"]["mod/a"]
        self.assertEqual((entry["failures"], entry["flaky"]), (1, 0))
        self.assertAlmostEqual(entry["mttf_hours"]["value"], 10, delta=0.1)
        self.assertAlmostEqual(entry["mttr_hours"]["value"], 4, delta=0.1)

    def test_flaky_failure_is_not_in_mttf_or_mttr(self):
        self.repo.run("r1", "a-payout", "pass", hour=0, commit="A")
        self.repo.run("r2", "a-payout", "fail", hour=1, commit="A")
        self.repo.run("r3", "a-payout", "pass", hour=2, commit="A")
        entry = self.report()["domains"]["mod/a"]
        self.assertEqual((entry["failures"], entry["flaky"]), (0, 1))
        self.assertIsNone(entry["mttr_hours"]["value"])

    def test_other_verdicts_are_counted_apart(self):
        self.repo.run("r1", "a-payout", "pass", hour=0)
        self.repo.run("r2", "a-payout", "harness_error", hour=1)
        entry = self.report()["domains"]["mod/a"]
        self.assertEqual((entry["runs"], entry["other"], entry["failures"]), (1, 1, 0))

    def test_broken_summary_is_skipped_and_listed(self):
        self.repo.run("r1", "a-payout", "pass", hour=0)
        self.repo.write("runs/r2/summary.json", "{ not json")
        result = self.report()
        self.assertEqual(len(result["skipped"]), 1)
        self.assertIn("r2", result["skipped"][0])
        self.assertEqual(result["domains"]["mod/a"]["runs"], 1)

    def test_test_name_from_file_stem(self):
        self.repo.run("r1", "load-check", "pass", hour=0)
        self.assertIn("mod/b", self.report()["domains"])

    def test_unknown_test_is_unmapped(self):
        self.repo.run("r1", "gone-test", "pass", hour=0)
        self.assertIn("unmapped", self.report()["domains"])

    def test_no_runs_section_gives_no_report(self):
        cfg = config()
        del cfg["runs"]
        self.assertIsNone(self.report(cfg))


class AssessTests(unittest.TestCase):
    def setUp(self):
        self.repo = TempRepo()

    def tearDown(self):
        self.repo.cleanup()

    def test_domain_over_the_cfr_limit_is_flagged(self):
        for i in range(5):
            self.repo.commit(f"feat: f{i}", {"core/x.py": f"{i}\n"}, day=i * 20)
            self.repo.commit(f"fix: r{i}", {"core/x.py": f"{i}b\n"}, day=i * 20 + 1)
        git = build_git_report(self.repo.root, "HEAD", config())
        flags = report.over_limits(git, None, config())
        self.assertTrue(any(flag.startswith("core: change failure rate") for flag in flags))

    def test_below_min_samples_is_not_flagged(self):
        self.repo.commit("feat: f", {"core/x.py": "1\n"}, day=0)
        self.repo.commit("fix: r", {"core/x.py": "2\n"}, day=1)
        git = build_git_report(self.repo.root, "HEAD", config())
        self.assertFalse(any(flag.startswith("core:") for flag in report.over_limits(git, None, config())))

    def test_assess_writes_markdown_and_json(self):
        self.repo.commit("feat: f", {"core/x.py": "1\n"}, day=0)
        cfg = config()
        git = build_git_report(self.repo.root, "HEAD", cfg)
        path = write_assessment(self.repo.root, cfg, "2026-10-18", git, build_runs_report(self.repo.root, cfg))
        self.assertTrue(path.read_text(encoding="utf-8").startswith("# Reliability assessment 2026-10-18"))
        data = json.loads((self.repo.root / "reports" / "2026-10-18.json").read_text(encoding="utf-8"))
        self.assertIn("over_limits", data)


class SecondLayoutTests(unittest.TestCase):
    """The script must work for another codebase with only a different config."""

    def test_other_layout_without_capabilities_or_runs(self):
        repo = TempRepo()
        try:
            repo.commit("bugfix: x", {"src/api/x.go": "1\n"}, day=0)
            repo.commit("feature: y", {"src/api/x.go": "2\n"}, day=1)
            cfg = config(domains=[{"glob": "src/{name}/**", "domain": "{name}"}],
                         commit_types={"pattern": r"^(?P<type>\w+):", "feat": ["feature"], "fix": ["bugfix"]})
            del cfg["runs"]
            entry = build_git_report(repo.root, "HEAD", cfg)["domains"]["api"]
            self.assertEqual((entry["feat"], entry["fix"]), (1, 1))
        finally:
            repo.cleanup()


if __name__ == "__main__":
    unittest.main()
