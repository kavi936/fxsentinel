"""Tests for Phase 2 analysis pipeline finalize path."""

import os
import unittest

from services.analysis_contract import (
    ANALYSIS_KIND_CALENDAR_EVENT,
    ANALYSIS_KIND_ECONOMY_SCAN,
    ANALYSIS_KIND_LIVE_NEWS,
    SPINE_PROFILE_TRADER_BRIEF_V1,
)
from services.analysis_pipeline import FinalizeContext, finalize_analysis
from services.analysis_v1_spine import ANALYSIS_FORMAT_VERSION


class AnalysisPipelineTests(unittest.TestCase):
    def setUp(self):
        self._prev_v1 = os.environ.get("ANALYSIS_V1_ENABLED")
        os.environ["ANALYSIS_V1_ENABLED"] = "true"

    def tearDown(self):
        if self._prev_v1 is None:
            os.environ.pop("ANALYSIS_V1_ENABLED", None)
        else:
            os.environ["ANALYSIS_V1_ENABLED"] = self._prev_v1

    def test_finalize_passthrough_when_v1_disabled(self):
        os.environ["ANALYSIS_V1_ENABLED"] = "false"
        payload = {"headline": "Only body"}
        out = finalize_analysis(
            payload,
            analysis_kind=ANALYSIS_KIND_LIVE_NEWS,
            context=FinalizeContext(news_item={"title": "t"}),
        )
        self.assertEqual(out, payload)
        self.assertNotIn("spine", out)
        self.assertNotIn("trace", out)

    def test_finalize_calendar_envelope(self):
        os.environ["ANALYSIS_V1_ENABLED"] = "true"
        payload = {
            "headline": "CPI preview",
            "forward_scenarios": {"bullish": "a", "bearish": "b", "neutral": "c"},
            "implications_takeaways": {"market_bias": "neutral"},
            "trading_plan": {},
            "market_reaction": {},
            "confidence_score": 70,
        }
        out = finalize_analysis(
            payload,
            analysis_kind=ANALYSIS_KIND_CALENDAR_EVENT,
            context=FinalizeContext(
                validated_event={"title": "CPI y/y", "currency": "USD"},
                analysis_type="pre_event",
                latency_ms=42,
            ),
        )
        self.assertEqual(out["analysis_kind"], ANALYSIS_KIND_CALENDAR_EVENT)
        self.assertEqual(out["spine_profile"], SPINE_PROFILE_TRADER_BRIEF_V1)
        self.assertEqual(out["analysis_format_version"], ANALYSIS_FORMAT_VERSION)
        self.assertIn("trace", out)
        self.assertIn("finalize:trader_brief_v1", out["trace"]["steps"])
        self.assertTrue(out["v1_observability"]["spine_present"])

    def test_finalize_economy_scan_wrapper(self):
        payload = {
            "status": "success",
            "scan": {
                "economy": "United States",
                "short_term": {"bias": "bearish", "confidence": 80},
                "trader_brief": {"short_term_line": "Bearish regime"},
                "pair_setups": [{"pair": "EURUSD"}],
                "quality_overrides": {},
            },
        }
        out = finalize_analysis(
            payload,
            analysis_kind=ANALYSIS_KIND_ECONOMY_SCAN,
            context=FinalizeContext(country_code="US"),
        )
        self.assertEqual(out["analysis_kind"], ANALYSIS_KIND_ECONOMY_SCAN)
        self.assertEqual(out["spine"]["bias"], "bearish")

    def test_finalize_news_envelope(self):
        payload = {
            "news_impact": "Oil risk",
            "immediate_reaction": "neutral",
            "key_pairs": ["EUR/USD"],
            "confidence": 75,
            "volatility": "low",
            "timeframe": "next session",
        }
        out = finalize_analysis(
            payload,
            analysis_kind=ANALYSIS_KIND_LIVE_NEWS,
            context=FinalizeContext(news_item={"title": "Headline", "id": 1}),
        )
        self.assertEqual(out["analysis_kind"], ANALYSIS_KIND_LIVE_NEWS)
        self.assertEqual(out["spine"]["bias"], "neutral")


if __name__ == "__main__":
    unittest.main()
