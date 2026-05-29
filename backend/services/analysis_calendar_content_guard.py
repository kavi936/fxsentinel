#!/usr/bin/env python3
"""
Calendar content guard (V2 Tier 2): honest spot labels, no vague catalysts, no filler forward_focus.

Runs at finalize time — does not call GPT.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from services.analysis_contract import ANALYSIS_KIND_CALENDAR_EVENT

CALENDAR_CONTENT_GUARD_PROMPT_RULES = """
CALENDAR CONTENT GUARD (mandatory):
- trading_plan.key_levels: until structured OHLC exists, use "Spot reference:" prefix only — do NOT label spot as support/resistance/pivot/swing.
- next_catalysts: each item must name a specific event OR include a month/date (e.g. "FOMC 18 Jun", "NFP 6 Jun"). Ban always-true lines like "geopolitical developments in the Middle East".
- big_picture.forward_focus: must reference THIS release or the next dated tier-1 catalyst — no generic "monitor inflation and geopolitical developments".
""".strip()

_GENERIC_FORWARD_FOCUS_RE = re.compile(
    r"monitor\s+(upcoming\s+)?(inflation|geopolitical)|"
    r"geopolitical\s+developments(?!\s+in\s+\w+\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|\d))",
    re.IGNORECASE,
)

_VAGUE_CATALYST_RES: List[re.Pattern] = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"^geopolitical\s+developments",
        r"geopolitical\s+developments\s+in\s+the\s+middle\s+east$",
        r"^monitor\s+upcoming",
        r"^watch\s+(for\s+)?developments",
        r"^central\s+bank\s+meetings\s+and\s+related",
        r"^focus\s+on\s+upcoming",
    )
]

_DATE_IN_TEXT_RE = re.compile(
    r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|"
    r"january|february|march|april|may|june|july|august|september|october|november|december|"
    r"\d{1,2}\s*[/-]\s*\d{1,2}|\d{4}|q[1-4])\b",
    re.IGNORECASE,
)

_SPECIFIC_EVENT_RE = re.compile(
    r"\b(fomc|nfp|non-?farm|cpi|pce|gdp|pmi|ecb|fed|boe|boj|rate\s+decision|"
    r"employment|payrolls|retail\s+sales|ism)\b",
    re.IGNORECASE,
)

_SPOT_LEVEL_RE = re.compile(
    r"anchored\s+to\s+(current\s+)?spot|current\s+spot|spot\s+reference|illustrative\s+levels",
    re.IGNORECASE,
)

_FORBIDDEN_LEVEL_CLAIM_RE = re.compile(
    r"\b(prior\s+)?(support|resistance|pivot|swing)\b",
    re.IGNORECASE,
)


def _is_vague_catalyst(text: str) -> bool:
    raw = str(text or "").strip()
    if not raw or len(raw) < 8:
        return True
    if any(p.search(raw) for p in _VAGUE_CATALYST_RES):
        if not _DATE_IN_TEXT_RE.search(raw) and not _SPECIFIC_EVENT_RE.search(raw):
            return True
    return False


def _is_generic_forward_focus(text: str) -> bool:
    raw = str(text or "").strip()
    if not raw:
        return False
    if _GENERIC_FORWARD_FOCUS_RE.search(raw):
        return True
    lowered = raw.lower()
    if "monitor" in lowered and "inflation" in lowered and "geopolitical" in lowered:
        return True
    return False


def _event_specific_forward_focus(event: Dict[str, Any], kept_catalysts: List[str]) -> str:
    title = str(event.get("title") or "this release").strip()
    currency = str(event.get("currency") or "USD").upper()
    if kept_catalysts:
        next_item = kept_catalysts[0]
        return (
            f"After {title}, focus on {next_item} for {currency} repricing confirmation or fade."
        )
    return (
        f"After {title}, watch the next tier-1 {currency} data print for confirmation of this read."
    )


def _honest_key_levels(plan: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    actions: List[str] = []
    out = dict(plan)
    raw = str(out.get("key_levels") or "").strip()
    if not raw:
        return out, actions

    is_spot_anchor = bool(_SPOT_LEVEL_RE.search(raw))
    has_structure_claim = bool(_FORBIDDEN_LEVEL_CLAIM_RE.search(raw)) and not raw.lower().startswith(
        "illustrative"
    )

    if is_spot_anchor or (has_structure_claim and not raw.lower().startswith("illustrative levels")):
        out["key_levels_label"] = "Spot reference"
        if not raw.lower().startswith("spot reference"):
            if raw.lower().startswith("illustrative levels"):
                out["key_levels"] = raw.replace("Illustrative levels:", "Spot reference:", 1).replace(
                    "illustrative levels:", "Spot reference:", 1
                )
            else:
                out["key_levels"] = f"Spot reference: {raw}"
            actions.append("key_levels_relabeled_spot_reference")
        else:
            out["key_levels_label"] = "Spot reference"
    else:
        out["key_levels_label"] = out.get("key_levels_label") or "Levels (check basis in text)"

    return out, actions


def apply_calendar_content_guard(
    payload: Dict[str, Any],
    *,
    event: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Sanitize calendar copy for Tier-2 clarity; attach QA metadata."""
    out = dict(payload)
    ev = event or {}
    enforcement: List[str] = []
    checks: List[Dict[str, Any]] = []

    plan = out.get("trading_plan")
    if isinstance(plan, dict):
        new_plan, plan_actions = _honest_key_levels(plan)
        out["trading_plan"] = new_plan
        enforcement.extend(plan_actions)

    catalysts = out.get("next_catalysts")
    if isinstance(catalysts, list):
        kept: List[str] = []
        removed: List[str] = []
        for item in catalysts:
            text = str(item or "").strip()
            if not text:
                continue
            if _is_vague_catalyst(text):
                removed.append(text)
            else:
                kept.append(text)
        if removed:
            enforcement.append(f"removed_vague_catalysts:{len(removed)}")
        out["next_catalysts"] = kept
        out["next_catalysts_removed"] = removed

    bp = out.get("big_picture")
    if isinstance(bp, dict):
        bp = dict(bp)
        ff = str(bp.get("forward_focus") or "").strip()
        if ff and _is_generic_forward_focus(ff):
            kept_cat = out.get("next_catalysts") if isinstance(out.get("next_catalysts"), list) else []
            bp["forward_focus"] = _event_specific_forward_focus(ev, kept_cat)
            bp["forward_focus_replaced"] = True
            enforcement.append("forward_focus_replaced_generic")
        out["big_picture"] = bp

    out["calendar_content_guard_applied"] = {
        "surface": "economic_calendar",
        "enforcement_actions": enforcement,
        "checks": checks,
    }
    return out


def apply_calendar_content_guard_if_calendar(
    payload: Dict[str, Any],
    analysis_kind: str,
    *,
    event: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if analysis_kind != ANALYSIS_KIND_CALENDAR_EVENT:
        return dict(payload)
    return apply_calendar_content_guard(payload, event=event)
