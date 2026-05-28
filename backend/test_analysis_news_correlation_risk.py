#!/usr/bin/env python3
"""Tests for live-news correlation risk specificity (§3.5)."""

import unittest

from services.analysis_news_correlation_risk import (
    apply_news_correlation_risk_if_news,
    apply_news_correlation_risk_to_response,
)
from services.analysis_pipeline import FinalizeContext, finalize_analysis


class NewsCorrelationRiskTests(unittest.TestCase):
    def test_apply_adds_specific_detail_and_pairs(self):
        payload = {
            "immediate_reaction": "neutral",
            "key_pairs": ["EUR/USD", "GBP/USD", "USD/JPY"],
            "news_impact": "Headline raises recession concern and risk-off tone.",
            "trading_implications": "If risk-off extends, then USD/JPY may fade despite stable yields.",
            "risk_assessment": {"correlation_risk": "medium"},
        }
        out = apply_news_correlation_risk_to_response(payload, news_item={"currency_pairs": ["EUR/USD", "USD/JPY"]})
        self.assertIn("correlation_risk_display", out)
        self.assertIn("correlation_risk_applied", out)
        self.assertIn("EUR/USD", out["risk_assessment"]["correlation_risk_detail"])
        self.assertIn("USD/JPY", out["risk_assessment"]["correlation_risk_detail"])
        self.assertTrue(len(out["risk_assessment"]["correlation_pairs"]) >= 2)

    def test_non_news_passthrough(self):
        payload = {"x": 1}
        out = apply_news_correlation_risk_if_news(payload, "calendar_event")
        self.assertEqual(out, payload)

    def test_finalize_pipeline_attaches_news_correlation_fields(self):
        payload = {
            "news_impact": "EUR pressure as growth concerns build.",
            "trading_implications": "If EUR/USD loses 1.08, then downside momentum can extend.",
            "immediate_reaction": "neutral",
            "key_pairs": ["EUR/USD", "USD/JPY"],
            "confidence": 72,
            "volatility": "medium",
            "timeframe": "next session",
        }
        out = finalize_analysis(
            payload,
            analysis_kind="live_news",
            context=FinalizeContext(news_item={"title": "ECB warning", "currency_pairs": ["EUR/USD", "USD/JPY"]}),
            spine_enabled=False,
        )
        self.assertIn("correlation_risk_display", out)
        self.assertIn("correlation_risk_applied", out)
        self.assertIn("risk_assessment", out)
        self.assertIn("correlation_risk_detail", out["risk_assessment"])


if __name__ == "__main__":
    unittest.main()

