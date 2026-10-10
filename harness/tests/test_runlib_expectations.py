import json
import unittest

import runlib_path  # noqa: F401
from runlib.expectations import Expectations


class JsonSafeRecordTest(unittest.TestCase):
    def test_a_set_value_is_stored_as_a_sorted_list(self):
        expect = Expectations()
        self.assertTrue(expect.equals("both factions raid", {"norse", "cuman"}, {"cuman", "norse"}))
        self.assertEqual(expect.records[0]["value"], ["cuman", "norse"])
        json.dumps(expect.records)  # must not raise

    def test_a_set_of_mixed_types_is_still_stored(self):
        expect = Expectations()
        expect.equals("mixed", {1, "a"}, {1, "a"})
        json.dumps(expect.records)

    def test_a_failed_set_check_keeps_the_value_for_the_report(self):
        expect = Expectations()
        self.assertFalse(expect.equals("years", {0, 1}, {0, 1, 2}))
        self.assertEqual(expect.records[0]["value"], [0, 1])
        self.assertFalse(expect.records[0]["ok"])


if __name__ == "__main__":
    unittest.main()
