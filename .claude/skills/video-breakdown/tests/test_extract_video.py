"""Unit tests for the pure helpers in scripts/extract_video.py (spec: .claude/skills/video-breakdown/spec/). No network, no ffmpeg."""

import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
import extract_video as ev  # noqa: E402


class ParseSceneTimesTest(unittest.TestCase):
    def test_reads_pts_time_from_showinfo(self):
        log = "[Parsed_showinfo_1] n:0 pts:100 pts_time:2.002 duration\n... n:1 pts_time:5.5 x"
        self.assertEqual(ev.parse_scene_times(log), [2.002, 5.5])

    def test_empty_log_gives_no_cuts(self):
        self.assertEqual(ev.parse_scene_times("no cuts here"), [])


class BuildShotsTest(unittest.TestCase):
    def test_shots_cover_the_whole_video(self):
        shots = ev.build_shots([2.0, 5.5], 10.0)
        self.assertEqual([s["id"] for s in shots], ["S01", "S02", "S03"])
        self.assertEqual([s["start"] for s in shots], [0.0, 2.0, 5.5])
        self.assertAlmostEqual(sum(s["length"] for s in shots), 10.0)
        self.assertEqual(shots[1]["mid"], 3.75)

    def test_merges_cuts_closer_than_min_length(self):
        shots = ev.build_shots([2.0, 2.1, 5.0], 10.0, min_length=0.2)
        self.assertEqual([s["start"] for s in shots], [0.0, 2.0, 5.0])

    def test_ignores_cuts_at_the_edges_and_unsorted_input(self):
        shots = ev.build_shots([9.95, 4.0, 0.05], 10.0)
        self.assertEqual([s["start"] for s in shots], [0.0, 4.0])

    def test_no_cuts_gives_one_shot(self):
        self.assertEqual(ev.build_shots([], 3.0), [{"id": "S01", "start": 0.0, "length": 3.0, "mid": 1.5}])


class ParseSrtTest(unittest.TestCase):
    SRT = ("1\n00:00:01,000 --> 00:00:02,500\nHello <c>there</c>\n\n"
           "2\n00:00:02,500 --> 00:00:03,000\nHello there\n\n"
           "3\n00:01:00.250 --> 00:01:02.000 align:start\nsecond\nline\n")

    def test_parses_times_strips_tags_and_drops_repeats(self):
        segments = ev.parse_srt(self.SRT)
        self.assertEqual([s["text"] for s in segments], ["Hello there", "second line"])
        self.assertEqual(segments[0]["start"], 1.0)
        self.assertEqual(segments[1]["start"], 60.25)
        self.assertEqual(segments[1]["end"], 62.0)


class FormatTest(unittest.TestCase):
    def test_transcript_lines(self):
        text = ev.format_transcript([{"start": 1.0, "end": 2.25, "text": "Hi"}])
        self.assertEqual(text, "[   1.0-   2.2] Hi\n")

    def test_shot_list_has_one_row_per_shot(self):
        table = ev.shot_list_markdown(ev.build_shots([2.0], 4.0))
        self.assertEqual(len(table.strip().splitlines()), 4)
        self.assertIn("| S02 | 2.0 | 2.0 |", table)


if __name__ == "__main__":
    unittest.main()
