"""Tests for the checks in harness/release.py that need git (spec 19). Git calls are replaced."""

import subprocess
import unittest
from unittest import mock

import runlib_path  # noqa: F401
import release


def completed(stdout="", returncode=0, stderr=""):
    return subprocess.CompletedProcess([], returncode, stdout, stderr)


class TagCheckTests(unittest.TestCase):
    def test_a_free_tag_passes(self):
        with mock.patch.object(release, "_run", return_value=completed()):
            release.check_not_tagged("demo-v1.0.0", offline=False)

    def test_a_local_tag_fails(self):
        with mock.patch.object(release, "_run", return_value=completed("demo-v1.0.0\n")):
            with self.assertRaisesRegex(release.ReleaseError, "exists already"):
                release.check_not_tagged("demo-v1.0.0", offline=False)

    def test_a_remote_tag_fails(self):
        answers = [completed(), completed("abc\trefs/tags/demo-v1.0.0\n")]
        with mock.patch.object(release, "_run", side_effect=answers):
            with self.assertRaisesRegex(release.ReleaseError, "exists on origin"):
                release.check_not_tagged("demo-v1.0.0", offline=False)

    def test_an_unreachable_origin_fails_unless_offline(self):
        answers = lambda: [completed(), completed(returncode=128, stderr="no network")]
        with mock.patch.object(release, "_run", side_effect=answers()):
            with self.assertRaisesRegex(release.ReleaseError, "could not ask origin"):
                release.check_not_tagged("demo-v1.0.0", offline=False)
        with mock.patch.object(release, "_run", side_effect=answers()):
            release.check_not_tagged("demo-v1.0.0", offline=True)


class ArgumentTests(unittest.TestCase):
    def test_dry_run_and_publish_exclude_each_other(self):
        with self.assertRaises(SystemExit):
            release.parse_args(["--mod", "Demo", "--dry-run", "--publish"])

    def test_a_failed_check_gives_exit_code_1(self):
        with mock.patch.object(release, "release", side_effect=release.ReleaseError("broken")):
            self.assertEqual(release.main(["--mod", "Demo", "--dry-run"]), 1)

    def test_an_unknown_mod_fails_with_a_clear_message(self):
        with mock.patch("sys.stderr"):
            self.assertEqual(release.main(["--mod", "NoSuchMod", "--dry-run"]), 1)


if __name__ == "__main__":
    unittest.main()
