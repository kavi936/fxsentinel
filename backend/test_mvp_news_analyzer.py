import unittest

from services.mvp_news_analyzer import MVPNewsAnalyzer


class MVPNewsAnalyzerConsistencyTests(unittest.TestCase):
    def setUp(self):
        self.analyzer = MVPNewsAnalyzer()

    def test_enforce_reaction_consistency_upgrades_neutral_to_bearish(self):
        adjusted = self.analyzer._enforce_reaction_consistency(
            "neutral",
            "The tone is **dovish Fed** and suggests **USD weakens** after the headline.",
            "If follow-through appears, expect EUR/USD drift higher while dollar demand fades.",
        )
        self.assertEqual(adjusted, "bearish_usd")

    def test_enforce_reaction_consistency_keeps_explicit_bullish(self):
        adjusted = self.analyzer._enforce_reaction_consistency(
            "bullish_usd",
            "The release supports a **hawkish Fed** and points to **USD strengthens** conditions.",
            "Watch for continuation if yields rise.",
        )
        self.assertEqual(adjusted, "bullish_usd")


if __name__ == "__main__":
    unittest.main()
