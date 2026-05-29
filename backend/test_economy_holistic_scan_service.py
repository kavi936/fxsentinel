import unittest

from services.economy_holistic_scan_service import EconomyHolisticScanService


def _indicator(values):
    return {"chartData": values}


class EconomyHolisticScanServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = EconomyHolisticScanService()
        self.components = [{"available": True} for _ in range(10)]

    def test_staleness_confidence_rule_thresholds(self):
        day = 60 * 60 * 24
        self.assertEqual(self.service._staleness_confidence_rule(29 * day)["cap"], 50)
        self.assertEqual(self.service._staleness_confidence_rule(22 * day)["cap"], 55)
        self.assertEqual(self.service._staleness_confidence_rule(15 * day)["cap"], 65)
        self.assertEqual(self.service._staleness_confidence_rule(8 * day)["cap"], 80)
        self.assertEqual(self.service._staleness_confidence_rule(2 * day)["cap"], 95)

    def test_confidence_penalized_for_stale_inputs(self):
        day = 60 * 60 * 24
        fresh = self.service._confidence(self.components, [], 2 * day)
        stale = self.service._confidence(self.components, [], 29 * day)
        self.assertGreater(fresh, stale)
        self.assertLessEqual(stale, 50)

    def test_score_to_bias_uses_documented_thresholds(self):
        self.assertEqual(self.service._score_to_bias(14), "neutral")
        self.assertEqual(self.service._score_to_bias(15), "bullish")
        self.assertEqual(self.service._score_to_bias(-12), "neutral")
        self.assertEqual(self.service._score_to_bias(-15), "bearish")
        self.assertEqual(self.service._score_to_bias(8), "neutral")

    def test_score_position_label_neutral_band(self):
        self.assertEqual(self.service._score_position_label(-8), "Neutral band, bearish lean")
        self.assertEqual(self.service._score_position_label(0), "Neutral band, balanced")
        self.assertEqual(self.service._score_position_label(-16), "Mild bearish")
        self.assertEqual(self.service._score_position_label(35), "Moderate bullish")

    def test_component_breakdown_sums_driver_contributions(self):
        components = [
            {"name": "Rate momentum", "contribution": -8.4, "direction": "negative", "weight": 0.35, "available": True, "note": "test"},
            {"name": "Growth momentum", "contribution": -6.2, "direction": "negative", "weight": 0.20, "available": True, "note": "test"},
            {"name": "Inflation momentum", "contribution": 4.1, "direction": "positive", "weight": 0.25, "available": True, "note": "test"},
        ]
        breakdown = self.service._build_component_breakdown(components, -10.5)
        self.assertEqual(breakdown["total"], -10)
        self.assertEqual(len(breakdown["drivers"]), 3)
        self.assertEqual(breakdown["drivers"][0]["contribution_display"], "-8.4")

    def test_build_scan_exposes_score_scale_and_breakdown(self):
        indicators = {
            "inflation": _indicator([2.0, 2.1, 2.0, 2.2, 2.3, 2.4]),
            "interest-rate": _indicator([4.5, 4.6, 4.55, 4.58, 4.6, 4.62]),
            "gdp-growth": _indicator([2.0, 2.1, 2.0, 2.05, 2.1, 2.15]),
            "unemployment": _indicator([4.0, 3.9, 3.95, 3.92, 3.9, 3.88]),
        }
        yields = {
            "US02Y": {"price": 4.5, "change": 0.02},
            "US10Y": {"price": 4.6, "change": 0.01},
            "US30Y": {"price": 4.7, "change": 0.0},
        }
        scan = self.service.build_scan(
            country_code="US",
            indicators=indicators,
            events=[],
            yields=yields,
        )
        self.assertIn("score_scale", scan)
        self.assertEqual(scan["score_scale"]["min"], -100)
        self.assertEqual(scan["score_scale"]["max"], 100)
        self.assertIn("component_breakdown", scan["short_term"])
        self.assertIn("position_label", scan["short_term"])
        self.assertIn("score_display", scan["short_term"])
        self.assertIsInstance(scan["short_term"]["score"], int)


if __name__ == "__main__":
    unittest.main()
