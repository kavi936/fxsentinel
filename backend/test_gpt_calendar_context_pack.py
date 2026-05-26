"""Phase C — calendar prompt uses AnalysisContextPack when enabled."""

import os
import unittest
from unittest.mock import patch

from services.analysis_context_pack import is_analysis_context_pack_enabled
from services.gpt_ai_analysis import GPTAIAnalyzer, MarketContext


class GPTCalendarContextPackTests(unittest.TestCase):
    def setUp(self):
        self.analyzer = GPTAIAnalyzer()
        self.event = {
            "id": "evt-cpi-1",
            "title": "US CPI YoY",
            "currency": "USD",
            "impact": "high",
            "previous": "3.2%",
            "expected": "3.1%",
            "actual": "N/A",
        }
        self.market_context = MarketContext(
            current_prices={"EURUSD": 1.08},
            recent_volatility={"EURUSD": "0.5%"},
            market_sentiment={"risk": "neutral"},
            key_levels={},
            economic_calendar=[],
            bond_yields={},
            equity_indices={},
            commodity_prices={},
        )
        self._prev_pack = os.environ.get("ANALYSIS_CONTEXT_PACK_ENABLED")

    def tearDown(self):
        if self._prev_pack is None:
            os.environ.pop("ANALYSIS_CONTEXT_PACK_ENABLED", None)
        else:
            os.environ["ANALYSIS_CONTEXT_PACK_ENABLED"] = self._prev_pack

    @patch("services.gpt_ai_analysis.build_calendar_context_pack_section")
    def test_prompt_uses_pack_when_flag_on(self, mock_build_section):
        os.environ["ANALYSIS_CONTEXT_PACK_ENABLED"] = "true"
        mock_build_section.return_value = (
            {"surface": "calendar_event", "pack_version": "2026-05-18"},
            "ANALYSIS CONTEXT PACK (calendar_event) v2026-05-18\n\n"
            "CALENDAR CONTEXT PACK RULES (Phase F)\nREGIME VS EVENT",
        )

        prompt = self.analyzer._create_analysis_prompt(
            self.event,
            self.market_context,
            "pre_event",
            personalization={"primary_pairs": ["EURUSD"]},
            user_info={"user_id": "user-1", "user_email": "a@b.com"},
        )

        self.assertIn("ANALYSIS CONTEXT PACK", prompt)
        self.assertIn("Phase F", prompt)
        self.assertIn("REGIME VS EVENT", prompt)
        self.assertIn('"bullish":', prompt)
        self.assertNotIn("USER PERSONALIZATION CONTEXT (economic_calendar)", prompt)
        mock_build_section.assert_called_once()
        call_kw = mock_build_section.call_args.kwargs
        self.assertEqual(call_kw["user_id"], "user-1")
        self.assertEqual(call_kw["token_user_info"]["user_email"], "a@b.com")

    @patch("services.gpt_ai_analysis.build_relevant_market_context_block")
    @patch("services.gpt_ai_analysis.build_prompt_personalization_block")
    def test_prompt_legacy_blocks_when_flag_off(self, mock_pers, mock_market):
        os.environ["ANALYSIS_CONTEXT_PACK_ENABLED"] = "false"
        mock_market.return_value = "RELEVANT LIVE MARKET SNAPSHOT:\n- EURUSD"
        mock_pers.return_value = "USER PERSONALIZATION CONTEXT (economic_calendar):\n- pairs"

        prompt = self.analyzer._create_analysis_prompt(
            self.event,
            self.market_context,
            "pre_event",
            personalization={"primary_pairs": ["EURUSD"]},
        )

        self.assertIn("USER PERSONALIZATION CONTEXT", prompt)
        self.assertIn("RELEVANT LIVE MARKET SNAPSHOT", prompt)
        self.assertNotIn("ANALYSIS CONTEXT PACK", prompt)
        mock_market.assert_called_once()
        mock_pers.assert_called_once()

    def test_flag_default_off(self):
        os.environ.pop("ANALYSIS_CONTEXT_PACK_ENABLED", None)
        self.assertFalse(is_analysis_context_pack_enabled())


if __name__ == "__main__":
    unittest.main()
