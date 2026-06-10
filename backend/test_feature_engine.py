#!/usr/bin/env python3
"""Snapshot-style tests for volume profile determinism."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from services.markets.feature_engine import compute_volume_profile


def _profile_bars_with_spike(spike_high: float = 102200.0):
    base = 1777881600
    bars = []
    for i in range(30):
        t = base - 14400 * (29 - i)
        bars.append(
            {
                "time": t,
                "open": 100000,
                "high": 100400,
                "low": 99600,
                "close": 100100,
                "volume": 5,
                "quote_volume": 500000,
            }
        )
    bars[-1] = {
        "time": base,
        "open": 101900,
        "high": spike_high,
        "low": 101800,
        "close": 102050,
        "volume": 5000,
        "quote_volume": 500_000_000,
    }
    return bars


class FeatureEngineTest(unittest.TestCase):
    def test_volume_profile_poc_near_spike(self):
        bars = _profile_bars_with_spike()
        profile = compute_volume_profile(bars)
        self.assertIsNotNone(profile)
        self.assertGreaterEqual(profile["poc"], 101800)
        self.assertLessEqual(profile["poc"], 102300)
        self.assertLess(profile["val"], profile["vah"])
        self.assertLessEqual(profile["val"], profile["poc"])
        self.assertGreaterEqual(profile["vah"], profile["poc"])

    def test_deterministic_rerun(self):
        bars = _profile_bars_with_spike()
        a = compute_volume_profile(bars)
        b = compute_volume_profile(bars)
        self.assertEqual(a, b)

    def test_insufficient_bars_returns_none(self):
        self.assertIsNone(compute_volume_profile(_profile_bars_with_spike()[:5], lookback_bars=30))


if __name__ == "__main__":
    unittest.main()
