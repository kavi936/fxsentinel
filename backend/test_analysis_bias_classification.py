#!/usr/bin/env python3
"""Tests for NEUTRAL sub-classification (review #9)."""

import unittest

from services.analysis_bias_classification import (
    BIAS_CLASS_NEUTRAL_BEARISH_LEAN,
    BIAS_CLASS_NEUTRAL_BULLISH_LEAN,
    BIAS_CLASS_TRUE_NEUTRAL,
    apply_bias_classification_to_response,
    classify_calendar_bias,
    classify_from_score,
    classify_usd_reaction,
    infer_lean_from_forward_scenarios,
)
from services.analysis_contract import (
    ANALYSIS_KIND_CALENDAR_EVENT,
    ANALYSIS_KIND_ECONOMY_SCAN,
    ANALYSIS_KIND_LIVE_NEWS,
)
from services.economy_holistic_scan_service import EconomyHolisticScanService


def _indicator(values):
    return {"chartData": values}


class BiasClassificationTests(unittest.TestCase):
    def test_score_neutral_bullish_lean(self):
        row = classify_from_score(12.0)
        self.assertEqual(row["bias"], "neutral")
        self.assertEqual(row["bias_classification"], BIAS_CLASS_NEUTRAL_BULLISH_LEAN)
        self.assertIn("BULLISH LEAN", row["display_bias"])

    def test_score_true_neutral(self):
        row = classify_from_score(2.0)
        self.assertEqual(row["bias_classification"], BIAS_CLASS_TRUE_NEUTRAL)

    def test_news_neutral_with_bearish_narrative_gets_lean(self):
        row = classify_usd_reaction(
            "neutral",
            "Bearish USD pressure after the headline with downward euro move.",
            "EUR/USD may drift lower if risk appetite fades.",
        )
        self.assertIn("LEAN", row["reaction_display"].upper())

    def test_calendar_scenario_skew_lean(self):
        lean = infer_lean_from_forward_scenarios(
            {
                "bullish": "[ABOVE] 60%: beat path",
                "bearish": "[BELOW] 25%: miss path",
                "neutral": "[ON] 15%: inline",
            }
        )
        self.assertEqual(lean, BIAS_CLASS_NEUTRAL_BULLISH_LEAN)

    def test_calendar_finalize_attaches_fields(self):
        payload = {
            "implications_takeaways": {"market_bias": "NEUTRAL: mixed drivers"},
            "forward_scenarios": {
                "bullish": "[ABOVE] 55%: higher",
                "bearish": "[BELOW] 30%: lower",
                "neutral": "[ON] 15%: inline",
            },
        }
        out = apply_bias_classification_to_response(payload, ANALYSIS_KIND_CALENDAR_EVENT)
        self.assertIn("bias_classification_applied", out)
        self.assertIn("bias_classification", out["implications_takeaways"])
        self.assertIn("display_bias", out["implications_takeaways"])

    def test_holistic_scan_build_includes_classification(self):
        service = EconomyHolisticScanService()
        indicators = {
            "inflation": _indicator([2.0, 2.1, 2.0, 2.2, 2.3, 2.4]),
            "interest-rate": _indicator([4.5, 4.6, 4.55, 4.58, 4.6, 4.62]),
            "gdp-growth": _indicator([2.0, 2.1, 2.0, 2.05, 2.1, 2.15]),
            "unemployment": _indicator([4.0, 3.9, 3.95, 3.92, 3.9, 3.88]),
        }
        yields = {
            "US02Y": {"price": 4.5, "change": 0.02},
            "US10Y": {"price": 4.6, "change": 0.01},
            "US30Y": {"price": 4.7, "change": 0.0},
        }
        scan = service.build_scan("US", indicators, [], yields)
        self.assertIn("bias_classification", scan["short_term"])
        self.assertIn("display_bias", scan["short_term"])

    def test_classify_calendar_strong_bias(self):
        row = classify_calendar_bias(
            {"market_bias": "BULLISH for USD: hot CPI"},
            {},
        )
        self.assertEqual(row["bias_classification"], "bullish")


if __name__ == "__main__":
    unittest.main()
