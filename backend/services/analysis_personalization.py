#!/usr/bin/env python3
"""
Shared personalization helpers for AI analysis surfaces.

This module translates onboarding trader_profile data into a compact, stable
shape that can be consumed by GPT prompts and deterministic ranking logic.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from services.user_trader_profile import user_trader_profile_store

logger = logging.getLogger(__name__)


def _safe_list(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    out: List[str] = []
    seen = set()
    for item in value:
        if not isinstance(item, str):
            continue
        norm = item.strip().upper()
        if not norm or norm in seen:
            continue
        seen.add(norm)
        out.append(norm)
    return out


def get_user_personalization(user_id: Optional[str]) -> Dict[str, Any]:
    """
    Read and normalize onboarding personalization for one user.
    Never raises; returns neutral defaults when unavailable.
    """
    defaults: Dict[str, Any] = {
        "profile_available": False,
        "trading_style": "unsure",
        "experience_level": "intermediate",
        "primary_goal": "stay_informed",
        "primary_pairs": [],
        "analysis_depth": "balanced",
        "time_horizon_bias": "balanced",
        "default_feature_emphasis": "overview",
        "education_mode": "standard",
    }
    if not user_id:
        return defaults

    try:
        profile_payload = user_trader_profile_store.get_profile(user_id) or {}
        tp = profile_payload.get("trader_profile") or {}
        if not isinstance(tp, dict):
            return defaults

        trading_style = tp.get("trading_style") if tp.get("trading_style") in {"day", "swing", "both", "unsure"} else "unsure"
        experience_level = tp.get("experience_level") if tp.get("experience_level") in {"beginner", "intermediate", "advanced"} else "intermediate"
        primary_goal = tp.get("primary_goal") if tp.get("primary_goal") in {
            "stay_informed", "analysis_workflow", "alerts", "learning", "other"
        } else "stay_informed"
        primary_pairs = _safe_list(tp.get("primary_pairs"))

        analysis_depth = {
            "beginner": "guided",
            "intermediate": "balanced",
            "advanced": "concise_expert",
        }.get(experience_level, "balanced")

        time_horizon_bias = {
            "day": "intraday",
            "swing": "multi_day",
            "both": "dual_horizon",
            "unsure": "balanced",
        }.get(trading_style, "balanced")

        default_feature_emphasis = {
            "stay_informed": "briefing",
            "analysis_workflow": "scenario_planning",
            "alerts": "trigger_monitoring",
            "learning": "education",
            "other": "overview",
        }.get(primary_goal, "overview")

        return {
            "profile_available": True,
            "trading_style": trading_style,
            "experience_level": experience_level,
            "primary_goal": primary_goal,
            "primary_pairs": primary_pairs[:24],
            "analysis_depth": analysis_depth,
            "time_horizon_bias": time_horizon_bias,
            "default_feature_emphasis": default_feature_emphasis,
            "education_mode": "high" if experience_level == "beginner" else "standard",
        }
    except Exception as e:
        logger.debug("Personalization lookup failed for %s: %s", user_id, e)
        return defaults


def build_prompt_personalization_block(personalization: Optional[Dict[str, Any]], surface: str) -> str:
    """
    Build a concise prompt block with user-preference steering instructions.
    """
    p = personalization or {}
    if not p:
        return ""

    style = p.get("trading_style", "unsure")
    level = p.get("experience_level", "intermediate")
    goal = p.get("primary_goal", "stay_informed")
    pairs = p.get("primary_pairs") or []
    depth = p.get("analysis_depth", "balanced")
    horizon = p.get("time_horizon_bias", "balanced")
    emphasis = p.get("default_feature_emphasis", "overview")

    pair_text = ", ".join(pairs[:8]) if pairs else "None specified"
    return (
        f"USER PERSONALIZATION CONTEXT ({surface}):\n"
        f"- Trading style: {style}\n"
        f"- Experience level: {level}\n"
        f"- Primary goal: {goal}\n"
        f"- Preferred instruments: {pair_text}\n"
        f"- Analysis depth mode: {depth}\n"
        f"- Time horizon bias: {horizon}\n"
        f"- Feature emphasis: {emphasis}\n\n"
        "PERSONALIZATION INSTRUCTIONS:\n"
        "- Keep the original analysis quality bar, but adapt framing and detail level.\n"
        "- If preferred instruments are relevant, reference them first.\n"
        "- For beginners: define key concepts briefly and avoid dense jargon.\n"
        "- For advanced users: keep explanations tighter and signal-focused.\n"
        "- Align structure with user goal (briefing vs workflow vs alerts vs learning).\n"
    )


def prioritize_instruments(instruments: List[str], preferred_instruments: List[str], limit: int = 4) -> List[str]:
    """
    Reorder instruments so user-preferred instruments appear first when present.
    """
    preferred_set = {p.strip().upper() for p in (preferred_instruments or []) if isinstance(p, str)}
    seen = set()
    prioritized: List[str] = []

    for raw in instruments or []:
        if not isinstance(raw, str):
            continue
        item = raw.strip().upper()
        if not item or item in seen:
            continue
        if item in preferred_set:
            prioritized.append(item)
            seen.add(item)

    for raw in instruments or []:
        if not isinstance(raw, str):
            continue
        item = raw.strip().upper()
        if not item or item in seen:
            continue
        prioritized.append(item)
        seen.add(item)

    return prioritized[:max(limit, 1)]
