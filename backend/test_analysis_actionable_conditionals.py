#!/usr/bin/env python3
"""Tests for If X → then Y actionable conditional enforcement."""

import unittest

from services.analysis_actionable_conditionals import (
    apply_actionable_conditionals_to_response,
    count_conditionals,
    has_actionable_conditional,
    validate_and_enforce_calendar,
    validate_and_enforce_news,
)
from services.analysis_contract import ANALYSIS_KIND_CALENDAR_EVENT, ANALYSIS_KIND_LIVE_NEWS


class ActionableConditionalsTests(unittest.TestCase):
    def test_detects_if_then_pattern(self):
        text = "If CPI beats forecast, then expect EUR/USD to test 1.09."
        self.assertTrue(has_actionable_conditional(text))
        self.assertGreaterEqual(count_conditionals(text), 1)

    def test_calendar_appends_trading_plan_conditional(self):
        payload = {
            "headline": "US CPI",
            "key_takeaway": "Inflation in focus.",
            "forward_scenarios": {
                "bullish": "Hot print supports USD.",
                "bearish": "Soft print weighs on USD.",
                "neutral": "Inline print.",
            },
            "trading_plan": {
                "best_approach": "Monitor upcoming data and watch EUR/USD closely.",
            },
        }
        event = {"title": "Core CPI", "currency": "USD", "forecast": "0.3%"}
        out, meta = validate_and_enforce_calendar(
            payload,
            event=event,
            analysis_type="pre_event",
        )
        self.assertIn("appended_trading_plan", " ".join(meta.get("enforcement_actions") or []))
        self.assertTrue(has_actionable_conditional(out["trading_plan"]["best_approach"]))

    def test_news_appends_trading_implications_conditional(self):
        payload = {
            "news_impact": "Headline adds USD pressure.",
            "trading_implications": "Traders should remain vigilant and monitor levels.",
        }
        news_item = {"title": "ECB speaker", "currency_pairs": ["EUR/USD"]}
        out, meta = validate_and_enforce_news(payload, news_item=news_item)
        self.assertIn("appended_trading_implications", " ".join(meta.get("enforcement_actions") or []))
        self.assertTrue(has_actionable_conditional(out["trading_implications"]))

    def test_finalize_kind_news_attaches_metadata(self):
        payload = {
            "news_impact": "Risk-off tone.",
            "trading_implications": "Watch price action.",
        }
        out = apply_actionable_conditionals_to_response(
            payload,
            ANALYSIS_KIND_LIVE_NEWS,
            news_item={"title": "Oil spike", "currency_pairs": ["XAU/USD"]},
        )
        self.assertIn("actionable_triggers_applied", out)
        self.assertEqual(out["actionable_triggers_applied"]["surface"], "live_news")

    def test_calendar_forward_scenarios_ab_tags_count(self):
        payload = {
            "forward_scenarios": {
                "bullish": "[ABOVE] 40%: USD strength if beat.",
                "bearish": "[BELOW] 35%: USD weakness if miss.",
                "neutral": "[ON] 25%: range if inline.",
            },
            "trading_plan": {"best_approach": "If beat, then target 1.09; if miss, fade to 1.05."},
        }
        out, meta = validate_and_enforce_calendar(payload, event={"currency": "USD"}, analysis_type="pre_event")
        checks = {c["id"]: c["passed"] for c in meta["checks"]}
        self.assertTrue(checks.get("forward_scenarios_conditional"))
        self.assertTrue(checks.get("global_conditional_present"))


if __name__ == "__main__":
    unittest.main()
