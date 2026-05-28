#!/usr/bin/env python3
"""
Holistic score ↔ narrative bridge (review priority #10).

When curated geo severity is CRITICAL or ELEVATED but the deterministic composite
score sits in (or near) the neutral band, traders need an explicit sentence linking
theme severity to driver offsets — without changing scores or biases.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

ELEVATED_GEO_SEVERITIES = frozenset({"CRITICAL", "ELEVATED"})

SCORE_BRIDGE_PROMPT_RULES = """
SCORE ↔ NARRATIVE BRIDGE (mandatory when payload.score_bridge_required is true):
- Curated geopolitical severity is CRITICAL or ELEVATED while the short-term composite may still read neutral or only a lean.
- Include narrative.score_bridge OR weave into narrative.geopolitical_energy / narrative.short_term one explicit bridge sentence.
- Template: "[[Theme title]] is **CRITICAL/ELEVATED**, but the short-term composite stays **{display_bias}** (score **{score}**) because **{driver A}** ({contribution A}) is partly offset by **{driver B}** ({contribution B}) — net effect keeps the regime from a full risk-off read."
- Reference at least two driver names from payload.short_term.component_breakdown.drivers (use contribution_display values; do not invent weights).
- Do not change deterministic scores, biases, or confidence.
""".strip()

_BRIDGE_PHRASE_RE = re.compile(
    r"(composite\s+score|short[- ]term\s+composite|offsets?|offset\s+by|net\s+effect|"
    r"neutral\s+band|because\s+.+\s+partly)",
    re.IGNORECASE,
)


def requires_score_bridge(geo_severity: Optional[str]) -> bool:
    return str(geo_severity or "").strip().upper() in ELEVATED_GEO_SEVERITIES


def _driver_rows(short_term: Dict[str, Any]) -> List[Dict[str, Any]]:
    breakdown = short_term.get("component_breakdown") or {}
    drivers = breakdown.get("drivers") if isinstance(breakdown, dict) else None
    if not isinstance(drivers, list):
        return []
    return [d for d in drivers if isinstance(d, dict) and d.get("available", True)]


def top_offset_drivers(short_term: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """
    Pick the strongest positive and negative contributors for bridge copy.
    Falls back to top two by |contribution| when one side is missing.
    """
    rows = _driver_rows(short_term)
    if not rows:
        return None, None

    positive = [r for r in rows if float(r.get("contribution") or 0.0) > 0.01]
    negative = [r for r in rows if float(r.get("contribution") or 0.0) < -0.01]
    pos = max(positive, key=lambda r: float(r.get("contribution") or 0.0), default=None)
    neg = min(negative, key=lambda r: float(r.get("contribution") or 0.0), default=None)
    if pos and neg:
        return pos, neg

    ranked = sorted(rows, key=lambda r: abs(float(r.get("contribution") or 0.0)), reverse=True)
    if len(ranked) >= 2:
        return ranked[0], ranked[1]
    if ranked:
        return ranked[0], None
    return None, None


def _primary_theme_title(curated_overlay: Dict[str, Any]) -> str:
    themes = curated_overlay.get("global_themes") or curated_overlay.get("theme_digest") or []
    if isinstance(themes, list) and themes:
        first = themes[0]
        if isinstance(first, dict):
            return str(first.get("title") or "Macro risk theme").strip()
    return "Macro risk theme"


def build_score_bridge_sentence(scan: Dict[str, Any]) -> Optional[str]:
    curated = scan.get("curated_macro_overlay") or {}
    if not requires_score_bridge(curated.get("geo_severity")):
        return None

    short_term = scan.get("short_term") or {}
    pos, neg = top_offset_drivers(short_term)
    if not pos:
        return None

    theme = _primary_theme_title(curated)
    severity = str(curated.get("geo_severity") or "ELEVATED").upper()
    score = short_term.get("score")
    display = short_term.get("display_bias") or short_term.get("position_label") or "neutral"
    band = short_term.get("position_label") or display

    pos_name = str(pos.get("name") or "driver")
    pos_disp = str(pos.get("contribution_display") or f"{float(pos.get('contribution') or 0):+.1f}")

    if neg:
        neg_name = str(neg.get("name") or "counter-driver")
        neg_disp = str(neg.get("contribution_display") or f"{float(neg.get('contribution') or 0):+.1f}")
        offset_clause = (
            f"**{pos_name}** ({pos_disp}) is partly offset by **{neg_name}** ({neg_disp})"
        )
    else:
        offset_clause = f"**{pos_name}** ({pos_disp}) dominates the available drivers"

    return (
        f"**Score bridge:** [[{theme}]] is **{severity}**, but the short-term composite reads "
        f"**{display}** (score **{score}**, {band}) because {offset_clause} — "
        f"net effect keeps the regime from a full risk-off read despite headline geo stress."
    )


def _driver_names_for_match(short_term: Dict[str, Any]) -> List[str]:
    names: List[str] = []
    for row in _driver_rows(short_term):
        name = str(row.get("name") or "").strip()
        if name:
            names.append(name.lower())
    return names


def _mentions_driver(text: str, driver_name: str) -> bool:
    if not driver_name:
        return False
    lowered = text.lower()
    tokens = [t for t in re.split(r"[\s/&-]+", driver_name.lower()) if len(t) >= 4]
    if driver_name.lower() in lowered:
        return True
    return any(tok in lowered for tok in tokens)


def has_score_bridge_language(text: str, short_term: Dict[str, Any]) -> bool:
    if not text or not text.strip():
        return False
    if not _BRIDGE_PHRASE_RE.search(text):
        return False
    names = _driver_names_for_match(short_term)
    if len(names) < 2:
        return bool(names) and _mentions_driver(text, names[0])
    mentioned = sum(1 for n in names if _mentions_driver(text, n))
    return mentioned >= 2


def validate_score_bridge_in_generated(
    generated: Dict[str, Any],
    scan: Dict[str, Any],
) -> Tuple[bool, Optional[str]]:
    curated = scan.get("curated_macro_overlay") or {}
    if not requires_score_bridge(curated.get("geo_severity")):
        return True, None

    narrative = generated.get("narrative") or {}
    parts = [
        str(narrative.get("score_bridge") or ""),
        str(narrative.get("geopolitical_energy") or ""),
        str(narrative.get("short_term") or ""),
    ]
    combined = " ".join(p for p in parts if p.strip())
    short_term = scan.get("short_term") or {}
    if has_score_bridge_language(combined, short_term):
        return True, None
    return False, "score_bridge_missing_or_weak"


def apply_score_narrative_bridge_to_scan(scan: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure CRITICAL/ELEVATED scans expose bridge copy on narrative + highlights.
    Does not mutate scores or biases.
    """
    curated = scan.get("curated_macro_overlay") or {}
    geo = curated.get("geo_severity")
    required = requires_score_bridge(geo)
    short_term = scan.get("short_term") or {}
    narrative = dict(scan.get("narrative") or {})

    existing_parts = [
        str(narrative.get("score_bridge") or ""),
        str(scan.get("score_narrative_bridge") or ""),
        str(narrative.get("geopolitical_energy") or ""),
        str(narrative.get("short_term") or ""),
    ]
    combined_existing = " ".join(p for p in existing_parts if p.strip())
    present = has_score_bridge_language(combined_existing, short_term) if required else False

    bridge_sentence = None
    source = "gpt_or_existing"
    if required and not present:
        bridge_sentence = build_score_bridge_sentence(scan)
        if bridge_sentence:
            narrative["score_bridge"] = bridge_sentence
            geo_block = str(narrative.get("geopolitical_energy") or "").strip()
            if geo_block and bridge_sentence not in geo_block:
                narrative["geopolitical_energy"] = f"{geo_block}\n\n{bridge_sentence}"
            elif not geo_block:
                narrative["geopolitical_energy"] = bridge_sentence
            scan["score_narrative_bridge"] = bridge_sentence
            source = "deterministic_fallback"
            present = True
    elif required and present:
        if narrative.get("score_bridge"):
            scan["score_narrative_bridge"] = narrative["score_bridge"]
        elif scan.get("score_narrative_bridge"):
            narrative["score_bridge"] = scan["score_narrative_bridge"]
        elif narrative.get("geopolitical_energy"):
            scan["score_narrative_bridge"] = str(narrative.get("geopolitical_energy") or "")[:480]
        source = "gpt_or_existing"

    scan["narrative"] = narrative
    scan["score_bridge_required"] = required
    scan["score_bridge_present"] = bool(present) if required else False
    scan["score_bridge_applied"] = {
        "required": required,
        "present": bool(present) if required else False,
        "source": source if required else "not_required",
        "geo_severity": str(geo or "").upper() or None,
    }

    highlight_text = (
        bridge_sentence
        or str(narrative.get("score_bridge") or "").strip()
        or str(scan.get("score_narrative_bridge") or "").strip()
    )
    if required and present and highlight_text:
        highlights = scan.get("highlights") or {}
        items = list(highlights.get("items") or [])
        if not any(item.get("id") == "score_narrative_bridge" for item in items if isinstance(item, dict)):
            insert_at = 0
            for idx, item in enumerate(items):
                if isinstance(item, dict) and item.get("id") == "geopolitical_energy":
                    insert_at = idx + 1
                    break
            items.insert(
                insert_at,
                {
                    "id": "score_narrative_bridge",
                    "label": "Why is the score still neutral?",
                    "emphasis": str(geo or "ELEVATED"),
                    "detail": highlight_text,
                },
            )
            highlights["items"] = items
            scan["highlights"] = highlights

    return scan
