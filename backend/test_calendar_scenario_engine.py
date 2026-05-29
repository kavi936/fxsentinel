"""Tests for canonical calendar scenario engine (Phase 3)."""

import unittest

from services.calendar_scenario_engine import (
    EVENT_DIRECTION_POLICY,
    build_market_scenarios,
    calendar_scenario_alignment_warnings,
    forward_scenarios_by_outcome,
    get_event_direction_mapping,
)
from services.analysis_v1_spine import merge_v1_calendar_response


class CalendarScenarioEngineTests(unittest.TestCase):
    def test_direction_policy_table_contains_core_families(self):
        self.assertIn("inflation", EVENT_DIRECTION_POLICY)
        self.assertIn("wages", EVENT_DIRECTION_POLICY)
        self.assertIn("employment", EVENT_DIRECTION_POLICY)
        self.assertIn("interest_rate", EVENT_DIRECTION_POLICY)
        self.assertTrue(EVENT_DIRECTION_POLICY["inflation"]["higher_is_bullish_for_currency"])
        self.assertFalse(EVENT_DIRECTION_POLICY["wages"]["higher_is_bullish_for_currency"])
        self.assertTrue(EVENT_DIRECTION_POLICY["employment"]["higher_is_bullish_for_currency"])
        self.assertTrue(EVENT_DIRECTION_POLICY["interest_rate"]["higher_is_bullish_for_currency"])

    def test_common_calendar_aliases_map_correctly(self):
        inflation = get_event_direction_mapping("Core PCE Price Index m/m")
        self.assertEqual(inflation["event_type"], "inflation")
        self.assertTrue(inflation["higher_is_bullish_for_currency"])

        rates = get_event_direction_mapping("Federal Funds Rate")
        self.assertEqual(rates["event_type"], "interest_rate")
        self.assertTrue(rates["higher_is_bullish_for_currency"])

        unemployment = get_event_direction_mapping("Claimant Count Change")
        self.assertEqual(unemployment["event_type"], "unemployment")
        self.assertFalse(unemployment["higher_is_bullish_for_currency"])

        wages = get_event_direction_mapping("Prelim Unit Labor Costs q/q")
        self.assertEqual(wages["event_type"], "wages")
        self.assertFalse(wages["higher_is_bullish_for_currency"])

        employment = get_event_direction_mapping("JOLTS Job Openings")
        self.assertEqual(employment["event_type"], "employment")
        self.assertTrue(employment["higher_is_bullish_for_currency"])

    def test_cpi_above_is_bullish_for_event_currency(self):
        ms = build_market_scenarios(
            event_title="Consumer Price Index y/y",
            currency="USD",
            expected="3.7%",
        )
        self.assertIsNotNone(ms)
        self.assertTrue(ms["higher_is_bullish_for_currency"])
        self.assertEqual(ms["rows"]["above"][0]["sentiment"], "Bullish")
        self.assertEqual(ms["rows"]["below"][0]["sentiment"], "Bearish")

    def test_nfp_above_is_bullish_usd(self):
        ms = build_market_scenarios(
            event_title="Non-Farm Payrolls",
            currency="USD",
            expected="200K",
        )
        self.assertTrue(ms["higher_is_bullish_for_currency"])
        self.assertEqual(ms["rows"]["above"][0]["sentiment"], "Bullish")

    def test_cpi_usd_strength_in_bullish_bucket_aligns(self):
        fs = {
            "bullish": "Hot CPI: USD strengthens above consensus.",
            "bearish": "Soft print",
            "neutral": "In line",
        }
        ms = build_market_scenarios(
            event_title="Consumer Price Index y/y",
            currency="USD",
            expected="3.7%",
        )
        warnings = calendar_scenario_alignment_warnings(
            "Consumer Price Index y/y", "USD", fs, market_scenarios=ms
        )
        self.assertEqual(len(warnings), 0)

    def test_forward_scenarios_by_outcome_keys(self):
        fs = {"bullish": "a", "bearish": "b", "neutral": "c"}
        mapped = forward_scenarios_by_outcome(fs)
        self.assertEqual(mapped["above"], "a")
        self.assertEqual(mapped["below"], "b")
        self.assertEqual(mapped["on_forecast"], "c")

    def test_merge_includes_market_scenarios(self):
        payload = {
            "event_summary": {"expected": "3.7%", "previous": "3.3%"},
            "forward_scenarios": {
                "bullish": "Above forecast path",
                "bearish": "Below",
                "neutral": "Inline",
            },
            "implications_takeaways": {"market_bias": "neutral"},
            "trading_plan": {},
            "market_reaction": {},
            "confidence_score": 70,
        }
        out = merge_v1_calendar_response(
            payload,
            validated_event={"title": "CPI y/y", "currency": "USD"},
            analysis_type="pre_event",
        )
        self.assertIn("market_scenarios", out)
        self.assertIn("forward_scenarios_by_outcome", out)
        self.assertEqual(
            get_event_direction_mapping("CPI y/y")["event_type"],
            "inflation",
        )


if __name__ == "__main__":
    unittest.main()
