#!/usr/bin/env python3
"""Tests for calendar trading plan structuring (§2.4)."""

import unittest

from services.analysis_calendar_trading_plan_structure import (
    apply_calendar_trading_plan_structure,
    build_structured_calendar_trading_plan,
)
from services.analysis_pipeline import FinalizeContext, finalize_analysis


class CalendarTradingPlanStructureTests(unittest.TestCase):
    def test_builds_structured_plan_from_prose(self):
        payload = {
            "forward_scenarios": {
                "bullish": "[ABOVE] 40%: If Core PCE beats 0.3%, USD strengthens.",
                "bearish": "[BELOW] 35%: USD weakens.",
                "neutral": "[ON] 25%: muted reaction.",
            },
            "implications_takeaways": {"market_bias": "BULLISH for USD: inflation risk"},
            "trading_plan": {
                "best_approach": "If Core PCE beats 0.3%, then expect EUR/USD downside continuation.",
                "key_levels": "Illustrative levels: EUR/USD 1.0820-1.0850",
                "position_sizing": "Conservative ahead of release.",
            },
            "market_scenarios": {
                "neutral_zone": {"definition": "Print between 0.2% and 0.4% (±0.1 pp vs consensus) — limited surprise."}
            },
        }
        structured = build_structured_calendar_trading_plan(payload, event={"currency": "USD"})
        self.assertIn("If", structured["scenario_trigger"])
        self.assertTrue(structured["direction"])
        self.assertIn("1.0820-1.0850", structured["target_zone"])
        self.assertTrue(structured["invalidation"])

    def test_extract_if_clause_preserves_decimal_levels(self):
        payload = {
            "forward_scenarios": {},
            "implications_takeaways": {"market_bias": "BULLISH for USD"},
            "trading_plan": {
                "best_approach": "If EUR/USD breaks above **1.0850**, then expect continuation.",
                "key_levels": "EUR/USD 1.0850",
            },
        }
        structured = build_structured_calendar_trading_plan(payload, event={"currency": "USD"})
        self.assertIn("1.0850", structured["scenario_trigger"])
        self.assertNotIn("**1;", structured["scenario_trigger"])
        self.assertIn("1.0850", structured["entry_condition"])
        self.assertEqual(structured["scenario_trigger"].count("**") % 2, 0)
        self.assertEqual(structured["entry_condition"].count("**") % 2, 0)

    def test_apply_adds_metadata(self):
        out = apply_calendar_trading_plan_structure(
            {
                "trading_plan": {"best_approach": "If beat then buy USD.", "position_sizing": "Small size."},
                "implications_takeaways": {"market_bias": "BULLISH for USD"},
            },
            event={"currency": "USD"},
        )
        self.assertIn("trading_plan_structured", out)
        self.assertIn("trading_plan_structure_applied", out)
        self.assertEqual(out["trading_plan_structure_applied"]["surface"], "economic_calendar")

    def test_finalize_pipeline_attaches_structured_plan(self):
        payload = {
            "headline": "CPI preview",
            "forward_scenarios": {"bullish": "a", "bearish": "b", "neutral": "c"},
            "implications_takeaways": {"market_bias": "NEUTRAL for USD: mixed"},
            "trading_plan": {"best_approach": "If CPI beats, then USD firms."},
            "market_reaction": {},
            "confidence_score": 70,
            "event_summary": {"expected": "0.3%", "previous": "0.2%"},
        }
        out = finalize_analysis(
            payload,
            analysis_kind="calendar_event",
            context=FinalizeContext(
                validated_event={"title": "CPI y/y", "currency": "USD", "impact": "high", "expected": "0.3%", "previous": "0.2%"},
                analysis_type="pre_event",
            ),
            spine_enabled=False,
        )
        self.assertIn("trading_plan_structured", out)
        self.assertIn("trading_plan_structure_applied", out)


if __name__ == "__main__":
    unittest.main()

