"""
Curated TradingView scanner instruments (whitelist).

Each row is posted to exactly one scanner namespace (`market` URL segment).
Symbols must match TradingView's naming; unknown symbols return no row from the API.

Categories:
  forex        — major FX (scanner: /forex/scan)
  crypto       — spot crypto pairs (/crypto/scan)
  commodities  — futures (/futures/scan)
  bonds        — sovereign yield curves, % (scanner: /bonds/scan; TVC:* tickers)
  indices      — cash indices & volatility (/cfd/scan); no single-name equities.
"""

from typing import Any, Dict, List, TypedDict


class Instrument(TypedDict, total=False):
    id: str
    label: str
    tv: str
    market: str
    category: str
    decimals: int


# `market` must match https://scanner.tradingview.com/{market}/scan
INSTRUMENTS: List[Instrument] = [
    # --- Forex (15) ---
    {"id": "EURUSD", "label": "EUR/USD", "tv": "FX:EURUSD", "market": "forex", "category": "forex", "decimals": 5},
    {"id": "GBPUSD", "label": "GBP/USD", "tv": "FX:GBPUSD", "market": "forex", "category": "forex", "decimals": 5},
    {"id": "USDJPY", "label": "USD/JPY", "tv": "FX:USDJPY", "market": "forex", "category": "forex", "decimals": 3},
    {"id": "USDCHF", "label": "USD/CHF", "tv": "FX:USDCHF", "market": "forex", "category": "forex", "decimals": 5},
    {"id": "AUDUSD", "label": "AUD/USD", "tv": "FX:AUDUSD", "market": "forex", "category": "forex", "decimals": 5},
    {"id": "USDCAD", "label": "USD/CAD", "tv": "FX:USDCAD", "market": "forex", "category": "forex", "decimals": 5},
    {"id": "NZDUSD", "label": "NZD/USD", "tv": "FX:NZDUSD", "market": "forex", "category": "forex", "decimals": 5},
    {"id": "EURGBP", "label": "EUR/GBP", "tv": "FX:EURGBP", "market": "forex", "category": "forex", "decimals": 5},
    {"id": "EURJPY", "label": "EUR/JPY", "tv": "FX:EURJPY", "market": "forex", "category": "forex", "decimals": 3},
    {"id": "GBPJPY", "label": "GBP/JPY", "tv": "FX:GBPJPY", "market": "forex", "category": "forex", "decimals": 3},
    {"id": "USDSEK", "label": "USD/SEK", "tv": "FX:USDSEK", "market": "forex", "category": "forex", "decimals": 5},
    {"id": "USDNOK", "label": "USD/NOK", "tv": "FX:USDNOK", "market": "forex", "category": "forex", "decimals": 5},
    {"id": "USDHKD", "label": "USD/HKD", "tv": "FX:USDHKD", "market": "forex", "category": "forex", "decimals": 5},
    {"id": "EURCHF", "label": "EUR/CHF", "tv": "FX:EURCHF", "market": "forex", "category": "forex", "decimals": 5},
    {"id": "GBPCHF", "label": "GBP/CHF", "tv": "FX:GBPCHF", "market": "forex", "category": "forex", "decimals": 5},
    # --- Crypto ---
    {"id": "BTCUSDT", "label": "BTC/USDT", "tv": "BINANCE:BTCUSDT", "market": "crypto", "category": "crypto", "decimals": 2},
    {"id": "ETHUSDT", "label": "ETH/USDT", "tv": "BINANCE:ETHUSDT", "market": "crypto", "category": "crypto", "decimals": 2},
    # --- Commodities (futures) ---
    {"id": "GOLD", "label": "Gold (GC)", "tv": "COMEX:GC1!", "market": "futures", "category": "commodities", "decimals": 2},
    {"id": "SILVER", "label": "Silver (SI)", "tv": "COMEX:SI1!", "market": "futures", "category": "commodities", "decimals": 3},
    {"id": "USOIL", "label": "WTI Crude", "tv": "NYMEX:CL1!", "market": "futures", "category": "commodities", "decimals": 2},
    # --- Bond yields (%), major economies (TradingView TVC curve symbols) ---
    {"id": "US02Y", "label": "US 2Y", "tv": "TVC:US02Y", "market": "bonds", "category": "bonds", "decimals": 3},
    {"id": "US10Y", "label": "US 10Y", "tv": "TVC:US10Y", "market": "bonds", "category": "bonds", "decimals": 3},
    {"id": "US30Y", "label": "US 30Y", "tv": "TVC:US30Y", "market": "bonds", "category": "bonds", "decimals": 3},
    {"id": "DE10Y", "label": "DE 10Y", "tv": "TVC:DE10Y", "market": "bonds", "category": "bonds", "decimals": 3},
    {"id": "GB10Y", "label": "UK 10Y", "tv": "TVC:GB10Y", "market": "bonds", "category": "bonds", "decimals": 3},
    {"id": "JP10Y", "label": "JP 10Y", "tv": "TVC:JP10Y", "market": "bonds", "category": "bonds", "decimals": 3},
    {"id": "EU10Y", "label": "EU 10Y", "tv": "TVC:EU10Y", "market": "bonds", "category": "bonds", "decimals": 3},
    {"id": "AU10Y", "label": "AU 10Y", "tv": "TVC:AU10Y", "market": "bonds", "category": "bonds", "decimals": 3},
    {"id": "CA10Y", "label": "CA 10Y", "tv": "TVC:CA10Y", "market": "bonds", "category": "bonds", "decimals": 3},
    {"id": "IT10Y", "label": "IT 10Y", "tv": "TVC:IT10Y", "market": "bonds", "category": "bonds", "decimals": 3},
    # --- Indices & vol (CFD / index symbols on cfd scanner) ---
    {"id": "SPX", "label": "S&P 500", "tv": "SP:SPX", "market": "cfd", "category": "indices", "decimals": 2},
    {"id": "DJI", "label": "Dow Jones", "tv": "DJ:DJI", "market": "cfd", "category": "indices", "decimals": 2},
    {"id": "IXIC", "label": "Nasdaq Comp", "tv": "TVC:IXIC", "market": "cfd", "category": "indices", "decimals": 2},
    {"id": "VIX", "label": "VIX", "tv": "CBOE:VIX", "market": "cfd", "category": "indices", "decimals": 2},
]


def instruments_by_market() -> Dict[str, List[Instrument]]:
    groups: Dict[str, List[Instrument]] = {}
    for inst in INSTRUMENTS:
        m = inst["market"]
        groups.setdefault(m, []).append(inst)
    return groups


def instrument_by_id() -> Dict[str, Instrument]:
    return {i["id"]: i for i in INSTRUMENTS}
