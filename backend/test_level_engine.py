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
    bars = []
    for i in range(30):
        t = base - 14400 * (29 - i)
        bars.append(
            {
                "time": t,
                "open": 101000 + i * 10,
                "high": 101800 + i * 10,
                "low": 100800 + i * 10,
                "close": 101200 + i * 10,
                "volume": 10,
                "quote_volume": 1_000_000,
            }
        )
    bars[-1]["volume"] = 5000
    bars[-1]["quote_volume"] = 500_000_000
    bars[-1]["high"] = 102200
    bars[-1]["low"] = 101800
    return bars


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

    def test_volume_profile_levels_present(self):
        levels = build_structured_levels("BTCUSD")
        bases = {l["basis"] for l in levels}
        self.assertIn("volume_poc", bases)
        self.assertIn("value_area_4h_5d", bases)
        poc = next(l for l in levels if l["basis"] == "volume_poc")
        va = next(l for l in levels if l["basis"] == "value_area_4h_5d")
        self.assertEqual(poc["source"], "level_engine_v1")
        self.assertEqual(va["source"], "level_engine_v1")
        self.assertIn("feature_metrics", poc)
        self.assertLess(va["price_low"], va["price_high"])

    def test_volume_level_ids_stable(self):
        a = build_structured_levels("BTCUSD")
        b = build_structured_levels("BTCUSD")
        vol_ids_a = [l["level_id"] for l in a if l["basis"] in ("volume_poc", "value_area_4h_5d")]
        vol_ids_b = [l["level_id"] for l in b if l["basis"] in ("volume_poc", "value_area_4h_5d")]
        self.assertEqual(vol_ids_a, vol_ids_b)
        self.assertEqual(len(vol_ids_a), 2)


if __name__ == "__main__":
    unittest.main()
