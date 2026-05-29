#!/usr/bin/env python3
"""Tests for calendar content guard (V2 Tier 2)."""

import unittest

from services.analysis_calendar_content_guard import apply_calendar_content_guard
from services.analysis_pipeline import FinalizeContext, finalize_analysis


class CalendarContentGuardTests(unittest.TestCase):
    def test_spot_key_levels_relabeled(self):
        out = apply_calendar_content_guard(
            {
                "trading_plan": {"key_levels": "Anchored to current spot: EUR/USD 1.0842"},
                "next_catalysts": ["FOMC 18 Jun", "NFP 6 Jun"],
                "big_picture": {"forward_focus": "Track Core PCE follow-through into June FOMC."},
            },
            event={"title": "Core PCE Price Index m/m", "currency": "USD"},
        )
        self.assertEqual(out["trading_plan"]["key_levels_label"], "Spot reference")
        self.assertIn("Spot reference", out["trading_plan"]["key_levels"])

    def test_vague_catalyst_removed(self):
        out = apply_calendar_content_guard(
            {
                "next_catalysts": [
                    "FOMC 18 Jun",
                    "Geopolitical developments in the Middle East",
                ],
            },
            event={"title": "CPI y/y", "currency": "USD"},
        )
        self.assertEqual(len(out["next_catalysts"]), 1)
        self.assertIn("FOMC", out["next_catalysts"][0])
        self.assertGreaterEqual(len(out.get("next_catalysts_removed") or []), 1)

    def test_generic_forward_focus_replaced(self):
        out = apply_calendar_content_guard(
            {
                "big_picture": {
                    "forward_focus": "Monitor upcoming inflation data and geopolitical developments.",
                },
                "next_catalysts": ["NFP 6 Jun"],
            },
            event={"title": "Core PCE Price Index m/m", "currency": "USD"},
        )
        self.assertNotIn("geopolitical developments", out["big_picture"]["forward_focus"].lower())
        self.assertTrue(out["big_picture"].get("forward_focus_replaced"))

    def test_finalize_wires_guard(self):
        payload = {
            "headline": "Test",
            "forward_scenarios": {"bullish": "[ABOVE] 40%", "neutral": "[ON] 30%", "bearish": "[BELOW] 30%"},
            "event_summary": {"expected": "0.3%", "previous": "0.2%"},
            "implications_takeaways": {"market_bias": "NEUTRAL for USD"},
            "trading_plan": {"key_levels": "Anchored to current spot 1.08"},
            "next_catalysts": ["Geopolitical developments in the Middle East", "FOMC 18 Jun"],
            "big_picture": {"forward_focus": "Monitor inflation and geopolitical developments"},
        }
        event = {"title": "Core PCE", "currency": "USD", "impact": "high", "expected": "0.3%"}
        out = finalize_analysis(
            payload,
            analysis_kind="calendar_event",
            context=FinalizeContext(validated_event=event, analysis_type="pre_event"),
        )
        self.assertIn("calendar_content_guard_applied", out)
        self.assertEqual(out["trading_plan"].get("key_levels_label"), "Spot reference")


if __name__ == "__main__":
    unittest.main()
