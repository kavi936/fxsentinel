#!/usr/bin/env python3
"""Tests for calendar context chart selection and payload."""

import unittest

from services.analysis_context_charts import (
    apply_context_chart_if_calendar,
    resolve_context_chart_for_event,
)
from services.analysis_indicator_registry import (
    pick_best_indicator_for_event,
    resolve_economy_key,
)


class AnalysisContextChartsTests(unittest.TestCase):
    def test_resolve_economy_from_country_aliases(self):
        self.assertEqual(resolve_economy_key("EU", None), "EUR")
        self.assertEqual(resolve_economy_key("GB", None), "GBP")
        self.assertEqual(resolve_economy_key(None, "USD"), "US")

    def test_pick_core_pce_us(self):
        ind = pick_best_indicator_for_event("US", "Core PCE Price Index m/m")
        self.assertEqual(ind, "core-inflation-YoY")

    def test_pick_nfp_us(self):
        ind = pick_best_indicator_for_event("US", "Non-Farm Payrolls")
        self.assertEqual(ind, "nonfarm-payrolls")

    def test_pick_ecb_rate_eur(self):
        ind = pick_best_indicator_for_event("EUR", "ECB Main Refinancing Rate")
        self.assertEqual(ind, "interest-rate")

    def test_unsupported_aud_returns_none(self):
        chart, meta = resolve_context_chart_for_event(
            {"title": "CPI m/m", "currency": "AUD", "country": "AU"}
        )
        self.assertIsNone(chart)
        self.assertEqual(meta.get("economy"), None)

    def test_us_pce_chart_payload(self):
        chart, meta = resolve_context_chart_for_event(
            {
                "title": "Core PCE Price Index m/m",
                "currency": "USD",
                "country": "US",
            }
        )
        self.assertIsNotNone(chart)
        self.assertEqual(chart["id"], "core-inflation-YoY")
        self.assertIsInstance(chart.get("chartData"), list)
        self.assertGreaterEqual(len(chart["chartData"]), 2)
        self.assertTrue(chart.get("showTargetLine"))
        self.assertEqual(meta["selected_indicator_id"], "core-inflation-YoY")

    def test_finalize_attaches_context_chart(self):
        out = apply_context_chart_if_calendar(
            {},
            "calendar_event",
            event={"title": "CPI m/m", "currency": "USD", "country": "US"},
        )
        self.assertIn("context_chart", out)
        self.assertIn("context_chart_meta", out)
        self.assertEqual(out["context_chart"]["id"], "inflation-YoY")


if __name__ == "__main__":
    unittest.main()
