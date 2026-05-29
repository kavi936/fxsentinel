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

# Severities that imply elevated geopolitical/energy risk in macro_snapshot + cross-checks.
_GEO_ELEVATED_SEVERITIES = frozenset({"critical", "elevated", "high", "severe"})


def geopolitical_risk_from_severity_label(severity: Optional[str]) -> str:
    """Map highlight emphasis / overlay severity to macro_snapshot geo risk."""
    sev = str(severity or "").strip().lower()
    return "elevated" if sev in _GEO_ELEVATED_SEVERITIES else "low"


def theme_digest_from_scan_highlights(scan: Dict[str, Any]) -> List[str]:
    """One-line digest per curated macro theme row in holistic highlights."""
    lines: List[str] = []
    items = scan.get("highlights") or {}
    if isinstance(items, dict):
        item_list = items.get("items") or []
    elif isinstance(items, list):
        item_list = items
    else:
        item_list = []
    for item in item_list:
        if not isinstance(item, dict):
            continue
        iid = str(item.get("id") or "")
        if iid != "geopolitical_energy" and not iid.startswith("macro_theme_"):
            continue
        label = str(item.get("label") or "Macro theme").strip()
        emphasis = str(item.get("emphasis") or "").strip().upper()
        detail = str(item.get("detail") or "").strip()
        if len(detail) > 220:
            detail = detail[:217].rstrip() + "…"
        lines.append(f"{label} [{emphasis}]: {detail}" if detail else f"{label} [{emphasis}]")
    return lines


def max_geopolitical_risk_from_highlights(scan: Dict[str, Any]) -> str:
    risk = "low"
    items = scan.get("highlights") or {}
    item_list = items.get("items") if isinstance(items, dict) else items if isinstance(items, list) else []
    for item in item_list:
        if not isinstance(item, dict):
            continue
        iid = str(item.get("id") or "")
        if iid != "geopolitical_energy" and not iid.startswith("macro_theme_"):
            continue
        if geopolitical_risk_from_severity_label(item.get("emphasis")) == "elevated":
            return "elevated"
    return risk

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

    geo_risk = max_geopolitical_risk_from_highlights(scan)
    overlay_meta = scan.get("curated_macro_overlay") or {}
    if overlay_meta.get("geo_severity"):
        geo_risk = geopolitical_risk_from_severity_label(overlay_meta.get("geo_severity"))

    theme_digest = overlay_meta.get("theme_digest")
    if not theme_digest:
        theme_digest = theme_digest_from_scan_highlights(scan)

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
        "overlay_version": overlay_meta.get("version"),
        "overlay_last_updated": overlay_meta.get("lastUpdated"),
        "primary_geo_title": overlay_meta.get("primary_geo_title"),
        "geo_severity": (overlay_meta.get("geo_severity") or "").upper() or None,
        "theme_digest": theme_digest or [],
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


def macro_snapshot_from_holistic_record(
    record: Dict[str, Any],
    *,
    now: Optional[datetime] = None,
    max_age_hours: float = HOLISTIC_MAX_AGE_HOURS,
) -> Optional[Dict[str, Any]]:
    """
    Resolve macro snapshot from a persisted holistic scan record (Phase E).

    Prefers stored ``macro_snapshot`` (H2 write-through); falls back to extracting
    from ``scan_snapshot`` for records saved before Phase E.
    """
    snap = record.get("scan_snapshot") or {}
    if not snap and not record.get("macro_snapshot"):
        return None

    scanned_at = _parse_utc_datetime(record.get("created_at")) or _parse_utc_datetime(
        snap.get("timestamp")
    )
    freshness = _hours_since(scanned_at, now=now)
    if freshness is None or freshness > max_age_hours:
        return None

    stored = record.get("macro_snapshot")
    if isinstance(stored, dict) and stored.get("source") == "holistic_scan":
        macro = dict(stored)
    else:
        macro = extract_macro_snapshot_from_scan(snap, scanned_at=scanned_at, now=now)

    macro["scan_id"] = record.get("id")
    macro["scanned_at_utc"] = scanned_at.isoformat() if scanned_at else None
    if macro.get("freshness_hours") is None and freshness is not None:
        macro["freshness_hours"] = round(freshness, 2)
    cc = (record.get("country_code") or snap.get("country") or macro.get("country_code") or "").upper()
    if cc:
        macro["country_code"] = cc
    return macro


def build_macro_snapshot_for_persist(
    scan: Dict[str, Any],
    *,
    scanned_at: Optional[datetime] = None,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Build macro snapshot blob to store alongside a holistic scan (Phase E H2)."""
    return extract_macro_snapshot_from_scan(scan, scanned_at=scanned_at, now=now)


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

        cc = country_code.upper()
        recent = economy_holistic_scan_store.get_recent_holistic_scans(
            user_info=token_user_info,
            limit=1,
            country_code=cc,
        )
        if not recent:
            return None
        return macro_snapshot_from_holistic_record(
            recent[0] or {},
            now=now,
            max_age_hours=max_age_hours,
        )
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
        if macro.get("overlay_version") or macro.get("primary_geo_title"):
            lines.extend(
                [
                    "CURATED MACRO OVERLAY (from holistic_scan_context.json):",
                    f"- Overlay version: {macro.get('overlay_version') or 'n/a'} "
                    f"(updated {macro.get('overlay_last_updated') or 'n/a'})",
                    f"- Primary geo theme: {macro.get('primary_geo_title') or 'n/a'} "
                    f"[{(macro.get('geo_severity') or 'n/a').upper()}]",
                    "",
                ]
            )
        digest = macro.get("theme_digest") or []
        if digest:
            lines.append("MACRO THEME DIGEST (from latest scan):")
            for row in digest[:6]:
                lines.append(f"- {row}")
            lines.append("")
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


def is_analysis_context_pack_debug() -> bool:
    return os.environ.get("ANALYSIS_CONTEXT_PACK_DEBUG", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def _calendar_release_status(event: Dict[str, Any]) -> str:
    actual = event.get("actual")
    if actual in ("N/A", "TBD", "", None):
        return "pre"
    return "post"


def build_calendar_area_facts(event: Dict[str, Any], analysis_type: str) -> Dict[str, Any]:
    """Area-specific facts for calendar_event surface (Phase C)."""
    from services.calendar_scenario_engine import compute_neutral_zone_range

    expected = event.get("expected") or event.get("forecast")
    scheduled = (
        event.get("scheduled_at_utc")
        or event.get("datetime_utc")
        or event.get("date")
        or event.get("time")
    )
    impact = str(event.get("impact") or "medium").strip().lower()
    if impact not in ("high", "medium", "low"):
        impact = "medium"
    release = _calendar_release_status(event)
    if analysis_type == "post_event" and release == "pre":
        release = "post"
    facts = {
        "event_id": str(event.get("id") or event.get("event_id") or ""),
        "title": str(event.get("title") or ""),
        "scheduled_at_utc": scheduled,
        "release_status": release,
        "analysis_type": analysis_type,
        "actual": event.get("actual"),
        "forecast": expected,
        "previous": event.get("previous"),
        "impact_tier": impact,
    }
    neutral_zone = compute_neutral_zone_range(expected)
    if neutral_zone:
        facts["neutral_zone"] = neutral_zone
    return facts


CALENDAR_PACK_PROMPT_RULES = """
CALENDAR CONTEXT PACK RULES (Phase F — mandatory when this pack is present):

REGIME VS EVENT (read carefully):
- Latest economy scan (MACRO SNAPSHOT block) = prevailing regime; its short-term bias/scores are authoritative for baseline tone.
- This calendar release = catalyst. forward_scenarios are conditional surprise paths (beat / miss / inline), NOT a second copy of regime.
- implications_takeaways.market_bias: start with exactly one label BULLISH | BEARISH | NEUTRAL for the event currency, then explain how the print fits the prevailing regime (e.g. bearish regime but hot CPI could still lift USD short-term).
- If regime and a high-probability scenario conflict, explain the tension in one sentence — do not ignore the scan.

TRADER-FACING LANGUAGE:
- Never write "macro snapshot" in JSON output — say "latest economy scan", "prevailing short-term bias", or "recent holistic view".
- Do not repeat "data-dependent" (or similar filler) more than once in the entire response.
- Each major section needs at least one concrete number from the pack, economy context, or event fields — no generic-only paragraphs.

CONSISTENCY:
- forward_scenarios probabilities must be single integer percentages that sum to exactly 100.
- forward_scenarios.neutral ([ON] path) must describe the **inline band** from area_facts.neutral_zone when present
  (e.g. "0.25%–0.35%"), NOT a single exact consensus tick — markets treat near-consensus as limited reaction.
- big_picture.medium_term_direction must not repeat market_bias verbatim.
- edge_confidence / analysis_confidence (High | Medium | Low) = your directional edge; edge_confidence_reason = one sentence why.
- assumptions[] only for missing data gaps (separate from edge_confidence_reason).

LEVELS & SESSION:
- If market session is closed, trading_plan.key_levels must start with "Spot reference:" or "Illustrative levels:" — never label spot as support/resistance until structured OHLC exists.
- next_catalysts: each entry must name a specific release or include a date/month; ban vague always-true geopolitical filler.
- big_picture.forward_focus: must tie to THIS event or the next dated catalyst — no generic "monitor inflation and geopolitical developments".
- Prefer user onboarding pairs when relevant; still cover economy-linked movers for this release.

PERSONALIZATION CASCADE (mandatory):
- If user.trading_style is swing: expand big_picture.medium_term_direction and forward_focus for multi-week framing; keep short-term language concise and conditional.
- If user.trading_style is day: prioritize immediate post-release reaction, trigger/invalidation logic, and session-aware execution notes.
- If user.primary_pairs is populated: prioritize those pairs in forward_scenarios/trading_plan first. If event relevance to a preferred pair is weak, say so explicitly rather than forcing a strong claim.

ACTIONABLE TRIGGERS (mandatory):
- Include at least one explicit "If [trigger] → then [FX outcome]" in trading_plan.best_approach and in each forward_scenarios path.
- Ban passive-only lines ("monitor", "watch closely", "remain vigilant") without a linked trigger.
- Example: "If Core PCE beats 0.3%, expect EUR/USD to test 1.1580; a break below 1.1520 would invalidate the USD-bullish follow-through."

TRADING PLAN STRUCTURE (mandatory):
- trading_plan should be execution-ready, not generic advice.
- Include: trigger, direction (pair + long/short), entry condition, target zone, invalidation, sizing note.
- Use conditional phrasing if levels are uncertain; do not omit invalidation logic.

NEUTRAL SUB-CLASSIFICATION (mandatory):
- implications_takeaways.market_bias must start with BULLISH | BEARISH | NEUTRAL for the event currency.
- If drivers are balanced but tilt one way, use NEUTRAL · BULLISH LEAN or NEUTRAL · BEARISH LEAN (not plain NEUTRAL).
- Use TRUE NEUTRAL only when there is no readable lean in scenarios or narrative.
""".strip()

try:
    from services.analysis_calendar_content_guard import CALENDAR_CONTENT_GUARD_PROMPT_RULES as _CAL_GUARD
except ImportError:
    _CAL_GUARD = ""
if _CAL_GUARD:
    CALENDAR_PACK_PROMPT_RULES = f"{CALENDAR_PACK_PROMPT_RULES}\n\n{_CAL_GUARD}"


def calendar_forward_scenarios_json_spec(currency: str, *, is_pre_event: bool) -> str:
    """Phase F: use bullish/bearish/neutral keys with explicit surprise-path framing."""
    event_frame = (
        "expected vs previous and current indicators"
        if is_pre_event
        else "actual vs expected and policy implications"
    )
    return f"""
    "forward_scenarios": {{
        "bullish": "[ABOVE] <INT>%: {currency} strength path as a conditional surprise outcome if print is above forecast. Use one integer probability; include FX pairs/direction and why vs {event_frame}.",
        "bearish": "[BELOW] <INT>%: {currency} weakness path as a conditional surprise outcome if print is below forecast. Use one integer probability; include FX pairs/direction and why.",
        "neutral": "[ON] <INT>%: inline/surprise-on-forecast path when print falls in the neutral_zone band from context (not a single exact tick). Use one integer probability and why reaction may be muted."
    }},
""".strip()


def build_calendar_context_pack_section(
    event: Dict[str, Any],
    analysis_type: str,
    *,
    user_id: Optional[str] = None,
    token_user_info: Optional[Dict[str, Any]] = None,
    focus_instruments: Optional[List[str]] = None,
) -> Tuple[Dict[str, Any], str]:
    """
    Build AnalysisContextPack + prompt block for calendar enhanced analysis (Phase C).
    """
    area_facts = build_calendar_area_facts(event, analysis_type)
    currency = str(event.get("currency") or "USD").upper()
    title = str(event.get("title") or "")
    pack = build_analysis_context_pack(
        surface=SURFACE_CALENDAR,
        user_id=user_id,
        token_user_info=token_user_info,
        subject_currency=currency,
        context_text=title,
        focus_instruments=focus_instruments,
        area_facts=area_facts,
        options={"include_holistic_macro": True},
    )
    from services.analysis_calendar_confidence import CALENDAR_CONFIDENCE_PROMPT_RULES

    block = render_pack_for_prompt(pack) + "\n\n" + CALENDAR_PACK_PROMPT_RULES + "\n\n" + CALENDAR_CONFIDENCE_PROMPT_RULES
    if is_analysis_context_pack_debug():
        logger.info("Calendar context pack built for event=%s", area_facts.get("event_id") or title)
    return pack, block


# ---------------------------------------------------------------------------
# Phase D — Live news context pack helpers
# ---------------------------------------------------------------------------

NEWS_PACK_PROMPT_RULES = """
LIVE NEWS CONTEXT PACK RULES (Phase F — mandatory when this pack is present):

HEADLINE & INSTRUMENTS:
- Lead with the primary affected instrument (XAU/USD for gold, not USD/JPY by default).
- Hard personalization: user onboarding pairs must appear in key_pairs when relevant to the headline.

REGIME VS HEADLINE:
- If latest economy scan (MACRO SNAPSHOT) is present, state whether the headline aligns or challenges prevailing short-term bias in news_impact (one clear sentence).
- Never write "macro snapshot" in output — use "latest economy scan" or "prevailing short-term bias".
- Do not repeat "data-dependent" or generic safe-haven boilerplate more than once.

CONFIDENCE & LEVELS:
- confidence (50-95) = edge strength: what supports the read vs what could negate it (mention in trading_implications).
- If market session is closed, all levels are illustrative; say so explicitly.
- Cite at least one concrete input from the pack (VIX, pair move, scan bias, geo flag) in each paragraph.

CROSS-SURFACE:
- If CROSS-SURFACE note is present in the pack, address it in news_impact or trading_implications.

PERSONALIZATION CASCADE (mandatory):
- If user.trading_style is swing: emphasize multi-session follow-through and invalidation conditions; avoid scalper-style micro timing language.
- If user.trading_style is day: emphasize next-session trigger conditions and immediate risk controls.
- If user.primary_pairs is populated: lead with the most relevant preferred pair; if headline relevance is weak for those pairs, state that explicitly.

ACTIONABLE TRIGGERS (mandatory):
- trading_implications MUST include at least one "If [trigger] → then [pair move / level / session]" using the primary instrument.
- Replace "monitor" / "watch closely" / "remain vigilant" with a concrete conditional.

CORRELATION RISK SPECIFICITY (mandatory):
- Do not output generic "correlation risk: medium" without context.
- Name the exact correlated pairs/channels (e.g. EUR/USD + GBP/USD via USD leg, USD/JPY via haven flow, XAU/USD via real yields).
- State one concrete spillover condition that would raise or reduce that risk.

NEUTRAL SUB-CLASSIFICATION (mandatory):
- immediate_reaction stays bullish_usd | bearish_usd | neutral for the API enum.
- When reaction is neutral but narrative has a mild USD lean, the copy must read as NEUTRAL · BULLISH/BEARISH LEAN in trading_implications (do not contradict with "clear bullish USD").
- Use TRUE NEUTRAL only when the headline is genuinely two-sided for USD.
""".strip()

try:
    from services.analysis_news_horizon import NEWS_HORIZON_PROMPT_RULES as _NEWS_HORIZON
except ImportError:
    _NEWS_HORIZON = ""
if _NEWS_HORIZON:
    NEWS_PACK_PROMPT_RULES = f"{NEWS_PACK_PROMPT_RULES}\n\n{_NEWS_HORIZON}"

try:
    from services.analysis_news_classification import NEWS_CLASSIFICATION_PROMPT_RULES as _NEWS_CLASS
except ImportError:
    _NEWS_CLASS = ""
if _NEWS_CLASS:
    NEWS_PACK_PROMPT_RULES = f"{NEWS_PACK_PROMPT_RULES}\n\n{_NEWS_CLASS}"


def _infer_news_currency(news_item: Dict[str, Any]) -> str:
    """Best-effort: derive primary currency from news currency_pairs or title keywords."""
    # Explicit field first
    currency = news_item.get("currency") or news_item.get("primary_currency")
    if currency:
        return str(currency).upper()

    # Derive from currency_pairs list (take base of first pair)
    pairs = news_item.get("currency_pairs") or []
    if pairs:
        first = str(pairs[0]).replace("/", "").replace("-", "").upper()
        if len(first) >= 3:
            return first[:3]

    # Keyword scan on title
    title_lower = (news_item.get("title") or "").lower()
    keyword_map = {
        "usd": "USD", "dollar": "USD", "fed ": "USD", "federal reserve": "USD",
        "eur": "EUR", "euro": "EUR", "ecb": "EUR",
        "gbp": "GBP", "pound": "GBP", "boe": "GBP",
        "jpy": "JPY", "yen": "JPY", "boj": "JPY",
        "aud": "AUD", "australian": "AUD", "rba": "AUD",
        "cad": "CAD", "canadian": "CAD", "boc": "CAD",
        "chf": "CHF", "franc": "CHF", "snb": "CHF",
        "nzd": "NZD", "kiwi": "NZD", "rbnz": "NZD",
    }
    for kw, ccy in keyword_map.items():
        if kw in title_lower:
            return ccy
    return "USD"


def build_news_area_facts(news_item: Dict[str, Any]) -> Dict[str, Any]:
    """Area-specific facts for live_news surface (Phase D)."""
    return {
        "news_id": str(news_item.get("id") or ""),
        "title": str(news_item.get("title") or ""),
        "summary": str(news_item.get("summary") or "")[:400],
        "source": str(news_item.get("source") or ""),
        "published_at": news_item.get("published_at") or news_item.get("timestamp"),
        "impact": str(news_item.get("impact") or "medium").lower(),
        "currency_pairs": news_item.get("currency_pairs") or [],
    }


def build_news_context_pack_section(
    news_item: Dict[str, Any],
    *,
    user_id: Optional[str] = None,
    token_user_info: Optional[Dict[str, Any]] = None,
    focus_instruments: Optional[List[str]] = None,
) -> Tuple[Dict[str, Any], str]:
    """
    Build AnalysisContextPack + prompt block for live news analysis (Phase D).

    Returns (pack_dict, rendered_prompt_block).
    The caller inserts rendered_prompt_block into the GPT prompt instead of
    the legacy personalization + market snapshot blocks.
    """
    area_facts = build_news_area_facts(news_item)
    currency = _infer_news_currency(news_item)
    title = area_facts["title"]
    summary = area_facts["summary"]
    context_text = f"{title} {summary}".strip()

    pack = build_analysis_context_pack(
        surface=SURFACE_LIVE_NEWS,
        user_id=user_id,
        token_user_info=token_user_info,
        subject_currency=currency,
        context_text=context_text,
        focus_instruments=focus_instruments,
        area_facts=area_facts,
        options={"include_holistic_macro": True},
    )
    block = render_pack_for_prompt(pack) + "\n\n" + NEWS_PACK_PROMPT_RULES
    if is_analysis_context_pack_debug():
        logger.info("News context pack built for news_id=%s title=%s", area_facts.get("news_id"), title)
    return pack, block
