"""
Compose cross-app context for Markets research — calendar, macro scan, sentiment, news.

All platform data is pulled server-side; Markets UI reads one /research payload.
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from services.markets.market_profile import load_market_profile

logger = logging.getLogger(__name__)

_IMPACT_RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}

# In-memory cache for deterministic US scan digest (avoid rebuild every /research)
_scan_cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}
_SCAN_CACHE_TTL_SEC = 3600


def _impact_meets_min(impact: str, impact_min: str) -> bool:
    return _IMPACT_RANK.get((impact or "low").lower(), 0) >= _IMPACT_RANK.get(
        (impact_min or "medium").lower(), 1
    )


def _event_matches_calendar_filter(event: Dict[str, Any], filt: Dict[str, Any]) -> bool:
    currencies = [c.upper() for c in (filt.get("currencies") or [])]
    if currencies:
        ev_cur = (event.get("currency") or "").upper()
        if ev_cur and ev_cur not in currencies:
            return False

    if not _impact_meets_min(str(event.get("impact") or "medium"), str(filt.get("impact_min") or "medium")):
        return False

    tags = [t.upper() for t in (filt.get("tags") or []) if t]
    if tags:
        hay = f"{event.get('title') or ''} {event.get('type') or ''} {event.get('description') or ''}".upper()
        if not any(tag in hay for tag in tags):
            return False

    return True


def fetch_market_catalysts(profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    filt = profile.get("calendar_filter") or {}
    horizon = int(filt.get("horizon_days") or 7)
    max_items = int(filt.get("max_items") or 8)

    start = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    end = (datetime.now(timezone.utc) + timedelta(days=horizon)).strftime("%Y-%m-%d")

    try:
        from services.hybrid_economic_calendar import hybrid_economic_calendar

        raw = hybrid_economic_calendar.get_economic_events(start, end) or []
    except Exception as e:
        logger.warning("Calendar fetch failed for Markets: %s", e)
        return []

    matched: List[Dict[str, Any]] = []
    for ev in raw:
        if not isinstance(ev, dict):
            continue
        if not _event_matches_calendar_filter(ev, filt):
            continue
        matched.append(
            {
                "id": ev.get("id") or f"cal_{hash(ev.get('title', ''))}",
                "title": ev.get("title") or "Economic event",
                "date": ev.get("date"),
                "time": ev.get("time"),
                "currency": ev.get("currency"),
                "impact": ev.get("impact") or "medium",
                "status": ev.get("status") or "upcoming",
                "source": ev.get("source") or "calendar",
            }
        )

    def sort_key(row: Dict[str, Any]) -> Tuple[str, str]:
        return (str(row.get("date") or ""), str(row.get("time") or ""))

    matched.sort(key=sort_key)
    return matched[:max_items]


def _load_fallback_indicators(country_code: str) -> Dict[str, Any]:
    """Load economy indicator snapshot — tries repo-root and backend-relative paths."""
    candidates = []
    here = Path(__file__).resolve()
    repo_root = here.parents[3]
    candidates.extend(
        [
            repo_root / "src" / "data" / "economyIndicators.json",
            here.parents[2] / "data" / "economyIndicators.json",
            Path.cwd() / "src" / "data" / "economyIndicators.json",
            Path.cwd() / "economyIndicators.json",
        ]
    )

    for path in candidates:
        if not path.is_file():
            continue
        try:
            with path.open(encoding="utf-8") as f:
                payload = json.load(f)
            return (payload.get(country_code.upper()) or {}).get("indicators") or {}
        except Exception as e:
            logger.debug("Indicators file %s unreadable: %s", path, e)

    logger.warning("economyIndicators.json not found — US macro digest may be thin")
    return {}


def _load_live_yields() -> Dict[str, Any]:
    try:
        from app import get_tradingview_prices

        return get_tradingview_prices() or {}
    except Exception as e:
        logger.debug("Live yields unavailable for macro digest: %s", e)
        return {}


def _build_country_scan_digest(country: str, max_age_hours: float) -> Optional[Dict[str, Any]]:
    cache_key = country.upper()
    cached = _scan_cache.get(cache_key)
    if cached and (time.monotonic() - cached[0]) < _SCAN_CACHE_TTL_SEC:
        return cached[1]

    try:
        from services.analysis_context_pack import extract_macro_snapshot_from_scan
        from services.economy_holistic_scan_service import economy_holistic_scan_service
        from services.hybrid_economic_calendar import hybrid_economic_calendar
    except ImportError as e:
        logger.warning("Macro scan modules unavailable: %s", e)
        return None

    cc = country.upper()
    if cc not in economy_holistic_scan_service.SUPPORTED_COUNTRIES:
        return None

    indicators = _load_fallback_indicators(cc)
    start = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    end = (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d")
    try:
        events = hybrid_economic_calendar.get_economic_events(start, end) or []
    except Exception:
        events = []

    try:
        scan = economy_holistic_scan_service.build_scan(
            country_code=cc,
            indicators=indicators,
            events=events,
            yields=_load_live_yields(),
            personalization=None,
            user_info=None,
        )
    except Exception as e:
        logger.warning("US scan build failed for Markets macro context: %s", e)
        return None

    macro = extract_macro_snapshot_from_scan(scan, scanned_at=datetime.now(timezone.utc))
    macro["scanned_at"] = datetime.now(timezone.utc).isoformat()
    macro["country"] = cc
    macro["trader_brief"] = (scan.get("trader_brief") or {}).get("short_term_line")

    freshness = macro.get("freshness_hours")
    if freshness is not None and float(freshness) > max_age_hours:
        return None

    _scan_cache[cache_key] = (time.monotonic(), macro)
    return macro


def fetch_macro_context(profile: Dict[str, Any]) -> Dict[str, Any]:
    scans_cfg = profile.get("economy_scans") or []
    digests: List[Dict[str, Any]] = []

    for row in scans_cfg:
        if not isinstance(row, dict):
            continue
        country = (row.get("country") or "").upper()
        if not country:
            continue
        max_age = float(row.get("max_age_hours") or 72)
        digest = _build_country_scan_digest(country, max_age)
        if digest:
            digests.append(digest)

    primary = digests[0] if digests else None
    return {
        "digests": digests,
        "primary_country": (primary or {}).get("country") or (primary or {}).get("country_code"),
        "us_scan_summary": (primary or {}).get("one_line_summary"),
        "us_scan_as_of": (primary or {}).get("scanned_at"),
        "short_term_bias": (primary or {}).get("short_term_bias"),
        "long_term_bias": (primary or {}).get("long_term_bias"),
        "calendar_stress_14d": (primary or {}).get("calendar_stress_14d"),
        "theme_digest": (primary or {}).get("theme_digest") or [],
    }


def fetch_sentiment_snapshot() -> Dict[str, Any]:
    try:
        from services.market_sentiment_service import market_sentiment_service

        raw = market_sentiment_service.get_market_sentiment() or {}
    except Exception as e:
        logger.warning("Market sentiment unavailable for Markets: %s", e)
        return {}

    risk_regime = "mixed"
    volatility = None
    for cond in raw.get("market_conditions") or []:
        if not isinstance(cond, dict):
            continue
        name = (cond.get("name") or "").lower()
        if name == "risk appetite":
            val = cond.get("percentage")
            if val is None:
                val = cond.get("value")
            if val is not None:
                try:
                    v = float(val)
                    if v >= 55:
                        risk_regime = "risk_on"
                    elif v <= 45:
                        risk_regime = "risk_off"
                    else:
                        risk_regime = "mixed"
                except (TypeError, ValueError):
                    level = (cond.get("value") or "").lower()
                    if level in ("high", "risk_on"):
                        risk_regime = "risk_on"
                    elif level in ("low", "risk_off"):
                        risk_regime = "risk_off"
        if name == "volatility environment":
            detail = (cond.get("detail") or "").lower()
            if "high" in detail or (raw.get("vix") or {}).get("level") == "high":
                volatility = "high"
            elif "low" in detail or (raw.get("vix") or {}).get("level") == "low":
                volatility = "low"
            else:
                volatility = "medium"

    fng = raw.get("fng") or {}
    return {
        "risk_regime": risk_regime,
        "volatility": volatility,
        "fear_greed": {
            "value": fng.get("value"),
            "classification": fng.get("classification"),
        },
        "vix": raw.get("vix"),
        "as_of": raw.get("timestamp"),
        "source": "market_sentiment_service",
    }


def fetch_market_news(profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    filt = profile.get("news_filter") or {}
    keywords = tuple(k.lower() for k in (filt.get("keywords") or []) if k)
    limit = int(filt.get("max_items") or 5)
    if not keywords:
        return []

    try:
        from services.persistent_news_cache import get_persistent_news_cache

        raw = get_persistent_news_cache().load_news(allow_stale=True) or []
    except Exception:
        return []

    out: List[Dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        text = f"{item.get('title') or ''} {item.get('summary') or ''}".lower()
        if not any(kw in text for kw in keywords):
            continue
        out.append(
            {
                "title": item.get("title") or "",
                "source": item.get("source") or item.get("publisher") or "",
                "published_at": item.get("published_at") or item.get("date") or item.get("timestamp"),
                "url": item.get("url") or item.get("link"),
            }
        )
        if len(out) >= limit:
            break
    return out


def build_platform_context(market_id: str) -> Dict[str, Any]:
    profile = load_market_profile(market_id)
    if not profile:
        return {
            "catalysts": [],
            "macro_context": {},
            "sentiment": {},
            "news": [],
        }

    platform = profile.get("platform_context") or {}
    sentiment = fetch_sentiment_snapshot() if platform.get("market_sentiment", True) else {}

    return {
        "catalysts": fetch_market_catalysts(profile),
        "macro_context": fetch_macro_context(profile),
        "sentiment": sentiment,
        "news": fetch_market_news(profile),
        "profile": {
            "market_id": profile.get("market_id"),
            "narrative_frame": profile.get("narrative_frame"),
        },
    }


def get_cross_asset_ids(profile: Optional[Dict[str, Any]]) -> Tuple[str, ...]:
    if profile and profile.get("cross_assets"):
        return tuple(profile["cross_assets"])
    return ("ETHUSDT", "SPX", "VIX", "US10Y", "GOLD")
