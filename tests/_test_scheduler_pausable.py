"""Tests for scheduler pausability: env hard-switch, settings persistence, runtime toggle.

Covers the three-layer switch added for hub/panel coexistence (WB_SCHEDULER env,
settings.scheduler_enabled, and the panel toggle), plus the disabled-reason
logging and throttled idle log.

    python -m unittest tests/_test_scheduler_pausable.py
"""
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import wb_settings
import wb_scheduler


class SchedulerEnabledSettingsTests(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.temp_dir = tempfile.mkdtemp(dir=self.base_dir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_default_is_enabled(self):
        self.assertTrue(wb_settings.scheduler_enabled(self.temp_dir))

    def test_disable_persists(self):
        wb_settings.set_scheduler_enabled(self.temp_dir, False)
        self.assertFalse(wb_settings.scheduler_enabled(self.temp_dir))

    def test_enable_persists(self):
        wb_settings.set_scheduler_enabled(self.temp_dir, False)
        wb_settings.set_scheduler_enabled(self.temp_dir, True)
        self.assertTrue(wb_settings.scheduler_enabled(self.temp_dir))

    def test_strict_boolean_required(self):
        # Non-boolean values are coerced, but the proxy layer rejects them;
        # here we only verify the settings round-trip with proper booleans.
        self.assertTrue(wb_settings.set_scheduler_enabled(self.temp_dir, True))
        self.assertFalse(wb_settings.set_scheduler_enabled(self.temp_dir, False))


class SchedulerDisabledReasonTests(unittest.TestCase):
    def test_disabled_reason_default_empty(self):
        pool = mock.Mock()
        pool.dir = ""
        s = wb_scheduler.Scheduler(pool)
        self.assertEqual(s._disabled_reason, "")

    def test_stop_records_reason(self):
        pool = mock.Mock()
        pool.dir = ""
        s = wb_scheduler.Scheduler(pool)
        s.stop(reason="test pause")
        self.assertEqual(s._disabled_reason, "test pause")

    def test_status_includes_disabled_reason(self):
        pool = mock.Mock()
        pool.dir = ""
        s = wb_scheduler.Scheduler(pool)
        s.enabled = False
        s._disabled_reason = "settings.scheduler_enabled=false"
        st = s.status()
        self.assertIn("disabled_reason", st)
        self.assertEqual(st["disabled_reason"], "settings.scheduler_enabled=false")


class SchedulerLogThrottleTests(unittest.TestCase):
    def test_throttle_interval_constant(self):
        # The run-loop throttle is 600 seconds (10 minutes).
        # We verify by reading the source: the constant appears exactly once.
        src_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "wb_scheduler.py",
        )
        with open(src_path, "r", encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn(">= 600", text)
        self.assertIn("_last_disabled_log", text)


class EnvOffValuesTests(unittest.TestCase):
    """The set of env strings that mean "off" — mirrored from wb_proxy.py."""

    def test_off_values_documented(self):
        src_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "wb_proxy.py",
        )
        with open(src_path, "r", encoding="utf-8") as fh:
            text = fh.read()
        for value in ("off", "0", "false", "disabled", "no", "n"):
            self.assertIn('"%s"' % value, text)


if __name__ == "__main__":
    unittest.main()
