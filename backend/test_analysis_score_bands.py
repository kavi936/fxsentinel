#!/usr/bin/env python3
"""Tests for shared macro score bands (holistic v2)."""

import unittest

from services.analysis_bias_classification import classify_from_score
from services.analysis_score_bands import (
    BIAS_BULLISH_MIN,
    NEUTRAL_BAND_MAX,
    compute_directional_conviction,
    score_to_base_bias,
)


class AnalysisScoreBandsTests(unittest.TestCase):
    def test_narrow_neutral_band(self):
        self.assertEqual(score_to_base_bias(12), "neutral")
        self.assertEqual(score_to_base_bias(BIAS_BULLISH_MIN), "bullish")
        self.assertEqual(score_to_base_bias(-BIAS_BULLISH_MIN), "bearish")

    def test_headline_bias_promotes_lean(self):
        row = classify_from_score(8.0)
        self.assertEqual(row["bias"], "neutral")
        self.assertEqual(row["headline_bias"], "BULLISH LEAN")
        self.assertIn("BULLISH LEAN", row["display_bias"])

    def test_directional_conviction_low_when_stale(self):
        self.assertEqual(compute_directional_conviction(-13, 50, incomplete=False), "low")

    def test_directional_conviction_medium_on_lean(self):
        self.assertEqual(compute_directional_conviction(8, 75, incomplete=False), "medium")


if __name__ == "__main__":
    unittest.main()
