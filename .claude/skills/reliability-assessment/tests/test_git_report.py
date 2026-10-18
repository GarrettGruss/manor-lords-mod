import unittest

from support import TempRepo, config

from reliability import build_git_report


class GitReportTests(unittest.TestCase):
    def setUp(self):
        self.repo = TempRepo()

    def tearDown(self):
        self.repo.cleanup()

    def report(self, cfg=None):
        return build_git_report(self.repo.root, "HEAD", cfg or config())

    def test_counts_ratio_and_cfr_inside_the_window(self):
        self.repo.commit("feat(a): one", {"features/a/x.lua": "1\n"}, day=0)
        self.repo.commit("feat(a): two", {"features/a/x.lua": "1\n2\n"}, day=10)
        self.repo.commit("fix(a): repair", {"features/a/x.lua": "1\n3\n"}, day=15)
        self.repo.commit("feat(a): three", {"features/a/x.lua": "1\n3\n4\n"}, day=40)
        entry = self.report()["domains"]["mod/a"]
        self.assertEqual((entry["feat"], entry["fix"]), (3, 1))
        self.assertAlmostEqual(entry["fix_feat_ratio"]["value"], 0.333, places=2)
        # Only the second feat has the fix within 14 days.
        self.assertAlmostEqual(entry["cfr"]["value"], 0.333, places=2)

    def test_fix_outside_the_window(self):
        self.repo.commit("feat: one", {"core/x.py": "1\n"}, day=0)
        self.repo.commit("fix: late", {"core/x.py": "2\n"}, day=20)
        self.assertEqual(self.report()["domains"]["core"]["cfr"]["value"], 0)

    def test_fix_of_other_lines_does_not_fail_the_feat(self):
        self.repo.commit("feat: base", {"core/x.py": "a\n"}, day=0)
        self.repo.commit("feat: new file", {"core/y.py": "b\n"}, day=1)
        self.repo.commit("fix: old line", {"core/x.py": "c\n"}, day=2)
        entry = self.report()["domains"]["core"]
        # Only "base" wrote the line that the fix changed.
        self.assertEqual(entry["cfr"]["value"], 0.5)

    def test_window_comes_from_the_config(self):
        self.repo.commit("feat: one", {"core/x.py": "1\n"}, day=0)
        self.repo.commit("fix: late", {"core/x.py": "2\n"}, day=20)
        self.assertEqual(self.report(config(cfr={"window_days": 30}))["domains"]["core"]["cfr"]["value"], 1)

    def test_commit_in_two_domains_counts_in_each(self):
        self.repo.commit("feat: both", {"core/x.py": "1\n", "features/a/y.lua": "1\n"}, day=0)
        domains = self.report()["domains"]
        self.assertEqual(domains["core"]["feat"], 1)
        self.assertEqual(domains["mod/a"]["feat"], 1)

    def test_bug_lifetime_from_blame(self):
        self.repo.commit("feat: base", {"core/x.py": "a\nb\n"}, day=0)
        self.repo.commit("feat: bug", {"core/x.py": "a\nbad\n"}, day=1)
        self.repo.commit("fix: repair", {"core/x.py": "a\ngood\n"}, day=4)
        lifetime = self.report()["domains"]["core"]["bug_lifetime_days"]
        self.assertGreaterEqual(lifetime["value"], 2.9)
        self.assertLessEqual(lifetime["value"], 3.1)
        self.assertEqual(lifetime["n"], 1)
        self.assertTrue(lifetime["low_sample"])

    def test_removed_line_that_looks_like_a_header(self):
        self.repo.commit("feat: base", {"core/x.lua": "a\n-- old comment\nb\n"}, day=0)
        self.repo.commit("fix: drop comment", {"core/x.lua": "a\nb\n"}, day=2)
        self.assertEqual(self.report()["domains"]["core"]["bug_lifetime_days"]["n"], 1)

    def test_fix_that_only_adds_lines_has_no_origin(self):
        self.repo.commit("feat: base", {"core/x.py": "a\n"}, day=0)
        self.repo.commit("fix: add", {"core/x.py": "a\nb\n"}, day=2)
        entry = self.report()["domains"]["core"]
        self.assertEqual(entry["no_origin"], 1)
        self.assertEqual(entry["bug_lifetime_days"]["n"], 0)

    def test_ignored_paths_add_no_churn_and_unmapped_share_is_reported(self):
        self.repo.commit("docs: page", {"docs/a.md": "1\n2\n3\n"}, day=0)
        self.repo.commit("chore: misc", {"other/a.txt": "1\n", "core/x.py": "1\n2\n3\n"}, day=1)
        report = self.report()
        self.assertAlmostEqual(report["unmapped_churn_share"], 0.25)
        self.assertNotIn("docs", str(report["domains"].keys()))

    def test_merge_commits_are_skipped(self):
        self.repo.commit("feat: base", {"core/x.py": "1\n"}, day=0)
        self.repo.git("checkout", "-q", "-b", "side")
        self.repo.commit("feat: side", {"core/y.py": "1\n"}, day=1)
        self.repo.git("checkout", "-q", "-")
        self.repo.git("merge", "-q", "--no-ff", "-m", "feat: merge", "side")
        self.assertEqual(self.report()["domains"]["core"]["feat"], 2)


if __name__ == "__main__":
    unittest.main()
