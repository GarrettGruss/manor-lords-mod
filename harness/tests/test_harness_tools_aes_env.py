"""Tests for harness/tools/aes_env.py: the `.env` key file is read and rewritten without losing other lines."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools import aes_env  # noqa: E402

FAKE_KEY = "0x" + "12" * 32


class AesEnvTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.env = self.tmp / ".env"

    def test_missing_file_has_no_key(self):
        self.assertIsNone(aes_env.read_env_key(self.env))

    def test_written_key_is_read_back(self):
        aes_env.write_env_key(self.env, FAKE_KEY)
        self.assertEqual(aes_env.read_env_key(self.env), FAKE_KEY)

    def test_rewrite_keeps_other_lines_and_one_key_line(self):
        self.env.write_text(f"OTHER=1\n{aes_env.ENV_NAME}=old\n", encoding="utf-8")
        aes_env.write_env_key(self.env, FAKE_KEY)
        lines = self.env.read_text(encoding="utf-8").splitlines()
        self.assertIn("OTHER=1", lines)
        self.assertEqual([line for line in lines if line.startswith(aes_env.ENV_NAME)], [f"{aes_env.ENV_NAME}={FAKE_KEY}"])
        self.assertFalse((self.tmp / ".env.tmp").exists())


if __name__ == "__main__":
    unittest.main()
