"""
Multi-namespace TradingView scanner fetch: parallel POSTs per market, merged by internal id.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

from services.tradingview_instruments import INSTRUMENTS, Instrument, instruments_by_market

TV_HEADERS = {
    "Content-Type": "application/json",
    "Origin": "https://www.tradingview.com",
    "Referer": "https://www.tradingview.com/",
}

SCAN_TIMEOUT = 8


def _scan_one_market(market: str, instruments: List[Instrument]) -> Dict[str, Any]:
    """POST to one scanner namespace; returns price dict keyed by internal id."""
    if not instruments:
        return {}

    url = f"https://scanner.tradingview.com/{market}/scan"
    tickers = [i["tv"] for i in instruments]
    tv_to_inst = {i["tv"]: i for i in instruments}

    payload = {
        "symbols": {"tickers": tickers},
        "columns": ["close", "change", "change_abs"],
    }

    out: Dict[str, Any] = {}
    try:
        response = requests.post(url, headers=TV_HEADERS, json=payload, timeout=SCAN_TIMEOUT)
        if response.status_code == 429:
            print(f"⚠️ TradingView rate limit (429) on {market}/scan")
            return {}
        response.raise_for_status()
        result = response.json()
    except requests.RequestException as e:
        print(f"❌ TradingView {market}/scan request error: {e}")
        return {}
    except ValueError as e:
        print(f"❌ TradingView {market}/scan JSON error: {e}")
        return {}

    rows = result.get("data") or []
    for item in rows:
        symbol = item.get("s")
        values = item.get("d") or []
        if not symbol or len(values) < 3:
            continue
        inst = tv_to_inst.get(symbol)
        if not inst:
            continue

        price = values[0]
        change_percent = values[1]
        change_abs = values[2]
        inst_id = inst["id"]

        out[inst_id] = {
            "price": price,
            "change": change_abs,
            "changePercent": change_percent,
            "lastUpdate": datetime.now().isoformat(),
            "source": "TradingView",
            "category": inst.get("category", "forex"),
            "decimals": inst.get("decimals", 4),
            "tvSymbol": inst["tv"],
        }

    return out


def fetch_tradingview_quotes() -> Optional[Dict[str, Any]]:
    """
    Fetch all configured instruments from TradingView (parallel per market namespace).
    Returns None only if every market request fails or returns empty.
    """
    groups = instruments_by_market()
    merged: Dict[str, Any] = {}

    if not INSTRUMENTS:
        return None

    try:
        from services.live_lite_config import tradingview_max_workers
        workers = min(tradingview_max_workers(), len(groups) or 1)
    except Exception:
        workers = min(8, len(groups) or 1)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(_scan_one_market, market, insts): market
            for market, insts in groups.items()
        }
        for fut in as_completed(futures):
            market = futures[fut]
            try:
                part = fut.result()
                merged.update(part)
            except Exception as e:
                print(f"❌ TradingView worker error ({market}): {e}")

    if not merged:
        return None

    print(f"✅ TradingView merged quotes: {len(merged)} instruments — {list(merged.keys())}")
    return merged
