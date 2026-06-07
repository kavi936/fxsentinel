#!/usr/bin/env python3
"""Snapshot-style tests for level_engine determinism."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from services.markets.level_engine import build_structured_levels
from services.markets.ohlc_store import save_bars


def _fake_daily():
    return [
        {"time": 1777708800, "open": 100000, "high": 101000, "low": 99000, "close": 100500, "volume": 1},
        {"time": 1777795200, "open": 100500, "high": 102000, "low": 100000, "close": 101500, "volume": 1},
        {"time": 1777881600, "open": 101500, "high": 103000, "low": 101000, "close": 102500, "volume": 1},
    ]


def _fake_h4():
    base = 1777881600
    return [
        {"time": base - 14400 * 3, "open": 101000, "high": 101800, "low": 100800, "close": 101200, "volume": 1},
        {"time": base - 14400 * 2, "open": 101200, "high": 102200, "low": 101000, "close": 102000, "volume": 1},
        {"time": base - 14400, "open": 102000, "high": 102800, "low": 101800, "close": 102400, "volume": 1},
        {"time": base, "open": 102400, "high": 103000, "low": 102100, "close": 102900, "volume": 1},
    ]


class LevelEngineTest(unittest.TestCase):
    def setUp(self):
        save_bars("BTCUSD", "D", _fake_daily(), source="test")
        save_bars("BTCUSD", "240", _fake_h4(), source="test")

    def test_builds_core_levels(self):
        levels = build_structured_levels("BTCUSD")
        kinds = {l["kind"] for l in levels}
        bases = {l["basis"] for l in levels}
        self.assertIn("level", kinds)
        self.assertIn("range", kinds)
        self.assertIn("prior_day_high", bases)
        self.assertIn("prior_day_low", bases)
        self.assertIn("session_value_zone_4h", bases)

    def test_deterministic_ids(self):
        a = build_structured_levels("BTCUSD")
        b = build_structured_levels("BTCUSD")
        self.assertEqual([x["level_id"] for x in a], [x["level_id"] for x in b])

    def test_pdh_value_from_prior_day(self):
        levels = build_structured_levels("BTCUSD")
        pdh = next(l for l in levels if l["basis"] == "prior_day_high")
        self.assertEqual(pdh["price"], 102000.0)


if __name__ == "__main__":
    unittest.main()
