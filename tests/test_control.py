from datetime import datetime
import unittest
from zoneinfo import ZoneInfo

from two_bar.control import DEFAULT_CONFIG, evaluate


class ScheduleTests(unittest.TestCase):
    def at(self, stamp, state=None, action="status", zone="Europe/Zurich"):
        now = datetime.fromisoformat(stamp).replace(tzinfo=ZoneInfo(zone))
        return evaluate(now, DEFAULT_CONFIG, state or {}, action)

    def test_boundaries(self):
        for stamp, expected in [("2026-09-07T07:59:59", False),
                                ("2026-09-07T08:00:00", True),
                                ("2026-09-07T17:59:59", True),
                                ("2026-09-07T18:00:00", False),
                                ("2026-09-12T10:00:00", False),
                                ("2026-09-13T10:00:00", False)]:
            with self.subTest(stamp=stamp):
                self.assertEqual(self.at(stamp)[0]["visible"], expected)

    def test_hide_survives_poll_and_restart_until_boundary(self):
        _, state = self.at("2026-09-07T10:00", action="hide")
        result, kept = self.at("2026-09-07T11:00", state)
        self.assertFalse(result["visible"])
        self.assertEqual(kept, state)
        result, expired = self.at("2026-09-07T18:00", state)
        self.assertEqual(result["mode"], "automatic")
        self.assertEqual(expired, {})
        self.assertTrue(self.at("2026-09-08T09:00", state)[0]["visible"])

    def test_weekend_show_and_follow_schedule(self):
        result, state = self.at("2026-09-12T10:00", action="show")
        self.assertEqual(result["override_until"], "2026-09-14T08:00:00+02:00")
        self.assertTrue(self.at("2026-09-13T20:00", state)[0]["visible"])
        self.assertFalse(self.at("2026-09-13T20:00", state, "follow-schedule")[0]["visible"])
        self.assertEqual(self.at("2026-09-14T08:00", state)[0]["mode"], "automatic")

    def test_toggle_and_idempotent_show(self):
        _, state = self.at("2026-09-07T19:00", action="show")
        self.assertEqual(self.at("2026-09-07T20:00", state, "show")[1], state)
        result, _ = self.at("2026-09-07T20:00", state, "toggle")
        self.assertFalse(result["visible"])

    def test_dst_uses_calendar_boundaries(self):
        for friday, monday in [("2026-03-27T19:00", "2026-03-30T08:00:00+02:00"),
                               ("2026-10-23T19:00", "2026-10-26T08:00:00+01:00")]:
            self.assertEqual(self.at(friday)[0]["next_boundary"], monday)

    def test_clock_rewind_and_timezone_change_clear_override(self):
        _, state = self.at("2026-09-07T10:00", action="hide")
        self.assertEqual(self.at("2026-09-07T09:00", state)[0]["mode"], "automatic")
        self.assertEqual(self.at("2026-09-07T11:00", state, zone="UTC")[0]["mode"], "automatic")

    def test_schedule_change_clears_override(self):
        _, state = self.at("2026-09-07T10:00", action="hide")
        now = datetime(2026, 9, 7, 11, tzinfo=ZoneInfo("Europe/Zurich"))
        result, _ = evaluate(now, DEFAULT_CONFIG | {"end": "17:00"}, state)
        self.assertEqual(result["mode"], "automatic")

    def test_corrupt_override_fields_fall_back_to_schedule(self):
        result, state = self.at("2026-09-07T10:00", {"visible": False, "created": "broken", "expires": 9999999999})
        self.assertTrue(result["visible"])
        self.assertEqual(state, {})


if __name__ == "__main__":
    unittest.main()
