#!/usr/bin/env python3
"""
Refresh OHLC cache for Markets tab symbols.

Usage:
  cd backend && python scripts/ingest_market_ohlc.py --market BTCUSD
  cd backend && python scripts/ingest_market_ohlc.py --market BTCUSD --resolution 240,60,D
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.markets.market_registry import get_market
from services.markets.ohlc_ingest_binance import ingest_market


def main():
    parser = argparse.ArgumentParser(description="Ingest market OHLC into ohlc_store")
    parser.add_argument("--market", default="BTCUSD", help="Market id (e.g. BTCUSD)")
    parser.add_argument(
        "--resolution",
        default="240,60,D",
        help="Comma-separated UDF resolutions (60, 240, D)",
    )
    parser.add_argument("--limit", type=int, default=500, help="Max bars per resolution")
    args = parser.parse_args()

    market = get_market(args.market)
    if not market:
        print(f"Unknown market: {args.market}")
        sys.exit(1)

    if market.get("ohlc_source") != "binance":
        print(f"Market {args.market} uses {market.get('ohlc_source')} — Binance ingest skipped")
        sys.exit(0)

    symbol = market.get("binance_symbol")
    if not symbol:
        print("No binance_symbol configured")
        sys.exit(1)

    for res in args.resolution.split(","):
        res = res.strip()
        if not res:
            continue
        bars, path = ingest_market(args.market, symbol, res, limit=args.limit)
        print(f"OK {args.market} {res}: {len(bars)} bars → {path}")


if __name__ == "__main__":
    main()
