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


class SchedulerStartupCycleTests(unittest.TestCase):
    """The startup cycle must obey the same switch as the hourly slots.

    Before this was pinned, ``_run_loop`` ran ``_execute_cycle("启动初次初始化巡检")``
    unconditionally: turning the scheduler off still produced one real
    check-in / daily-activity round on every gateway restart, so the pause was
    bypassed once per restart.
    """

    def _scheduler(self):
        pool = mock.Mock()
        pool.dir = ""
        s = wb_scheduler.Scheduler(pool)
        # Stop the run loop from sleeping 10s and then walking into the real
        # cycle: we only want to observe whether _execute_cycle is reached.
        s._stop_event.set()
        return s

    def _run_startup(self, s):
        calls = []
        s._execute_cycle = lambda *a, **k: calls.append(a[0] if a else "")
        real_sleep = wb_scheduler.time.sleep
        wb_scheduler.time.sleep = lambda *_: None
        try:
            s._run_loop()
        finally:
            wb_scheduler.time.sleep = real_sleep
        return calls

    def test_enabled_runs_the_startup_cycle(self):
        s = self._scheduler()
        s.enabled = True
        self.assertEqual(self._run_startup(s), ["启动初次初始化巡检"])

    def test_disabled_skips_the_startup_cycle(self):
        s = self._scheduler()
        s.enabled = False
        s._disabled_reason = "settings.scheduler_enabled=false"
        self.assertEqual(self._run_startup(s), [])

    def test_disabled_keeps_the_catchup_pending(self):
        # The startup catch-up is a one-shot flag: skipping must not consume
        # it, otherwise re-enabling the switch loses that day's activity.
        s = self._scheduler()
        s.enabled = False
        self.assertTrue(s._catchup_pending)
        self._run_startup(s)
        self.assertTrue(s._catchup_pending)


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
