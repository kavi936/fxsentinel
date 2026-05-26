#!/usr/bin/env python3
"""Tests for central OpenAI model configuration."""

import os
import unittest
from unittest.mock import MagicMock

from services.openai_model_config import (
    DEFAULT_HIGH_IMPACT_MODEL,
    DEFAULT_STANDARD_MODEL,
    DEPRECATED_MODELS,
    estimate_cost_from_usage,
    normalize_model_id,
    select_model_for_impact,
)


class TestOpenAIModelConfig(unittest.TestCase):
    def test_defaults_are_modern_models(self):
        self.assertEqual(DEFAULT_HIGH_IMPACT_MODEL, "gpt-4o")
        self.assertEqual(DEFAULT_STANDARD_MODEL, "gpt-4o-mini")
        self.assertNotIn(DEFAULT_HIGH_IMPACT_MODEL, DEPRECATED_MODELS)
        self.assertNotIn(DEFAULT_STANDARD_MODEL, DEPRECATED_MODELS)

    def test_select_model_for_impact(self):
        self.assertEqual(select_model_for_impact("high"), "gpt-4o")
        self.assertEqual(select_model_for_impact("medium"), "gpt-4o-mini")
        self.assertEqual(select_model_for_impact("low"), "gpt-4o-mini")

    def test_normalize_deprecated_to_current(self):
        self.assertEqual(normalize_model_id("gpt-4-turbo-preview"), "gpt-4o")
        self.assertEqual(normalize_model_id("gpt-4-turbo"), "gpt-4o")

    def test_env_override(self):
        prev_h = os.environ.get("OPENAI_HIGH_IMPACT_MODEL")
        prev_s = os.environ.get("OPENAI_STANDARD_MODEL")
        try:
            os.environ["OPENAI_HIGH_IMPACT_MODEL"] = "gpt-4o-mini"
            os.environ["OPENAI_STANDARD_MODEL"] = "gpt-3.5-turbo"
            from importlib import reload
            import services.openai_model_config as cfg

            reload(cfg)
            self.assertEqual(cfg.get_high_impact_model(), "gpt-4o-mini")
            self.assertEqual(cfg.get_standard_model(), "gpt-3.5-turbo")
        finally:
            if prev_h is None:
                os.environ.pop("OPENAI_HIGH_IMPACT_MODEL", None)
            else:
                os.environ["OPENAI_HIGH_IMPACT_MODEL"] = prev_h
            if prev_s is None:
                os.environ.pop("OPENAI_STANDARD_MODEL", None)
            else:
                os.environ["OPENAI_STANDARD_MODEL"] = prev_s
            from importlib import reload
            import services.openai_model_config as cfg

            reload(cfg)

    def test_estimate_cost_from_usage(self):
        usage = MagicMock(prompt_tokens=1000, completion_tokens=500, total_tokens=1500)
        cost = estimate_cost_from_usage(usage, "gpt-4o")
        self.assertGreater(cost, 0)


if __name__ == "__main__":
    unittest.main()
