#!/usr/bin/env python3
"""
Build concise, relevant market-context snapshots for AI analysis.

Uses the expanded TradingView instrument catalog (same source family as ticker API),
then filters to instruments relevant to a specific event/news request.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from services.tradingview_instruments import instrument_by_id
from services.tradingview_market_data import fetch_tradingview_quotes


_INSTR_BY_ID = instrument_by_id()


def _normalize_pair_to_id(pair: str) -> str:
    return (pair or "").replace("/", "").strip().upper()


def _keyword_in(text: str, keywords: List[str]) -> bool:
    t = (text or "").lower()
    return any(k in t for k in keywords)


def _pick_ids_for_currency(currency: str) -> List[str]:
    c = (currency or "").upper()
    if c == "USD":
        return ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "US10Y", "US02Y", "SPX", "VIX", "GOLD"]
    if c == "EUR":
        return ["EURUSD", "EURGBP", "EURJPY", "EU10Y", "DE10Y"]
    if c == "GBP":
        return ["GBPUSD", "EURGBP", "GBPJPY", "GB10Y"]
    if c == "JPY":
        return ["USDJPY", "EURJPY", "GBPJPY", "JP10Y"]
    if c == "AUD":
        return ["AUDUSD", "AU10Y", "USOIL", "GOLD"]
    if c == "CAD":
        return ["USDCAD", "CA10Y", "USOIL"]
    if c == "CHF":
        return ["USDCHF", "EURCHF", "GBPCHF", "VIX"]
    if c == "NZD":
        return ["NZDUSD", "AUDUSD"]
    return ["EURUSD", "USDJPY", "GBPUSD", "VIX"]


def _pick_ids_by_keywords(text: str) -> List[str]:
    ids: List[str] = []
    if _keyword_in(text, ["gold", "bullion", "xau"]):
        ids.extend(["GOLD", "EURUSD", "USDJPY", "US10Y"])
    if _keyword_in(text, ["silver", "xag"]):
        ids.extend(["SILVER", "EURUSD", "USDJPY"])
    if _keyword_in(text, ["oil", "crude", "brent", "wti", "energy"]):
        ids.extend(["USOIL", "USDCAD", "USDNOK"])
    if _keyword_in(text, ["inflation", "cpi", "ppi", "rates", "hawkish", "dovish", "fomc", "ecb", "boe", "boj"]):
        ids.extend(["US02Y", "US10Y", "EU10Y", "GB10Y", "JP10Y"])
    if _keyword_in(text, ["risk-off", "risk on", "volatility", "fear", "equities", "stocks"]):
        ids.extend(["VIX", "SPX", "DJI", "IXIC", "USDJPY", "GOLD"])
    if _keyword_in(text, ["crypto", "bitcoin", "btc", "ethereum", "eth"]):
        ids.extend(["BTCUSDT", "ETHUSDT", "VIX"])
    # Dedup preserving order
    out: List[str] = []
    seen: Set[str] = set()
    for i in ids:
        if i in seen:
            continue
        seen.add(i)
        out.append(i)
    return out


def _parse_last_update(raw: Any) -> Optional[datetime]:
    if not isinstance(raw, str) or not raw.strip():
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        return None


def _freshness_score(q: Dict[str, Any]) -> float:
    """
    0..1 freshness confidence from quote timestamp + completeness.
    """
    score = 1.0
    if not isinstance(q.get("changePercent"), (int, float)):
        score -= 0.25
    if not isinstance(q.get("change"), (int, float)):
        score -= 0.15
    dt = _parse_last_update(q.get("lastUpdate"))
    if dt is not None:
        now = datetime.now(timezone.utc)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        age_minutes = (now - dt).total_seconds() / 60.0
        if age_minutes > 120:
            score -= 0.45
        elif age_minutes > 30:
            score -= 0.2
    return max(0.0, min(score, 1.0))


def _category_regime_score(inst_id: str, text: str) -> float:
    """
    0..1 relevance by macro regime cues in text.
    """
    meta = _INSTR_BY_ID.get(inst_id, {})
    cat = str(meta.get("category", "")).lower()
    s = 0.0
    if _keyword_in(text, ["risk", "volatility", "fear", "equities", "stocks"]):
        if inst_id in {"VIX", "SPX", "DJI", "IXIC"}:
            s += 1.0
        if inst_id in {"GOLD", "USDJPY", "USDCHF"}:
            s += 0.6
    if _keyword_in(text, ["rates", "yield", "inflation", "cpi", "ppi", "fomc", "ecb", "boe", "boj"]):
        if cat == "bonds":
            s += 1.0
        if inst_id in {"EURUSD", "USDJPY", "GBPUSD"}:
            s += 0.4
    if _keyword_in(text, ["gold", "silver", "oil", "energy", "commodity", "crude"]):
        if cat == "commodities":
            s += 1.0
        if inst_id in {"USDCAD", "USDNOK", "AUDUSD"}:
            s += 0.4
    if _keyword_in(text, ["crypto", "bitcoin", "btc", "ethereum", "eth"]):
        if cat == "crypto":
            s += 1.0
        if inst_id == "VIX":
            s += 0.3
    return max(0.0, min(s, 1.0))


def _event_match_score(
    inst_id: str,
    *,
    currency_ids: Set[str],
    keyword_ids: Set[str],
    focus_ids: Set[str],
) -> float:
    """
    0..1 event relevance from deterministic match sets.
    """
    score = 0.0
    if inst_id in focus_ids:
        score += 1.0
    if inst_id in currency_ids:
        score += 0.75
    if inst_id in keyword_ids:
        score += 0.85
    return max(0.0, min(score, 1.0))


def _preference_score(inst_id: str, preferred_ids: Set[str]) -> float:
    if inst_id in preferred_ids:
        return 1.0
    # Related-asset light boost: EURUSD preference can still help EUR/JPY etc.
    for pid in preferred_ids:
        if len(pid) >= 6 and len(inst_id) >= 6:
            bases = {pid[:3], pid[3:6]}
            if inst_id[:3] in bases or inst_id[3:6] in bases:
                return 0.35
    return 0.0


def _rank_instruments(
    *,
    quotes: Dict[str, Dict[str, Any]],
    currency: Optional[str],
    text: str,
    focus_instruments: Optional[List[str]],
    preferred_instruments: Optional[List[str]],
    surface: str = "generic",
) -> List[Tuple[str, float]]:
    """
    Weighted ranking for prompt context relevance.
    Surface profiles:
    - calendar: macro/event-led
    - news: balanced with stronger personalization influence
    """
    focus_ids = {_normalize_pair_to_id(p) for p in (focus_instruments or []) if _normalize_pair_to_id(p)}
    preferred_ids = {_normalize_pair_to_id(p) for p in (preferred_instruments or []) if _normalize_pair_to_id(p)}
    currency_ids = set(_pick_ids_for_currency(currency or ""))
    keyword_ids = set(_pick_ids_by_keywords(text))

    if surface == "calendar":
        w_event, w_regime, w_pref, w_fresh = 0.60, 0.20, 0.15, 0.05
    elif surface == "news":
        w_event, w_regime, w_pref, w_fresh = 0.45, 0.20, 0.30, 0.05
    else:
        w_event, w_regime, w_pref, w_fresh = 0.50, 0.20, 0.25, 0.05

    ranked: List[Tuple[str, float]] = []
    for inst_id, q in quotes.items():
        event_score = _event_match_score(
            inst_id,
            currency_ids=currency_ids,
            keyword_ids=keyword_ids,
            focus_ids=focus_ids,
        )
        regime_score = _category_regime_score(inst_id, text)
        pref_score = _preference_score(inst_id, preferred_ids)
        fresh_score = _freshness_score(q)
        score = (
            (w_event * event_score) +
            (w_regime * regime_score) +
            (w_pref * pref_score) +
            (w_fresh * fresh_score)
        )
        # Keep only assets with some signal, or top movers fallback logic later.
        if score > 0:
            ranked.append((inst_id, score))

    ranked.sort(key=lambda t: t[1], reverse=True)
    return ranked


def _format_line(inst_id: str, q: Dict[str, Any]) -> str:
    meta = _INSTR_BY_ID.get(inst_id, {})
    label = meta.get("label", inst_id)
    price = q.get("price")
    chg = q.get("change")
    chg_pct = q.get("changePercent")
    if isinstance(chg_pct, (int, float)):
        chg_pct_str = f"{chg_pct:+.2f}%"
    else:
        chg_pct_str = "n/a"
    if isinstance(chg, (int, float)):
        chg_str = f"{chg:+.4f}"
    else:
        chg_str = "n/a"
    return f"- {label} [{inst_id}]: price={price}, daily_change={chg_str}, daily_change_pct={chg_pct_str}"


def build_relevant_market_context_block(
    *,
    currency: Optional[str] = None,
    text: str = "",
    focus_instruments: Optional[List[str]] = None,
    preferred_instruments: Optional[List[str]] = None,
    limit: int = 10,
    surface: str = "generic",
) -> str:
    """
    Build prompt-ready block of relevant prices/changes from expanded ticker universe.
    """
    quotes = fetch_tradingview_quotes() or {}
    if not quotes:
        return "RELEVANT LIVE MARKET SNAPSHOT:\n- No live quote data available from TradingView."

    ranked = _rank_instruments(
        quotes=quotes,
        currency=currency,
        text=text,
        focus_instruments=focus_instruments,
        preferred_instruments=preferred_instruments,
        surface=surface,
    )

    selected_ids: List[str] = [inst_id for inst_id, _ in ranked[: max(1, limit)]]

    # Fallback: ensure non-empty snapshot with top movers.
    if not selected_ids:
        top_movers = sorted(
            quotes.items(),
            key=lambda kv: abs(float(kv[1].get("changePercent") or 0.0)),
            reverse=True,
        )
        selected_ids = [k for k, _ in top_movers[: max(1, min(limit, 5))]]

    lines: List[str] = []
    for inst_id in selected_ids:
        q = quotes.get(inst_id)
        if not q:
            continue
        lines.append(_format_line(inst_id, q))

    if not lines:
        lines = ["- No relevant instrument quotes available."]
    return "RELEVANT LIVE MARKET SNAPSHOT:\n" + "\n".join(lines)

