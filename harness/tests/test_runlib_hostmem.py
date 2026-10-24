import json
import tempfile
import unittest
from pathlib import Path

import runlib_path  # noqa: F401
from runlib import hostmem


class HostMemoryTest(unittest.TestCase):
    def test_sample_line_has_the_memory_fields(self):
        line = json.loads(hostmem.sample_line(None, now=100.0))
        self.assertEqual(line["t"], 100.0)
        self.assertGreater(line["free_mb"], 0)
        self.assertGreaterEqual(line["total_mb"], line["free_mb"])
        self.assertIsNone(line["game_rss_mb"])

    def test_sampler_writes_a_line_at_start(self):
        with tempfile.TemporaryDirectory() as folder:
            sampler = hostmem.HostMemorySampler(Path(folder), None, interval_s=0.05)
            sampler.start()
            sampler.stop()
            lines = (Path(folder) / hostmem.FILE_NAME).read_text(encoding="utf-8").splitlines()
            self.assertGreaterEqual(len(lines), 1)
            json.loads(lines[0])


if __name__ == "__main__":
    unittest.main()
