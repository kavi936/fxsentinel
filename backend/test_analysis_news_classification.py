#!/usr/bin/env python3
"""Tests for live news type + react guidance (V2 Tier 3: NA1, NA2)."""

import unittest

from services.analysis_news_classification import (
    apply_news_classification,
    infer_news_type_from_text,
)
from services.analysis_pipeline import FinalizeContext, finalize_analysis


class NewsClassificationTests(unittest.TestCase):
    def test_ecb_policy_classified_multi_day(self):
        out = apply_news_classification(
            {
                "news_impact": "ECB tightening bias supports a stronger euro.",
                "trading_implications": "EUR/USD may rally through June as hikes are priced.",
                "impact_horizon": "intraday",
                "volatility": "medium",
            },
            news_item={"title": "ECB signals June rate hikes"},
        )
        self.assertEqual(out["news_type"], "policy_signal")
        self.assertEqual(out["impact_horizon"], "multi_day")
        self.assertEqual(out["initial_reaction_guidance"], "wait_confirmation")
        self.assertIn("Policy signal", out["news_type_display"])

    def test_analyst_note_defaults_to_fade(self):
        out = apply_news_classification(
            {
                "news_impact": "Goldman raises gold target.",
                "trading_implications": "XAU/USD may grind higher.",
                "initial_reaction_guidance": "follow",
            },
            news_item={"title": "Goldman Sachs raises XAU price target"},
        )
        self.assertEqual(out["news_type"], "analyst_note")
        self.assertEqual(out["initial_reaction_guidance"], "fade")

    def test_nfp_data_print_follow(self):
        text = "US NFP beats expectations; USD bid across G10."
        self.assertEqual(infer_news_type_from_text(text), "data_print")
        out = apply_news_classification(
            {
                "news_impact": text,
                "trading_implications": "If follow-through holds, USD extends.",
                "volatility": "high",
            },
            news_item={"title": "US Nonfarm Payrolls beat forecast"},
        )
        self.assertEqual(out["news_type"], "data_print")
        self.assertEqual(out["initial_reaction_guidance"], "follow")

    def test_finalize_attaches_classification_metadata(self):
        payload = {
            "title": "ECB hawkish",
            "news_impact": "ECB hawkish bias.",
            "trading_implications": "Watch EUR/USD.",
            "immediate_reaction": "neutral",
            "key_pairs": ["EUR/USD"],
            "timeframe": "next 2-4 hours",
        }
        out = finalize_analysis(
            payload,
            analysis_kind="live_news",
            context=FinalizeContext(
                news_item={"title": "ECB tightening bias supports EUR"},
                personalization={"primary_pairs": ["EUR/USD"]},
            ),
        )
        self.assertIn("news_classification_applied", out)
        self.assertIn("news_type_display", out)
        self.assertIn("initial_reaction_guidance_display", out)


if __name__ == "__main__":
    unittest.main()
