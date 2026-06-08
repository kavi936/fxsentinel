"""BTC-focused news filter for Markets tab strip."""

from __future__ import annotations

from typing import Any, Dict, List

BTC_NEWS_KEYWORDS = (
    "bitcoin",
    "btc",
    "crypto",
    "cryptocurrency",
    "ethereum",
    "etf",
    "sec",
    "binance",
    "regulation",
)


def is_btc_market_news(item: Dict[str, Any]) -> bool:
    text = f"{item.get('title') or ''} {item.get('summary') or ''}".lower()
    return any(kw in text for kw in BTC_NEWS_KEYWORDS)


def filter_btc_news(items: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
    if not items:
        return []
    out: List[Dict[str, Any]] = []
    for item in items:
        if not is_btc_market_news(item):
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


def fetch_btc_market_news(limit: int = 5) -> List[Dict[str, Any]]:
    try:
        from services.persistent_news_cache import get_persistent_news_cache

        cache = get_persistent_news_cache()
        raw = cache.load_news(allow_stale=True) or []
        return filter_btc_news(raw, limit=limit)
    except Exception:
        return []
