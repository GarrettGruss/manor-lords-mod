"""Reads of files that the mod writes while Python reads them (Windows refuses a read at that moment)."""

import tempfile
import unittest
from pathlib import Path
from unittest import mock

import runlib_path  # noqa: F401  (puts harness/ on sys.path)
from runlib import game


class RefusedReadTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.temp = Path(temp.name)

    def test_boot_file_that_is_refused_counts_as_not_readable_yet(self):
        path = self.temp / "boot.json"
        path.write_text('{"state": "READY"}', encoding="utf-8")
        with mock.patch.object(Path, "read_text", side_effect=PermissionError("in use")):
            self.assertIsNone(game.read_boot_file(path))

    def test_pause_call_count_retries_after_a_refused_read(self):
        log = self.temp / "mod.log"
        log.write_text("1 1 INFO [HarnessBoot] game clock is moving; calling pauseGame (call 1)\n", encoding="utf-8")
        real_read = Path.read_text
        attempts = {"n": 0}

        def flaky(self_path, *args, **kwargs):
            attempts["n"] += 1
            if attempts["n"] < 3:
                raise PermissionError("in use")
            return real_read(self_path, *args, **kwargs)

        with mock.patch.object(Path, "read_text", flaky), mock.patch.object(game.time, "sleep"):
            self.assertEqual(game.count_pause_calls(log), 1)
        self.assertEqual(attempts["n"], 3)

    def test_pause_call_count_gives_up_with_the_error_when_it_stays_refused(self):
        log = self.temp / "mod.log"
        log.write_text("x\n", encoding="utf-8")
        with mock.patch.object(Path, "read_text", side_effect=PermissionError("in use")), \
                mock.patch.object(game.time, "sleep"):
            with self.assertRaises(PermissionError):
                game.count_pause_calls(log)


if __name__ == "__main__":
    unittest.main()
