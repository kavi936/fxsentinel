#!/usr/bin/env python3
"""
Shared AnalysisContextPack for calendar, live news, and holistic scan surfaces.

Phase B: build structured context once per analysis request; prompts consume
`render_pack_for_prompt()` in later phases (C/D). See ANALYSIS_INPUT_LAYER.md.
"""

from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from services.analysis_personalization import get_user_personalization, prioritize_instruments
from services.relevant_market_context import build_market_snapshot_dict

logger = logging.getLogger(__name__)

PACK_VERSION = "2026-05-18"
HOLISTIC_MAX_AGE_HOURS = 72

SURFACE_CALENDAR = "calendar_event"
SURFACE_LIVE_NEWS = "live_news"
SURFACE_ECONOMY_SCAN = "economy_scan"
VALID_SURFACES = {SURFACE_CALENDAR, SURFACE_LIVE_NEWS, SURFACE_ECONOMY_SCAN}

CURRENCY_TO_COUNTRY: Dict[str, str] = {
    "USD": "US",
    "EUR": "EUR",
    "GBP": "GBP",
    "JPY": "JPY",
    "AUD": "AUD",
    "CAD": "CAD",
    "CHF": "CHF",
    "NZD": "NZD",
}

COUNTRY_TO_CURRENCY: Dict[str, str] = {
    "US": "USD",
    "EUR": "EUR",
    "GBP": "GBP",
    "JPY": "JPY",
}

COUNTRY_LABELS: Dict[str, str] = {
    "US": "United States",
    "EUR": "Euro area",
    "GBP": "United Kingdom",
    "JPY": "Japan",
}

COMMODITY_CRYPTO_IDS = frozenset(
    {
        "GOLD",
        "SILVER",
        "XAUUSD",
        "XAGUSD",
        "BTCUSDT",
        "ETHUSDT",
        "USOIL",
    }
)

GEO_HEADLINE_KEYWORDS = (
    "oil",
    "crude",
    "hormuz",
    "iran",
    "israel",
    "geopolit",
    "war",
    "conflict",
    "energy",
    "opec",
    "sanction",
    "middle east",
)

DEFAULT_MARKET_LIMIT = {
    SURFACE_CALENDAR: 8,
    SURFACE_LIVE_NEWS: 8,
    SURFACE_ECONOMY_SCAN: 6,
}


def is_analysis_context_pack_enabled() -> bool:
    return os.environ.get("ANALYSIS_CONTEXT_PACK_ENABLED", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def should_include_holistic_macro() -> bool:
    if not is_analysis_context_pack_enabled():
        return False
    return os.environ.get("ANALYSIS_CONTEXT_PACK_INCLUDE_HOLISTIC", "true").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def _parse_utc_datetime(raw: Any) -> Optional[datetime]:
    if raw is None:
        return None
    if isinstance(raw, datetime):
        dt = raw
    elif isinstance(raw, str) and raw.strip():
        try:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _hours_since(dt: Optional[datetime], now: Optional[datetime] = None) -> Optional[float]:
    if dt is None:
        return None
    ref = now or datetime.now(timezone.utc)
    return max(0.0, (ref - dt).total_seconds() / 3600.0)


def resolve_subject(
    *,
    subject_currency: Optional[str] = None,
    subject_country_code: Optional[str] = None,
) -> Dict[str, Optional[str]]:
    cc = (subject_country_code or "").strip().upper() or None
    cur = (subject_currency or "").strip().upper() or None
    if cc and not cur:
        cur = COUNTRY_TO_CURRENCY.get(cc, cc)
    if cur and not cc:
        cc = CURRENCY_TO_COUNTRY.get(cur, cur)
    economy_label = COUNTRY_LABELS.get(cc or "", None) if cc else None
    if not economy_label and cur:
        economy_label = cur
    return {
        "currency": cur,
        "country_code": cc,
        "economy_label": economy_label,
    }


def _build_user_section(user_id: Optional[str]) -> Dict[str, Any]:
    p = get_user_personalization(user_id)
    return {
        "profile_available": bool(p.get("profile_available")),
        "trading_style": p.get("trading_style", "unsure"),
        "experience_level": p.get("experience_level", "intermediate"),
        "primary_goal": p.get("primary_goal", "stay_informed"),
        "primary_pairs": list(p.get("primary_pairs") or [])[:24],
        "analysis_depth": p.get("analysis_depth", "balanced"),
        "time_horizon_bias": p.get("time_horizon_bias", "balanced"),
        "default_feature_emphasis": p.get("default_feature_emphasis", "overview"),
        "education_mode": p.get("education_mode", "standard"),
    }


def _preferred_instruments_for_surface(
    personalization: Dict[str, Any],
    *,
    surface: str,
    subject_currency: Optional[str],
    context_text: str,
) -> List[str]:
    pairs = list(personalization.get("primary_pairs") or [])
    if surface == SURFACE_CALENDAR:
        # Calendar: user pairs + commodities they trade (gold/crypto) when relevant.
        expanded: List[str] = []
        for p in pairs:
            norm = re.sub(r"[^A-Z0-9]", "", (p or "").upper())
            if norm:
                expanded.append(norm)
            if norm in ("XAUUSD", "GOLD"):
                expanded.append("GOLD")
            if norm in ("XAGUSD", "SILVER"):
                expanded.append("SILVER")
            if "BTC" in norm:
                expanded.append("BTCUSDT")
            if "ETH" in norm:
                expanded.append("ETHUSDT")
        return prioritize_instruments(expanded, expanded, limit=12)
    # News: hard steer — user pairs first (focus instruments added by caller).
    if surface == SURFACE_LIVE_NEWS:
        return pairs[:12]
    return pairs[:12]


def _market_surface_key(surface: str) -> str:
    if surface == SURFACE_CALENDAR:
        return "calendar"
    if surface == SURFACE_LIVE_NEWS:
        return "news"
    return "generic"


def _detect_market_session() -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    utc_day = now.weekday()
    utc_month = now.month
    utc_date = now.day
    is_weekend = utc_day >= 5
    is_holiday = (
        (utc_month == 1 and utc_date == 1)
        or (utc_month == 12 and utc_date == 25)
        or (utc_month == 12 and utc_date == 26)
    )
    if is_weekend or is_holiday:
        return {
            "market_session": "closed",
            "active_sessions": [],
            "notes": ["Major FX cash session closed (weekend or holiday)."],
        }

    utc_hour = now.hour
    sessions = [
        {"name": "Sydney", "start": 22, "end": 7},
        {"name": "Tokyo", "start": 0, "end": 9},
        {"name": "London", "start": 8, "end": 17},
        {"name": "New York", "start": 13, "end": 22},
    ]
    active: List[str] = []
    for session in sessions:
        if session["start"] <= session["end"]:
            is_active = session["start"] <= utc_hour < session["end"]
        else:
            is_active = utc_hour >= session["start"] or utc_hour < session["end"]
        if is_active:
            active.append(session["name"])

    if not active:
        return {
            "market_session": "closed",
            "active_sessions": [],
            "notes": ["No major FX session active at request time (UTC)."],
        }
    return {
        "market_session": "open",
        "active_sessions": active,
        "notes": [],
    }


def _level_anchor_policy(market_session: str) -> str:
    if market_session == "closed":
        return "illustrative"
    if market_session == "open":
        return "anchored"
    return "unavailable"


def _data_quality_from_market(market_snapshot: Dict[str, Any]) -> Tuple[str, List[str]]:
    instruments = market_snapshot.get("instruments") or []
    if not instruments:
        return "unknown", ["No live instrument quotes available."]
    scores = [float(i.get("freshness_score") or 0.0) for i in instruments if isinstance(i, dict)]
    avg = sum(scores) / len(scores) if scores else 0.0
    notes: List[str] = []
    if avg < 0.55:
        notes.append("Some market quotes are stale (>30–120m); treat levels as indicative.")
        return "stale", notes
    if avg < 0.8:
        return "partial", notes
    return "validated", notes


def extract_macro_snapshot_from_scan(
    scan: Dict[str, Any],
    *,
    scanned_at: Optional[datetime] = None,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
  Compact macro summary for cross-surface prompts (H2 write-through target).
    """
    short = scan.get("short_term") or {}
    long_term = scan.get("long_term") or {}
    event_flags = scan.get("event_flags") or {}
    trader_brief = scan.get("trader_brief") or {}

    geo_risk = "low"
    for item in scan.get("highlights") or []:
        if not isinstance(item, dict):
            continue
        if item.get("id") != "geopolitical_energy":
            continue
        sev = str(item.get("emphasis") or "").strip().lower()
        if sev in ("elevated", "high", "severe", "watch"):
            geo_risk = "elevated" if sev in ("elevated", "high", "severe") else "low"
        break

    pair_rows = scan.get("fx_pairs") or scan.get("pair_setups") or []
    top_pairs: List[Dict[str, Any]] = []
    for row in pair_rows[:2]:
        if not isinstance(row, dict):
            continue
        top_pairs.append(
            {
                "pair": row.get("pair"),
                "bias": row.get("bias"),
                "strength": row.get("strength"),
            }
        )

    one_line = str(trader_brief.get("short_term_line") or "").strip()
    key_risk = str(trader_brief.get("key_risk") or "").strip()
    if key_risk:
        one_line = f"{one_line} Key risk: {key_risk}".strip()

    ts = scanned_at or _parse_utc_datetime(scan.get("timestamp"))
    freshness_hours = _hours_since(ts, now=now)

    return {
        "source": "holistic_scan",
        "country_code": (scan.get("country") or "").upper() or None,
        "freshness_hours": round(freshness_hours, 2) if freshness_hours is not None else None,
        "short_term_bias": short.get("bias"),
        "short_term_score": short.get("score"),
        "short_term_confidence": short.get("confidence"),
        "long_term_bias": long_term.get("bias"),
        "long_term_score": long_term.get("score"),
        "long_term_confidence": long_term.get("confidence"),
        "calendar_stress_14d": event_flags.get("calendar_stress_score"),
        "geopolitical_energy_risk": geo_risk,
        "one_line_summary": one_line or None,
        "regime_strip": {
            "short_term": {
                "bias": short.get("bias"),
                "score": short.get("score"),
                "confidence": short.get("confidence"),
            },
            "long_term": {
                "bias": long_term.get("bias"),
                "score": long_term.get("score"),
                "confidence": long_term.get("confidence"),
            },
        },
        "top_pair_biases": top_pairs,
    }


def _load_fresh_holistic_macro(
    token_user_info: Optional[Dict[str, Any]],
    country_code: Optional[str],
    *,
    max_age_hours: float = HOLISTIC_MAX_AGE_HOURS,
    now: Optional[datetime] = None,
) -> Optional[Dict[str, Any]]:
    if not token_user_info or not country_code:
        return None
    try:
        from services.economy_holistic_scan_store import economy_holistic_scan_store

        recent = economy_holistic_scan_store.get_recent_holistic_scans(
            user_info=token_user_info,
            limit=1,
            country_code=country_code.upper(),
        )
        if not recent:
            return None
        record = recent[0] or {}
        snap = record.get("scan_snapshot") or {}
        if not snap:
            return None
        scanned_at = _parse_utc_datetime(record.get("created_at")) or _parse_utc_datetime(
            snap.get("timestamp")
        )
        freshness = _hours_since(scanned_at, now=now)
        if freshness is None or freshness > max_age_hours:
            return None
        macro = extract_macro_snapshot_from_scan(snap, scanned_at=scanned_at, now=now)
        macro["scan_id"] = record.get("id")
        macro["scanned_at_utc"] = scanned_at.isoformat() if scanned_at else None
        return macro
    except Exception as err:
        logger.debug("Holistic macro snapshot unavailable: %s", err)
        return None


def _news_bias_from_reaction(immediate_reaction: str) -> str:
    r = (immediate_reaction or "").lower()
    if r == "bullish_usd":
        return "bullish"
    if r == "bearish_usd":
        return "bearish"
    return "neutral"


def _text_has_geo_risk(text: str) -> bool:
    t = (text or "").lower()
    return any(k in t for k in GEO_HEADLINE_KEYWORDS)


def build_cross_surface_notes(
    *,
    surface: str,
    macro_snapshot: Optional[Dict[str, Any]],
    area_facts: Optional[Dict[str, Any]] = None,
) -> Dict[str, Optional[str]]:
    """
    Reconciliation hints for news vs holistic (§8.6). Calendar may use macro only.
    """
    out: Dict[str, Optional[str]] = {
        "related_headline_hint": None,
        "holistic_vs_headline_note": None,
    }
    if not macro_snapshot or macro_snapshot.get("source") == "none":
        return out

    facts = area_facts or {}
    if surface != SURFACE_LIVE_NEWS:
        return out

    headline = str(facts.get("headline") or "")
    body = str(facts.get("body_excerpt") or facts.get("summary") or "")
    combined = f"{headline} {body}".strip()
    if combined:
        out["related_headline_hint"] = headline[:240] if headline else combined[:240]

    scan_bias = str((macro_snapshot.get("short_term_bias") or "neutral")).lower()
    news_reaction = str(facts.get("immediate_reaction") or "neutral")
    news_bias = _news_bias_from_reaction(news_reaction)
    geo = str(macro_snapshot.get("geopolitical_energy_risk") or "low").lower()

    notes: List[str] = []

    if news_bias in ("bullish", "bearish") and scan_bias in ("bullish", "bearish") and news_bias != scan_bias:
        notes.append(
            "Cross-check: latest holistic short-term regime is "
            f"{scan_bias.upper()}, while this headline implies {news_bias.upper()} USD pressure. "
            "Reconcile explicitly; reduce conviction until confirmed."
        )
    elif news_bias in ("bullish", "bearish") and scan_bias == news_bias:
        notes.append(
            "Cross-check: headline direction aligns with the latest holistic short-term regime."
        )

    if geo == "elevated" and news_bias == "neutral" and _text_has_geo_risk(combined):
        notes.append(
            "Cross-check: holistic scan flags ELEVATED geopolitical/energy risk, but headline "
            "reads neutral for USD. Explain safe-haven vs risk-off channels; do not dismiss geo risk."
        )

    if notes:
        out["holistic_vs_headline_note"] = " ".join(notes)
    return out


def build_analysis_context_pack(
    *,
    surface: str,
    user_id: Optional[str] = None,
    token_user_info: Optional[Dict[str, Any]] = None,
    subject_currency: Optional[str] = None,
    subject_country_code: Optional[str] = None,
    context_text: str = "",
    focus_instruments: Optional[List[str]] = None,
    area_facts: Optional[Dict[str, Any]] = None,
    options: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Build the full AnalysisContextPack (shared block + caller-supplied area_facts).
    """
    if surface not in VALID_SURFACES:
        raise ValueError(f"Invalid surface '{surface}'; expected one of {sorted(VALID_SURFACES)}")

    opts = options or {}
    now = opts.get("now_utc")
    if now is not None and not isinstance(now, datetime):
        now = _parse_utc_datetime(now)
    if now is None:
        now = datetime.now(timezone.utc)

    subject = resolve_subject(
        subject_currency=subject_currency,
        subject_country_code=subject_country_code,
    )
    user = _build_user_section(user_id)
    preferred = _preferred_instruments_for_surface(
        user,
        surface=surface,
        subject_currency=subject.get("currency"),
        context_text=context_text,
    )

    market_limit = int(opts.get("market_limit") or DEFAULT_MARKET_LIMIT.get(surface, 8))
    market_snapshot = build_market_snapshot_dict(
        currency=subject.get("currency"),
        text=context_text,
        focus_instruments=focus_instruments,
        preferred_instruments=preferred,
        limit=market_limit,
        surface=_market_surface_key(surface),
    )

    session_info = _detect_market_session()
    market_session = session_info.get("market_session", "unknown")
    quality_notes: List[str] = list(session_info.get("notes") or [])
    data_quality, market_quality_notes = _data_quality_from_market(market_snapshot)
    quality_notes.extend(market_quality_notes)

    macro_snapshot: Optional[Dict[str, Any]] = None
    include_holistic = opts.get("include_holistic_macro")
    if include_holistic is None:
        include_holistic = should_include_holistic_macro() or bool(token_user_info)

    if include_holistic and subject.get("country_code"):
        macro_snapshot = _load_fresh_holistic_macro(
            token_user_info,
            subject["country_code"],
            max_age_hours=float(opts.get("holistic_max_age_hours") or HOLISTIC_MAX_AGE_HOURS),
            now=now,
        )
    if macro_snapshot is None:
        macro_snapshot = {
            "source": "none",
            "freshness_hours": None,
            "one_line_summary": None,
        }
        if include_holistic and subject.get("country_code"):
            quality_notes.append(
                f"No holistic scan for {subject['country_code']} within "
                f"{int(opts.get('holistic_max_age_hours') or HOLISTIC_MAX_AGE_HOURS)}h."
            )

    cross_surface = build_cross_surface_notes(
        surface=surface,
        macro_snapshot=macro_snapshot if macro_snapshot.get("source") != "none" else None,
        area_facts=area_facts,
    )

    pack: Dict[str, Any] = {
        "pack_version": PACK_VERSION,
        "surface": surface,
        "generated_at_utc": now.isoformat(),
        "user": user,
        "subject": subject,
        "macro_snapshot": macro_snapshot,
        "market_snapshot": market_snapshot,
        "session_and_quality": {
            "market_session": market_session,
            "active_sessions": session_info.get("active_sessions") or [],
            "data_quality": data_quality,
            "quality_notes": quality_notes,
            "level_anchor_policy": _level_anchor_policy(str(market_session)),
            "confidence_definition": "edge_strength",
        },
        "cross_surface": cross_surface,
        "area_facts": area_facts or {},
        "personalization_mode": _personalization_mode(surface),
    }
    return pack


def _personalization_mode(surface: str) -> str:
    if surface == SURFACE_LIVE_NEWS:
        return "hard"
    return "soft"


def shared_pack_signature(pack: Dict[str, Any]) -> Dict[str, Any]:
    """
    Comparable subset for tests: shared context should match across surfaces
    for the same user/subject when built with the same options.
    """
    return {
        "pack_version": pack.get("pack_version"),
        "user": pack.get("user"),
        "subject": pack.get("subject"),
        "macro_snapshot": pack.get("macro_snapshot"),
        "session_and_quality": {
            "market_session": (pack.get("session_and_quality") or {}).get("market_session"),
            "level_anchor_policy": (pack.get("session_and_quality") or {}).get("level_anchor_policy"),
            "confidence_definition": (pack.get("session_and_quality") or {}).get("confidence_definition"),
        },
    }


def render_pack_for_prompt(
    pack: Dict[str, Any],
    *,
    max_tokens_hint: Optional[int] = None,
) -> str:
    """
    Render AnalysisContextPack as a prompt block (Phase C/D will call this).
    """
    _ = max_tokens_hint  # reserved for truncation ranking
    surface = pack.get("surface", "generic")
    user = pack.get("user") or {}
    subject = pack.get("subject") or {}
    macro = pack.get("macro_snapshot") or {}
    market = pack.get("market_snapshot") or {}
    session = pack.get("session_and_quality") or {}
    cross = pack.get("cross_surface") or {}
    mode = pack.get("personalization_mode") or _personalization_mode(surface)

    lines: List[str] = [
        f"ANALYSIS CONTEXT PACK ({surface}) v{pack.get('pack_version')}",
        "",
        "USER PROFILE:",
        f"- Trading style: {user.get('trading_style')}",
        f"- Experience: {user.get('experience_level')}",
        f"- Preferred pairs: {', '.join((user.get('primary_pairs') or [])[:8]) or 'none'}",
        f"- Analysis depth: {user.get('analysis_depth')}",
        f"- Time horizon bias: {user.get('time_horizon_bias')}",
        "",
        "SUBJECT:",
        f"- Currency: {subject.get('currency')}",
        f"- Economy: {subject.get('economy_label') or subject.get('country_code')}",
        "",
    ]

    if macro.get("source") == "holistic_scan":
        lines.extend(
            [
                "MACRO SNAPSHOT (latest holistic scan):",
                f"- Short-term: {(macro.get('short_term_bias') or 'n/a').upper()} "
                f"(score {macro.get('short_term_score')}, conf {macro.get('short_term_confidence')}%)",
                f"- Long-term: {(macro.get('long_term_bias') or 'n/a').upper()} "
                f"(score {macro.get('long_term_score')}, conf {macro.get('long_term_confidence')}%)",
                f"- Calendar stress (14d): {macro.get('calendar_stress_14d')}",
                f"- Geopolitical/energy: {(macro.get('geopolitical_energy_risk') or 'n/a').upper()}",
                f"- Summary: {macro.get('one_line_summary') or 'n/a'}",
                f"- Freshness: {macro.get('freshness_hours')}h ago",
                "",
            ]
        )
        top_pairs = macro.get("top_pair_biases") or []
        if top_pairs:
            lines.append("TOP PAIR BIASES FROM SCAN:")
            for row in top_pairs:
                lines.append(
                    f"- {row.get('pair')}: {(row.get('bias') or 'neutral').upper()} ({row.get('strength')})"
                )
            lines.append("")

    lines.append("MARKET SNAPSHOT:")
    instruments = market.get("instruments") or []
    if not instruments:
        lines.append("- No live quotes available.")
    else:
        for inst in instruments:
            chg_pct = inst.get("change_pct")
            pct_str = f"{chg_pct:+.2f}%" if isinstance(chg_pct, (int, float)) else "n/a"
            lines.append(
                f"- {inst.get('label')} [{inst.get('id')}]: price={inst.get('price')}, "
                f"daily_change_pct={pct_str}"
            )
    lines.append("")

    lines.extend(
        [
            "SESSION & DATA QUALITY:",
            f"- Market session: {session.get('market_session')}",
            f"- Level policy: {session.get('level_anchor_policy')} "
            "(illustrative when closed — not live trade signals)",
            f"- Data quality: {session.get('data_quality')}",
            f"- Confidence means: edge strength (what supports vs negates the idea)",
        ]
    )
    for note in session.get("quality_notes") or []:
        lines.append(f"- Note: {note}")

    if cross.get("holistic_vs_headline_note"):
        lines.extend(["", "CROSS-SURFACE:", f"- {cross['holistic_vs_headline_note']}"])

    lines.extend(
        [
            "",
            "PERSONALIZATION MODE:",
            f"- {mode.upper()}: "
            + (
                "Prioritize user onboarding pairs; only broaden to macro movers if headline forces it."
                if mode == "hard"
                else "Cover economy-linked instruments; prefer user pairs when relevant."
            ),
        ]
    )

    if session.get("market_session") == "closed":
        lines.extend(
            [
                "",
                "CLOSED MARKET RULES:",
                "- Frame for when major FX cash reopens; crypto may still trade 24/7.",
                "- Price levels are illustrative (~round levels, % moves), not live entries.",
            ]
        )

    return "\n".join(lines)
