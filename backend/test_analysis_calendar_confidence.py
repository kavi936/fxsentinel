#!/usr/bin/env python3
"""Tests for deterministic calendar confidence methodology."""

import unittest

from services.analysis_calendar_confidence import compute_calendar_confidence
from services.analysis_pipeline import FinalizeContext, finalize_analysis
from services.calendar_scenario_engine import compute_neutral_zone_range


class CalendarConfidenceTests(unittest.TestCase):
    def test_high_impact_with_forecast_scores_higher(self):
        good = compute_calendar_confidence(
            event={"impact": "high", "expected": "0.3%", "previous": "0.2%"},
            analysis_type="pre_event",
            payload={"forward_scenarios": {"bullish": "[ABOVE] 40%", "neutral": "[ON] 30%", "bearish": "[BELOW] 30%"}},
        )
        poor = compute_calendar_confidence(
            event={"impact": "high"},
            analysis_type="pre_event",
            payload={},
        )
        self.assertGreater(good["confidence_score"], poor["confidence_score"])
        self.assertIn("forecast", good["confidence_reason"].lower())

    def test_scenario_sum_penalty(self):
        bad = compute_calendar_confidence(
            event={"impact": "medium", "expected": "0.3%", "previous": "0.2%"},
            payload={"forward_scenarios": {"bullish": "[ABOVE] 50%", "neutral": "[ON] 30%", "bearish": "[BELOW] 30%"}},
        )
        self.assertTrue(any(f["id"] == "scenarios_sum" and f["delta"] < 0 for f in bad["confidence_factors"]))

    def test_finalize_attaches_confidence_metadata(self):
        payload = {
            "headline": "Test",
            "forward_scenarios": {"bullish": "[ABOVE] 35%", "neutral": "[ON] 35%", "bearish": "[BELOW] 30%"},
            "event_summary": {"expected": "0.3%", "previous": "0.2%"},
            "implications_takeaways": {"market_bias": "NEUTRAL for USD: mixed"},
            "confidence_score": 90,
        }
        event = {"title": "Core PCE Price Index m/m", "currency": "USD", "impact": "high", "expected": "0.3%", "previous": "0.2%"}
        out = finalize_analysis(
            payload,
            analysis_kind="calendar_event",
            context=FinalizeContext(validated_event=event, analysis_type="pre_event"),
        )
        self.assertIn("confidence_methodology_applied", out)
        self.assertIn("confidence_reason", out)
        self.assertIn("data_confidence_score", out)
        payload["edge_confidence_reason"] = "Core PCE beat would extend USD bid if services stay sticky."
        payload["analysis_confidence"] = "High"
        out2 = finalize_analysis(
            payload,
            analysis_kind="calendar_event",
            context=FinalizeContext(validated_event=event, analysis_type="pre_event"),
        )
        self.assertEqual(out2.get("edge_confidence"), "High")
        self.assertIn("USD bid", out2.get("edge_confidence_reason", ""))
        self.assertIsInstance(out.get("market_scenarios"), dict)
        self.assertIn("neutral_zone", out["market_scenarios"])


class NeutralZoneTests(unittest.TestCase):
    def test_neutral_zone_band_for_percent_forecast(self):
        zone = compute_neutral_zone_range("0.3%")
        self.assertIsNotNone(zone)
        assert zone is not None
        self.assertEqual(zone["low_display"], "0.2%")
        self.assertEqual(zone["high_display"], "0.4%")


if __name__ == "__main__":
    unittest.main()
