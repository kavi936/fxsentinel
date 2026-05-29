#!/usr/bin/env python3
"""Tests for live news horizon + pairs focus (V2 Tier 2)."""

import unittest

from services.analysis_news_horizon import apply_news_horizon_and_pairs_focus
from services.analysis_pipeline import FinalizeContext, finalize_analysis


class NewsHorizonTests(unittest.TestCase):
    def test_policy_story_gets_multi_day_horizon(self):
        out = apply_news_horizon_and_pairs_focus(
            {
                "news_impact": "ECB tightening bias supports a stronger euro.",
                "trading_implications": "EUR/USD may rally through June as hikes are priced.",
                "timeframe": "next 2-4 hours",
                "key_pairs": ["EUR/USD", "GBP/USD"],
            },
            personalization={"primary_pairs": ["EUR/USD", "USD/JPY", "GBP/USD"]},
        )
        self.assertEqual(out["impact_horizon"], "multi_day")
        self.assertTrue(out.get("timeframe_positioning"))
        self.assertIn("Focused on", out.get("pairs_focus_display", ""))

    def test_finalize_attaches_horizon_metadata(self):
        payload = {
            "title": "ECB signals hikes",
            "news_impact": "ECB hawkish.",
            "trading_implications": "Watch EUR/USD.",
            "immediate_reaction": "neutral",
            "key_pairs": ["EUR/USD"],
            "timeframe": "next 2-4 hours",
        }
        out = finalize_analysis(
            payload,
            analysis_kind="live_news",
            context=FinalizeContext(
                personalization={"primary_pairs": ["EUR/USD", "USD/JPY"]},
            ),
        )
        self.assertIn("news_horizon_applied", out)
        self.assertIn("impact_horizon", out)


if __name__ == "__main__":
    unittest.main()
