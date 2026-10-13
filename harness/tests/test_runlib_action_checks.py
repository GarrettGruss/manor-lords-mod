"""Unit tests for the small check helpers in runlib.actions (no game)."""

import unittest

import runlib_path  # noqa: F401
from runlib.actions import (
    MAX_BUILDING_TYPE,
    MAX_GOOD_ID,
    MAX_MANOR_AMOUNT,
    MAX_WORKER_SLOTS,
    ActionError,
    check_banner_text,
    check_building_type,
    check_manor_goods,
    check_worker_slot,
    dead_count_delta,
)


class CheckManorGoodsTest(unittest.TestCase):
    def test_accepts_the_limits(self):
        check_manor_goods(0, 1)
        check_manor_goods(MAX_GOOD_ID, MAX_MANOR_AMOUNT)

    def test_rejects_bad_values(self):
        for good, amount in [(-1, 1), (MAX_GOOD_ID + 1, 1), (True, 1), ("5", 1),
                             (1, 0), (1, MAX_MANOR_AMOUNT + 1), (1, True), (1, 2.5)]:
            with self.subTest(good=good, amount=amount):
                with self.assertRaises(ActionError):
                    check_manor_goods(good, amount)


class CheckWorkerSlotTest(unittest.TestCase):
    def test_accepts_storage_jobs(self):
        check_worker_slot(44, 1)
        check_worker_slot(45, MAX_WORKER_SLOTS)

    def test_rejects_other_jobs_and_bad_slots(self):
        for job, slots in [(43, 1), (True, 1), (44, 0), (44, MAX_WORKER_SLOTS + 1), (44, True)]:
            with self.subTest(job=job, slots=slots):
                with self.assertRaises(ActionError):
                    check_worker_slot(job, slots)


class CheckBuildingTypeTest(unittest.TestCase):
    def test_returns_the_type(self):
        self.assertEqual(check_building_type(0), 0)
        self.assertEqual(check_building_type(MAX_BUILDING_TYPE), MAX_BUILDING_TYPE)

    def test_rejects_bad_types(self):
        for value in (-1, MAX_BUILDING_TYPE + 1, True, "3", None):
            with self.subTest(value=value):
                with self.assertRaises(ActionError):
                    check_building_type(value)


class CheckBannerTextTest(unittest.TestCase):
    def test_accepts_allowed_text(self):
        check_banner_text("title", "Raid, day 3: go!", 40, True)

    def test_empty_optional_text_is_allowed(self):
        check_banner_text("body", "", 40, False)

    def test_empty_required_text_fails(self):
        with self.assertRaisesRegex(ActionError, "title is required"):
            check_banner_text("title", "", 40, True)

    def test_too_long_text_fails(self):
        with self.assertRaisesRegex(ActionError, "longer than 5"):
            check_banner_text("title", "abcdef", 5, True)

    def test_forbidden_characters_fail(self):
        with self.assertRaisesRegex(ActionError, "may use only"):
            check_banner_text("title", "no <tags>", 40, True)


class DeadCountDeltaTest(unittest.TestCase):
    def test_counts_new_dead(self):
        answer = {"before": {"dead": 2}, "after": {"dead": 5}}
        self.assertEqual(dead_count_delta(answer), 3)

    def test_missing_field_fails_loudly(self):
        with self.assertRaises(KeyError):
            dead_count_delta({"before": {"dead": 2}})


if __name__ == "__main__":
    unittest.main()
