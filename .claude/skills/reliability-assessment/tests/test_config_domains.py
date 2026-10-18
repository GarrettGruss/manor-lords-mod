import unittest

from support import TempRepo, config

from reliabilitylib.config import ConfigError, check_config
from reliabilitylib.domains import DomainMap


class ConfigTests(unittest.TestCase):
    def test_missing_key_names_the_key(self):
        broken = config()
        del broken["cfr"]["window_days"]
        with self.assertRaisesRegex(ConfigError, "cfr.window_days"):
            check_config(broken)

    def test_wrong_type_names_the_key(self):
        with self.assertRaisesRegex(ConfigError, "low_sample_n"):
            check_config(config(low_sample_n="3"))

    def test_runs_section_is_optional(self):
        no_runs = config()
        del no_runs["runs"]
        check_config(no_runs)

    def test_runs_keys_are_required_when_runs_exists(self):
        broken = config()
        del broken["runs"]["fields"]["commit"]
        with self.assertRaisesRegex(ConfigError, "runs.fields.commit"):
            check_config(broken)


class DomainMapTests(unittest.TestCase):
    def setUp(self):
        self.repo = TempRepo()

    def tearDown(self):
        self.repo.cleanup()

    def test_capture_fills_the_domain(self):
        domains = DomainMap(config(), self.repo.root)
        self.assertEqual(domains.domain_of("features/tribute/rules.lua"), "mod/tribute")

    def test_first_match_wins(self):
        cfg = config(domains=[{"glob": "core/special.py", "domain": "special"}, {"glob": "core/**", "domain": "core"}])
        domains = DomainMap(cfg, self.repo.root)
        self.assertEqual(domains.domain_of("core/special.py"), "special")
        self.assertEqual(domains.domain_of("core/other.py"), "core")

    def test_unknown_path_is_unmapped(self):
        self.assertEqual(DomainMap(config(), self.repo.root).domain_of("elsewhere/x.py"), "unmapped")

    def test_ignored_path_has_no_domain(self):
        self.assertIsNone(DomainMap(config(), self.repo.root).domain_of("docs/page.md"))

    def test_double_star_slash_matches_zero_folders(self):
        cfg = config(domains=[{"glob": "core/**/x.py", "domain": "core"}])
        self.assertEqual(DomainMap(cfg, self.repo.root).domain_of("core/x.py"), "core")

    def test_missing_capability_stops_with_the_pattern(self):
        self.repo.write("specs/core/spec.md", "x")
        cfg = config(capabilities_dir="specs", domains=[{"glob": "a/**", "domain": "does-not-exist"}])
        with self.assertRaisesRegex(ConfigError, "a/\\*\\*.*does-not-exist"):
            DomainMap(cfg, self.repo.root)

    def test_require_capability_falls_through_to_the_next_rule(self):
        self.repo.write("specs/mod/a/spec.md", "x")
        self.repo.write("specs/kit/spec.md", "x")
        cfg = config(capabilities_dir="specs", domains=[
            {"glob": "tests/test_{name}.py", "domain": "mod/{name}", "require_capability": True},
            {"glob": "tests/**", "domain": "kit"},
        ])
        domains = DomainMap(cfg, self.repo.root)
        self.assertEqual(domains.domain_of("tests/test_a.py"), "mod/a")
        self.assertEqual(domains.domain_of("tests/test_harnessx.py"), "kit")
        self.assertEqual(domains.unknown, {})

    def test_captured_domain_without_folder_is_flagged(self):
        self.repo.write("specs/core/spec.md", "x")
        domains = DomainMap(config(capabilities_dir="specs"), self.repo.root)
        self.assertEqual(domains.domain_of("features/gone/x.lua"), "mod/gone")
        self.assertIn("mod/gone", domains.unknown)


if __name__ == "__main__":
    unittest.main()
