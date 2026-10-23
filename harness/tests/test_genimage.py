"""Fake tests for genimage.py. No network, no key."""
import base64
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import genimage  # noqa: E402

PNG = b"\x89PNG\r\n\x1a\n" + b"png body"
JPEG = b"\xff\xd8\xff" + b"jpeg body"
WEBP = b"RIFF\x00\x00\x00\x00WEBP" + b"webp body"
ANSWER_IMAGE = b"generated"


class GenimageTest(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.calls = []
        self.saved = (genimage.call_api, genimage.LOG_FILE)
        genimage.LOG_FILE = self.dir / "log.jsonl"
        genimage.call_api = self.fake_call

    def tearDown(self):
        genimage.call_api, genimage.LOG_FILE = self.saved

    def fake_call(self, method, path, body=None):
        self.calls.append((method, path, body))
        data = base64.b64encode(ANSWER_IMAGE).decode("ascii")
        return {"candidates": [{"content": {"parts": [{"inlineData": {"mimeType": "image/png", "data": data}}]}}]}

    def file(self, name, data):
        path = self.dir / name
        path.write_bytes(data)
        return path

    def test_references_come_before_the_prompt_in_order(self):
        refs = [self.file("a.png", PNG), self.file("b.jpg", JPEG), self.file("c.webp", WEBP)]
        genimage.generate("gemini-x", "a banner", self.dir / "out.png", 1, refs)
        parts = self.calls[0][2]["contents"][0]["parts"]
        self.assertEqual([p.get("inlineData", {}).get("mimeType") for p in parts[:3]],
                         ["image/png", "image/jpeg", "image/webp"])
        self.assertEqual(base64.b64decode(parts[1]["inlineData"]["data"]), JPEG)
        self.assertEqual(parts[3], {"text": "a banner"})

    def test_no_reference_sends_only_the_prompt(self):
        genimage.generate("gemini-x", "a banner", self.dir / "out.png", 1)
        self.assertEqual(self.calls[0][2]["contents"][0]["parts"], [{"text": "a banner"}])

    def test_too_many_references_make_no_call(self):
        refs = [self.file(f"{i}.png", PNG) for i in range(4)]
        with self.assertRaisesRegex(SystemExit, "0..3"):
            genimage.generate("gemini-x", "p", self.dir / "out.png", 1, refs)
        self.assertEqual(self.calls, [])

    def test_bad_reference_files_make_no_call(self):
        cases = [
            (self.dir / "missing.png", "not found"),
            (self.file("text.png", b"plain text"), "not PNG, JPEG or WebP"),
            (self.file("big.png", PNG + b"x" * genimage.MAX_REFERENCE_BYTES), "too large"),
        ]
        for path, message in cases:
            with self.subTest(path=path.name):
                with self.assertRaisesRegex(SystemExit, message) as raised:
                    genimage.generate("gemini-x", "p", self.dir / "out.png", 1, [path])
                self.assertIn(path.name, str(raised.exception))
        self.assertEqual(self.calls, [])

    def test_imagen_refuses_references(self):
        with self.assertRaisesRegex(SystemExit, "Only Gemini"):
            genimage.generate("imagen-4", "p", self.dir / "out.png", 1, [self.file("a.png", PNG)])
        self.assertEqual(self.calls, [])

    def test_count_out_of_range(self):
        for count in (0, 5):
            with self.subTest(count=count):
                with self.assertRaisesRegex(SystemExit, "1..4"):
                    genimage.generate("gemini-x", "p", self.dir / "out.png", count)
        self.assertEqual(self.calls, [])

    def test_call_is_logged_with_reference_hashes(self):
        ref = self.file("a.png", PNG)
        written = genimage.generate("gemini-x", "a banner", self.dir / "out.png", 1, [ref])
        entry = json.loads(genimage.LOG_FILE.read_text(encoding="utf-8").splitlines()[-1])
        self.assertEqual(entry["model"], "gemini-x")
        self.assertEqual(entry["prompt"], "a banner")
        self.assertEqual(entry["outputs"], [str(written[0])])
        self.assertEqual(entry["bytes"], [len(ANSWER_IMAGE)])
        self.assertEqual(entry["references"], [{"path": str(ref), "sha256": hashlib.sha256(PNG).hexdigest()}])


if __name__ == "__main__":
    unittest.main()
