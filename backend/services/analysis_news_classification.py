#!/usr/bin/env python3
"""
Live news story type + initial-reaction guidance (V2 Tier 3: NA1, NA2).
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional, Tuple

from services.analysis_contract import ANALYSIS_KIND_LIVE_NEWS

NEWS_CLASSIFICATION_PROMPT_RULES = """
NEWS TYPE & REACT PLAYBOOK (mandatory):
- news_type: exactly one of:
  headline_shock | data_print | central_bank_speech | policy_signal | geopolitical |
  analyst_note | structural_theme | other
- news_type_rationale: one sentence — what kind of story this is for traders.
- initial_reaction_guidance: exactly one of follow | fade | wait_confirmation
  - follow: first move often extends (hard data surprise, emergency CB action)
  - fade: headline spike often reverses (many speeches, analyst targets, thin headlines)
  - wait_confirmation: need hold/break, yields, or second headline (policy repricing, geopolitical)
- initial_reaction_guidance_rationale: one sentence on how the FIRST MOVE typically behaves.
- Do NOT give trade entries; describe typical first-move behaviour for this news category.
- policy_signal / structural_theme: prefer wait_confirmation over follow.
- Align news_type with impact_horizon (policy stories are rarely intraday-only).
""".strip()

_VALID_NEWS_TYPES = frozenset(
    {
        "headline_shock",
        "data_print",
        "central_bank_speech",
        "policy_signal",
        "geopolitical",
        "analyst_note",
        "structural_theme",
        "other",
    }
)

_VALID_GUIDANCE = frozenset({"follow", "fade", "wait_confirmation"})

_NEWS_TYPE_DISPLAY = {
    "headline_shock": "Headline shock",
    "data_print": "Data / calendar surprise",
    "central_bank_speech": "Central bank speech",
    "policy_signal": "Policy signal",
    "geopolitical": "Geopolitical / risk",
    "analyst_note": "Analyst / bank view",
    "structural_theme": "Structural theme",
    "other": "Market headline",
}

_GUIDANCE_DISPLAY = {
    "follow": "Follow initial move",
    "fade": "Fade initial spike",
    "wait_confirmation": "Wait for confirmation",
}

_HORIZON_SUFFIX = {
    "intraday": "hours",
    "multi_day": "multi-day to multi-week",
    "structural": "multi-week+",
}

_DEFAULT_GUIDANCE_BY_TYPE = {
    "headline_shock": "wait_confirmation",
    "data_print": "follow",
    "central_bank_speech": "wait_confirmation",
    "policy_signal": "wait_confirmation",
    "geopolitical": "wait_confirmation",
    "analyst_note": "fade",
    "structural_theme": "wait_confirmation",
    "other": "wait_confirmation",
}

_DEFAULT_GUIDANCE_RATIONALE = {
    "follow": "Hard surprises often see follow-through once direction is clear.",
    "fade": "Headline spikes for this category often partially reverse without confirmation.",
    "wait_confirmation": "First tick is often incomplete; wait for price, yields, or a second headline.",
}

_DATA_PRINT_RE = re.compile(
    r"\b(nfp|nonfarm|payroll|cpi|pce|gdp|pmi|ism|retail\s+sales|jobless|claims|"
    r"inflation\s+print|beats?\s+expect|miss(es|ed)?\s+expect|surprise\s+to\s+the)\b",
    re.IGNORECASE,
)
_POLICY_RE = re.compile(
    r"\b(ecb|fed|fomc|boe|boj|rate\s+hike|rate\s+cut|policy\s+signal|terminal\s+rate|"
    r"forward\s+guidance|tightening\s+bias|dovish\s+pivot|hikes?\s+pencilled)\b",
    re.IGNORECASE,
)
_SPEECH_RE = re.compile(
    r"\b(speech|remarks|testimony|press\s+conference|speaks|said\s+powell|said\s+lagarde)\b",
    re.IGNORECASE,
)
_ANALYST_RE = re.compile(
    r"\b(goldman|jpmorgan|morgan\s+stanley|barclays|ubs|deutsche|analyst|forecast|"
    r"price\s+target|raises?\s+target|cuts?\s+target)\b",
    re.IGNORECASE,
)
_GEOPOLITICAL_RE = re.compile(
    r"\b(war|sanction|invasion|missile|strait|hormuz|geopolitical|conflict|ceasefire)\b",
    re.IGNORECASE,
)
_STRUCTURAL_RE = re.compile(
    r"\b(structural|regime\s+shift|de[- ]?dollar|long[- ]term\s+theme|secular)\b",
    re.IGNORECASE,
)


def _combined_text(payload: Dict[str, Any], news_item: Optional[Dict[str, Any]] = None) -> str:
    parts = [
        str((news_item or {}).get("title") or ""),
        str((news_item or {}).get("summary") or ""),
        str(payload.get("title") or ""),
        str(payload.get("news_impact") or ""),
        str(payload.get("trading_implications") or ""),
    ]
    return " ".join(p for p in parts if p).strip()


def infer_news_type_from_text(text: str, *, news_item: Optional[Dict[str, Any]] = None) -> str:
    item = news_item or {}
    if str(item.get("type") or "").lower() in {"economic", "calendar"}:
        return "data_print"
    if _DATA_PRINT_RE.search(text):
        return "data_print"
    if _ANALYST_RE.search(text) and not _POLICY_RE.search(text):
        return "analyst_note"
    if _SPEECH_RE.search(text) and not _POLICY_RE.search(text):
        return "central_bank_speech"
    if _POLICY_RE.search(text):
        return "policy_signal"
    if _GEOPOLITICAL_RE.search(text):
        return "geopolitical"
    if _STRUCTURAL_RE.search(text):
        return "structural_theme"
    if re.search(r"\b(breaking|just\s+in|headline)\b", text, re.IGNORECASE):
        return "headline_shock"
    return "other"


def build_news_type_display(news_type: str, impact_horizon: str) -> str:
    label = _NEWS_TYPE_DISPLAY.get(news_type, _NEWS_TYPE_DISPLAY["other"])
    suffix = _HORIZON_SUFFIX.get(impact_horizon, "")
    if suffix:
        return f"{label} ({suffix})"
    return label


def default_guidance_for_type(
    news_type: str,
    *,
    impact_horizon: str = "intraday",
    volatility: str = "medium",
) -> str:
    guidance = _DEFAULT_GUIDANCE_BY_TYPE.get(news_type, "wait_confirmation")
    if impact_horizon == "structural" and guidance == "follow":
        return "wait_confirmation"
    if news_type == "data_print" and str(volatility).lower() == "high":
        return "follow"
    if news_type == "central_bank_speech" and guidance == "follow":
        return "wait_confirmation"
    return guidance


def _normalize_news_type(value: Any, text: str, news_item: Optional[Dict[str, Any]]) -> Tuple[str, str]:
    raw = str(value or "").strip().lower().replace(" ", "_").replace("-", "_")
    if raw in _VALID_NEWS_TYPES:
        return raw, "gpt"
    inferred = infer_news_type_from_text(text, news_item=news_item)
    return inferred, "heuristic"


def _normalize_guidance(value: Any, news_type: str, impact_horizon: str, volatility: str) -> Tuple[str, str]:
    raw = str(value or "").strip().lower().replace(" ", "_")
    if raw in _VALID_GUIDANCE:
        guidance = raw
        source = "gpt"
    else:
        guidance = default_guidance_for_type(
            news_type, impact_horizon=impact_horizon, volatility=volatility
        )
        source = "default_by_type"

    if news_type in {"central_bank_speech", "policy_signal", "analyst_note", "structural_theme"}:
        if guidance == "follow":
            return "wait_confirmation" if news_type != "analyst_note" else "fade", "type_override"
    if news_type == "analyst_note" and guidance == "follow":
        return "fade", "type_override"
    if impact_horizon == "structural" and guidance == "follow":
        return "wait_confirmation", "horizon_override"
    return guidance, source


def _align_horizon_for_news_type(news_type: str, impact_horizon: str) -> str:
    if news_type in {"policy_signal", "structural_theme"} and impact_horizon == "intraday":
        return "multi_day"
    if news_type == "structural_theme" and impact_horizon == "multi_day":
        return "structural"
    return impact_horizon


def apply_news_classification(
    payload: Dict[str, Any],
    *,
    news_item: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    out = dict(payload)
    text = _combined_text(out, news_item)
    horizon = str(out.get("impact_horizon") or "intraday").lower()
    volatility = str(out.get("volatility") or "medium").lower()

    news_type, type_source = _normalize_news_type(
        out.get("news_type"), text, news_item
    )
    inferred_type = infer_news_type_from_text(text, news_item=news_item)
    if type_source == "gpt" and inferred_type in {"policy_signal", "data_print"}:
        if news_type in {"other", "headline_shock"} and inferred_type != news_type:
            news_type = inferred_type
            type_source = "heuristic_override"

    horizon = _align_horizon_for_news_type(news_type, horizon)
    if horizon != out.get("impact_horizon"):
        out["impact_horizon"] = horizon
        out["impact_horizon_display"] = {
            "intraday": "Intraday reaction",
            "multi_day": "Multi-day repricing",
            "structural": "Structural / theme",
        }.get(horizon, horizon)

    guidance, guidance_source = _normalize_guidance(
        out.get("initial_reaction_guidance"),
        news_type,
        horizon,
        volatility,
    )

    type_rationale = str(out.get("news_type_rationale") or "").strip()
    if not type_rationale:
        type_rationale = f"Classified as {_NEWS_TYPE_DISPLAY.get(news_type, news_type).lower()} from headline and narrative cues."

    guidance_rationale = str(out.get("initial_reaction_guidance_rationale") or "").strip()
    if not guidance_rationale:
        guidance_rationale = _DEFAULT_GUIDANCE_RATIONALE.get(guidance, _DEFAULT_GUIDANCE_RATIONALE["wait_confirmation"])

    out["news_type"] = news_type
    out["news_type_display"] = build_news_type_display(news_type, horizon)
    out["news_type_rationale"] = type_rationale
    out["initial_reaction_guidance"] = guidance
    out["initial_reaction_guidance_display"] = _GUIDANCE_DISPLAY.get(guidance, guidance)
    out["initial_reaction_guidance_rationale"] = guidance_rationale

    out["news_classification_applied"] = {
        "surface": "live_news",
        "news_type": news_type,
        "news_type_source": type_source,
        "initial_reaction_guidance": guidance,
        "guidance_source": guidance_source,
        "impact_horizon_aligned": horizon == str(payload.get("impact_horizon") or "intraday").lower(),
    }
    return out


def apply_news_classification_if_news(
    payload: Dict[str, Any],
    analysis_kind: str,
    *,
    news_item: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if analysis_kind != ANALYSIS_KIND_LIVE_NEWS:
        return dict(payload)
    return apply_news_classification(payload, news_item=news_item)
