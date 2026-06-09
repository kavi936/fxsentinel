"""
Filesystem OHLC store — v0 JSON per market + resolution.

Path: backend/data/ohlc/{market_id}/{resolution_key}.json
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

_BAR = Dict[str, Any]

_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "ohlc")


def _store_path(market_id: str, resolution_key: str) -> str:
    safe_market = market_id.upper()
    safe_res = resolution_key.replace("/", "_")
    return os.path.join(_DATA_DIR, safe_market, f"{safe_res}.json")


def save_bars(
    market_id: str,
    resolution_key: str,
    bars: List[_BAR],
    *,
    source: str,
    meta: Optional[Dict[str, Any]] = None,
) -> str:
    path = _store_path(market_id, resolution_key)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    payload = {
        "market_id": market_id.upper(),
        "resolution": resolution_key,
        "source": source,
        "as_of": datetime.now(timezone.utc).isoformat(),
        "bars": bars,
        "meta": meta or {},
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, separators=(",", ":"))
    return path


def load_bars(market_id: str, resolution_key: str) -> Optional[Dict[str, Any]]:
    path = _store_path(market_id, resolution_key)
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def get_bar_list(market_id: str, resolution_key: str) -> List[_BAR]:
    doc = load_bars(market_id, resolution_key)
    if not doc:
        return []
    bars = doc.get("bars") or []
    return sorted(bars, key=lambda b: int(b.get("time", 0)))


def cache_age_seconds(market_id: str, resolution_key: str) -> Optional[float]:
    """Seconds since last save_bars for this series, or None if missing/unparseable."""
    doc = load_bars(market_id, resolution_key)
    if not doc:
        return None
    raw = doc.get("as_of")
    if not raw:
        return None
    try:
        as_of = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        if as_of.tzinfo is None:
            as_of = as_of.replace(tzinfo=timezone.utc)
        return max(0.0, (datetime.now(timezone.utc) - as_of).total_seconds())
    except (TypeError, ValueError):
        return None
