#!/usr/bin/env python3
"""
Central OpenAI model IDs and selection for FXSentinel analysis services.

Avoids deprecated names (e.g. gpt-4-turbo-preview → 404). Override via .env:
  OPENAI_HIGH_IMPACT_MODEL   — CPI, NFP, high-impact calendar/news (default gpt-4o)
  OPENAI_STANDARD_MODEL      — medium/low impact (default gpt-4o-mini)
  OPENAI_DEFAULT_MODEL       — alias for OPENAI_STANDARD_MODEL (legacy)
"""

from __future__ import annotations

import os
from typing import Dict, Optional

# Verified working on current OpenAI API (May 2026)
DEFAULT_HIGH_IMPACT_MODEL = "gpt-4o"
DEFAULT_STANDARD_MODEL = "gpt-4o-mini"
DEFAULT_HOLISTIC_NARRATIVE_MODEL = "gpt-4o-mini"

# Legacy / invalid — do not use in new code
DEPRECATED_MODELS = frozenset(
    {
        "gpt-4-turbo-preview",
        "gpt-4-turbo",
        "gpt-4-32k",
        "gpt-4-vision-preview",
    }
)

# Per-1K-token blended estimates for cost tracking (input+output average)
MODEL_COST_PER_1K_TOKENS: Dict[str, float] = {
    "gpt-4o": 0.008,
    "gpt-4o-mini": 0.0015,
    "gpt-3.5-turbo": 0.002,
}

# Finer-grained pricing for usage-based cost (USD per 1K tokens)
MODEL_TOKEN_PRICING: Dict[str, Dict[str, float]] = {
    "gpt-4o": {"input": 0.0025, "output": 0.01},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
}


def get_high_impact_model() -> str:
    return os.getenv("OPENAI_HIGH_IMPACT_MODEL", DEFAULT_HIGH_IMPACT_MODEL).strip()


def get_standard_model() -> str:
    return (
        os.getenv("OPENAI_STANDARD_MODEL")
        or os.getenv("OPENAI_DEFAULT_MODEL")
        or DEFAULT_STANDARD_MODEL
    ).strip()


def select_model_for_impact(impact: Optional[str]) -> str:
    """High → gpt-4o class; medium/low/unknown → gpt-4o-mini class."""
    level = str(impact or "medium").strip().lower()
    if level == "high":
        return get_high_impact_model()
    return get_standard_model()


def select_model_for_event(event: Dict) -> str:
    """Calendar-style event dict with optional impact field."""
    return select_model_for_impact(event.get("impact"))


def select_model_for_news(news_item: Dict) -> str:
    """Live news item dict with optional impact field."""
    return select_model_for_impact(news_item.get("impact"))

def select_model_for_holistic_narrative() -> str:
    """Model for holistic narrative enrichment (Phase H)."""
    configured = os.getenv("OPENAI_HOLISTIC_MODEL", DEFAULT_HOLISTIC_NARRATIVE_MODEL).strip()
    return normalize_model_id(configured)


def normalize_model_id(model: Optional[str]) -> str:
    """Map known deprecated IDs to current defaults."""
    if not model:
        return get_standard_model()
    m = model.strip()
    if m in DEPRECATED_MODELS:
        if m in ("gpt-4-turbo-preview", "gpt-4-turbo"):
            return get_high_impact_model()
        return get_standard_model()
    return m


def estimate_cost_from_usage(usage, model: str) -> float:
    """Estimate USD cost from OpenAI usage object."""
    if not usage:
        return 0.0
    model = normalize_model_id(model)
    pricing = MODEL_TOKEN_PRICING.get(model, MODEL_TOKEN_PRICING["gpt-4o-mini"])
    prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
    completion_tokens = getattr(usage, "completion_tokens", 0) or 0
    if not prompt_tokens and not completion_tokens:
        total = getattr(usage, "total_tokens", 0) or 0
        blended = MODEL_COST_PER_1K_TOKENS.get(model, 0.002)
        return (total / 1000.0) * blended
    input_cost = (prompt_tokens / 1000.0) * pricing["input"]
    output_cost = (completion_tokens / 1000.0) * pricing["output"]
    return input_cost + output_cost


def cost_per_1k_tokens(model: str) -> float:
    """Blended $/1K tokens for simple trackers."""
    return MODEL_COST_PER_1K_TOKENS.get(normalize_model_id(model), 0.002)
