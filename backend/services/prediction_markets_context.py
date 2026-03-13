"""
Prediction Markets Context for AI Analysis.

Read-only, query-style helpers on top of cached prediction markets.
Returns small, curated, structured payloads for injection into AI prompts
(central bank context, event context, FX pair context).
"""
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

# Central bank identifier -> keywords to match in market question/title (lowercase)
_CENTRAL_BANK_KEYWORDS: Dict[str, List[str]] = {
    "Fed": ["fed", "federal reserve", "fomc", "jerome powell", "powell"],
    "ECB": ["ecb", "european central bank", "christine lagarde", "lagarde"],
    "BOE": ["boe", "bank of england", "andrew bailey", "bailey"],
    "BOJ": ["boj", "bank of japan", "kazuo ueda", "ueda", "kuroda"],
    "RBNZ": ["rbnz", "reserve bank of new zealand", "new zealand rate"],
    "BOC": ["bank of canada", "boc", "poloz", "macklem"],
    "RBA": ["rba", "reserve bank of australia", "australia rate"],
    "SNB": ["snb", "swiss national bank", "swiss rate"],
}

# FX pair -> central banks / regions that move the pair (for relevance)
_FX_PAIR_TO_BANKS: Dict[str, List[str]] = {
    "EURUSD": ["Fed", "ECB"],
    "GBPUSD": ["Fed", "BOE"],
    "USDJPY": ["Fed", "BOJ"],
    "USDCHF": ["Fed", "SNB"],
    "AUDUSD": ["Fed", "RBA"],
    "USDCAD": ["Fed", "BOC"],
    "NZDUSD": ["Fed", "RBNZ"],
    "EURGBP": ["ECB", "BOE"],
    "EURJPY": ["ECB", "BOJ"],
    "GBPJPY": ["BOE", "BOJ"],
}

# Event type -> keywords in market question (for event_context)
_EVENT_TYPE_KEYWORDS: Dict[str, List[str]] = {
    "CPI": ["cpi", "consumer price index", "inflation report", "inflation"],
    "NFP": ["nfp", "non-farm payroll", "employment", "jobs report", "nonfarm"],
    "GDP": ["gdp", "gross domestic product", "growth"],
    "RATE_DECISION": ["rate cut", "rate hike", "interest rate", "basis points", "bps", "fed rate", "policy rate"],
}


def _get_cached_markets() -> List[Dict[str, Any]]:
    """Get current cached markets from PredictionMarketsService. Returns [] if unavailable."""
    try:
        from services.prediction_markets_service import prediction_markets_service
        markets = prediction_markets_service.cached_markets
        return list(markets) if markets else []
    except Exception:
        return []


def _market_text(m: Dict[str, Any]) -> str:
    """Single string for keyword matching: question + event_title + event_slug."""
    q = (m.get("question") or m.get("title") or "").lower()
    et = (m.get("event_title") or "").lower()
    es = (m.get("event_slug") or "").lower()
    return f"{q} {et} {es}"


def _to_compact_market(m: Dict[str, Any]) -> Dict[str, Any]:
    """Build AI-friendly compact market entry from normalized market."""
    yes_price = m.get("yes_price")
    if yes_price is not None:
        try:
            yes_prob = round(float(yes_price) * 100, 1)
        except (TypeError, ValueError):
            yes_prob = None
    else:
        yes_prob = None
    delta_24h = m.get("price_delta_24h")
    if delta_24h is not None:
        try:
            delta_24h = round(float(delta_24h), 1)
        except (TypeError, ValueError):
            pass
    return {
        "id": m.get("id"),
        "question": (m.get("question") or m.get("title") or "")[:500],
        "yes_probability": yes_prob,
        "price_delta_24h": delta_24h,
        "volume": m.get("volume"),
        "resolution_date": m.get("resolution_date"),
        "conviction_level": m.get("conviction_level"),
    }


def get_central_bank_context(
    central_bank: str,
    horizon_days: int = 120,
    max_markets: int = 5,
) -> Dict[str, Any]:
    """
    Get prediction market expectations for a central bank (Fed, ECB, BOJ, etc.).

    Args:
        central_bank: One of Fed, ECB, BOE, BOJ, RBNZ, BOC, RBA.
        horizon_days: Only include markets resolving within this many days (past or future).
        max_markets: Max number of markets to return (default 5 for token budget).

    Returns:
        Structured payload for AI injection, e.g.:
        {"provider": "prediction_markets", "as_of": "...", "central_bank": "Fed", "markets": [...]}
    """
    markets = _get_cached_markets()
    now = datetime.now(timezone.utc)
    horizon_end = now + timedelta(days=horizon_days)
    horizon_start = now - timedelta(days=min(horizon_days, 30))  # allow some past for recently resolved

    keywords = _CENTRAL_BANK_KEYWORDS.get(central_bank)
    if not keywords:
        return {
            "provider": "prediction_markets",
            "as_of": now.isoformat(),
            "central_bank": central_bank,
            "markets": [],
            "error": f"Unknown central_bank: {central_bank}",
        }

    # Filter: Polymarket (or allow all platforms), keyword match, resolution in window
    candidates = []
    for m in markets:
        if m.get("platform") and m.get("platform", "").lower() != "polymarket":
            continue
        text = _market_text(m)
        if not any(kw in text for kw in keywords):
            continue
        rd = m.get("resolution_date")
        if rd:
            try:
                if isinstance(rd, (int, float)):
                    res_dt = datetime.fromtimestamp(rd, tz=timezone.utc)
                else:
                    res_dt = datetime.fromisoformat(str(rd).replace("Z", "+00:00"))
                    if res_dt.tzinfo is None:
                        res_dt = res_dt.replace(tzinfo=timezone.utc)
                if not (horizon_start <= res_dt <= horizon_end):
                    continue
            except (ValueError, TypeError):
                pass
        # Prefer active, not resolved
        if m.get("is_resolved") or m.get("closed"):
            score = 0
        else:
            score = 1
        vol = float(m.get("volume") or 0)
        conv = m.get("conviction_score") or 0
        try:
            conv = float(conv)
        except (TypeError, ValueError):
            conv = 0
        candidates.append((m, score, vol, conv))

    # Sort: active first, then volume desc, then conviction desc
    candidates.sort(key=lambda x: (x[1], -(x[2] or 0), -(x[3] or 0)), reverse=True)
    top = [c[0] for c in candidates[:max_markets]]

    return {
        "provider": "prediction_markets",
        "as_of": now.isoformat(),
        "central_bank": central_bank,
        "markets": [_to_compact_market(m) for m in top],
    }


def get_event_context(
    event_type: str,
    country: str,
    date: Optional[datetime] = None,
    max_markets: int = 3,
) -> Dict[str, Any]:
    """
    Get prediction markets relevant to a macro event (CPI, NFP, GDP, rate decision).

    Args:
        event_type: One of CPI, NFP, GDP, RATE_DECISION.
        country: e.g. US, UK, EU (used to bias question match).
        date: Optional event date to prefer markets near this date.
        max_markets: Max markets to return.

    Returns:
        Structured payload for AI injection.
    """
    markets = _get_cached_markets()
    now = datetime.now(timezone.utc)
    keywords = _EVENT_TYPE_KEYWORDS.get(event_type, [event_type.lower()])
    country_lower = country.upper() if country else ""

    candidates = []
    for m in markets:
        if m.get("platform") and m.get("platform", "").lower() != "polymarket":
            continue
        text = _market_text(m)
        if not any(kw in text for kw in keywords):
            continue
        if country_lower and country_lower not in text.upper() and "us " not in text and "u.s" not in text and "united states" not in text:
            if country_lower == "US" and "fed" not in text and "fomc" not in text:
                continue
        vol = float(m.get("volume") or 0)
        conv = float(m.get("conviction_score") or 0)
        candidates.append((m, vol, conv))

    candidates.sort(key=lambda x: (-(x[1] or 0), -(x[2] or 0)))
    top = [c[0] for c in candidates[:max_markets]]

    return {
        "provider": "prediction_markets",
        "as_of": now.isoformat(),
        "event_type": event_type,
        "country": country,
        "markets": [_to_compact_market(m) for m in top],
    }


def get_fx_pair_context(
    pair: str,
    max_markets: int = 7,
) -> Dict[str, Any]:
    """
    Get prediction markets most relevant to an FX pair (Fed/ECB/BOE/BOJ etc.).

    Args:
        pair: e.g. EURUSD, GBPUSD, USDJPY.
        max_markets: Max markets to return.

    Returns:
        Structured payload with markets from the central banks that drive the pair.
    """
    pair_upper = (pair or "").replace("/", "").upper()
    banks = _FX_PAIR_TO_BANKS.get(pair_upper)
    if not banks:
        banks = ["Fed"]

    all_candidates = []
    for central_bank in banks:
        ctx = get_central_bank_context(central_bank, horizon_days=120, max_markets=max_markets)
        for m in ctx.get("markets", []):
            m_copy = dict(m)
            m_copy["central_bank"] = central_bank
            all_candidates.append(m_copy)

    # Dedupe by id, keep order
    seen_ids = set()
    unique = []
    for m in all_candidates:
        mid = m.get("id")
        if mid and mid not in seen_ids:
            seen_ids.add(mid)
            unique.append(m)
        elif not mid:
            unique.append(m)

    now = datetime.now(timezone.utc)
    return {
        "provider": "prediction_markets",
        "as_of": now.isoformat(),
        "fx_pair": pair_upper,
        "central_banks": banks,
        "markets": unique[:max_markets],
    }


def format_central_bank_context_for_prompt(context_payload: Dict[str, Any]) -> str:
    """
    Format get_central_bank_context() result as a string for prompt injection.
    """
    if not context_payload or not context_payload.get("markets"):
        return ""
    central_bank = context_payload.get("central_bank", "CB")
    as_of = context_payload.get("as_of", "")[:19]
    lines = [f"Prediction market expectations (Polymarket, as of {as_of}):", f"- {central_bank}:"]
    for m in context_payload.get("markets", []):
        q = (m.get("question") or "")[:200]
        prob = m.get("yes_probability")
        delta = m.get("price_delta_24h")
        conv = m.get("conviction_level") or ""
        prob_str = f" {int(prob)}% yes" if prob is not None and prob == int(prob) else (f" {round(prob, 1)}% yes" if prob is not None else "")
        delta_str = f", 24h: {delta:+.1f}%" if delta is not None else ""
        lines.append(f"  - {q}{prob_str}{delta_str} ({conv})".strip())
    return "\n".join(lines)
