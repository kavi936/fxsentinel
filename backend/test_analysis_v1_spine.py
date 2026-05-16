"""Tests for V1 analysis spine helpers (stdlib unittest — no pytest required)."""

import unittest

from services.analysis_v1_spine import (
    ANALYSIS_FORMAT_VERSION,
    build_spine_holistic,
    calendar_scenario_alignment_warnings,
    is_analysis_v1_spine_enabled,
    merge_v1_calendar_response,
    merge_v1_news_response,
)


class AnalysisV1SpineTests(unittest.TestCase):
    def test_calendar_inflation_usd_mismatch_warning(self):
        title = "Consumer Price Index y/y"
        fs = {
            "bullish": "55% probability: **USD strengthens** on a hot print above consensus.",
            "bearish": "Bearish case",
            "neutral": "Neutral",
        }
        w = calendar_scenario_alignment_warnings(title, "USD", fs)
        self.assertEqual(len(w), 1)
        self.assertTrue(w)

    def test_calendar_no_warning_for_employment(self):
        title = "Non-Farm Payrolls"
        fs = {"bullish": "USD strengthens on strong jobs", "bearish": "x", "neutral": "y"}
        w = calendar_scenario_alignment_warnings(title, "USD", fs)
        self.assertEqual(w, [])

    def test_merge_calendar_adds_version_and_spine(self):
        payload = {
            "headline": "CPI preview",
            "key_takeaway": "Inflation matters",
            "forward_scenarios": {"bullish": "a", "bearish": "b", "neutral": "c"},
            "implications_takeaways": {"market_bias": "Neutral bias into the print"},
            "trading_plan": {"avoid_strategies": "Do not over-leverage"},
            "market_reaction": {"price_action": "EUR/USD and USD/JPY active"},
            "confidence_score": 72.0,
            "data_quality": "live_data",
            "validation_status": "ok",
        }
        event = {"title": "CPI m/m", "currency": "USD", "id": 1}
        out = merge_v1_calendar_response(
            payload,
            validated_event=event,
            analysis_type="pre_event",
        )
        self.assertEqual(out["analysis_format_version"], ANALYSIS_FORMAT_VERSION)
        self.assertEqual(out["spine"]["bias_subject"], "USD around this release")
        self.assertTrue(out["spine"]["primary_instruments"])
        self.assertIn("headline", out)
        self.assertIn("scenario_alignment_status", out)
        self.assertIn("level_context_note", out)

    def test_merge_news_spine(self):
        news_item = {"title": "Oil headline", "id": 1}
        analysis = {
            "news_impact": "Impact text",
            "trading_implications": "Trade text",
            "immediate_reaction": "bullish_usd",
            "key_pairs": ["EUR/USD"],
            "volatility": "high",
            "timeframe": "1h",
            "confidence": 80,
            "analysis_type": "gpt_enhanced",
            "risk_assessment": {},
            "market_context": {},
        }
        out = merge_v1_news_response(analysis, news_item)
        self.assertEqual(out["spine"]["bias"], "bullish")
        self.assertEqual(out["spine"]["bias_subject"], "USD")

    def test_spine_enabled_env(self):
        import os

        old = os.environ.get("ANALYSIS_V1_ENABLED")
        try:
            os.environ["ANALYSIS_V1_ENABLED"] = "false"
            self.assertFalse(is_analysis_v1_spine_enabled())
            os.environ["ANALYSIS_V1_ENABLED"] = "true"
            self.assertTrue(is_analysis_v1_spine_enabled())
        finally:
            if old is None:
                os.environ.pop("ANALYSIS_V1_ENABLED", None)
            else:
                os.environ["ANALYSIS_V1_ENABLED"] = old

    def test_build_spine_holistic_minimal(self):
        scan = {
            "economy": "United States",
            "short_term": {"bias": "bearish", "confidence": 80},
            "long_term": {"bias": "neutral"},
            "trader_brief": {"short_term_line": "Bearish · score", "key_risk": "events"},
            "pair_setups": [{"pair": "EURUSD", "invalidation": "Oil spike"}],
            "quality_overrides": {},
            "model_version": "economy_scan_v1.2",
        }
        spine = build_spine_holistic(scan, "US")
        self.assertEqual(spine["bias"], "bearish")
        self.assertIn("EURUSD", spine["primary_instruments"])

    def test_calendar_alignment_status_warning_for_cpi_usd(self):
        payload = {
            "headline": "CPI preview",
            "forward_scenarios": {"bullish": "USD strengthens on upside surprise"},
            "implications_takeaways": {"market_bias": "neutral"},
            "trading_plan": {"key_levels": "Watch 1.0800 and 1.0900"},
            "market_reaction": {"price_action": "EUR/USD active"},
            "confidence_score": 70,
        }
        out = merge_v1_calendar_response(
            payload,
            validated_event={"title": "Consumer Price Index y/y", "currency": "USD"},
            analysis_type="pre_event",
        )
        self.assertEqual(out.get("scenario_alignment_status"), "warning")
        self.assertTrue(out.get("scenario_alignment_warnings"))


if __name__ == "__main__":
    unittest.main()
