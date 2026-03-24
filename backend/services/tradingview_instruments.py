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
    {"id": "DE02Y", "label": "DE 2Y", "tv": "TVC:DE02Y", "market": "bonds", "category": "bonds", "decimals": 3},
    {"id": "DE10Y", "label": "DE 10Y", "tv": "TVC:DE10Y", "market": "bonds", "category": "bonds", "decimals": 3},
    {"id": "DE30Y", "label": "DE 30Y", "tv": "TVC:DE30Y", "market": "bonds", "category": "bonds", "decimals": 3},
    {"id": "GB02Y", "label": "UK 2Y", "tv": "TVC:GB02Y", "market": "bonds", "category": "bonds", "decimals": 3},
    {"id": "GB10Y", "label": "UK 10Y", "tv": "TVC:GB10Y", "market": "bonds", "category": "bonds", "decimals": 3},
    {"id": "GB30Y", "label": "UK 30Y", "tv": "TVC:GB30Y", "market": "bonds", "category": "bonds", "decimals": 3},
    {"id": "JP02Y", "label": "JP 2Y", "tv": "TVC:JP02Y", "market": "bonds", "category": "bonds", "decimals": 3},
    {"id": "JP10Y", "label": "JP 10Y", "tv": "TVC:JP10Y", "market": "bonds", "category": "bonds", "decimals": 3},
    {"id": "JP30Y", "label": "JP 30Y", "tv": "TVC:JP30Y", "market": "bonds", "category": "bonds", "decimals": 3},
    {"id": "EU02Y", "label": "EU 2Y", "tv": "TVC:EU02Y", "market": "bonds", "category": "bonds", "decimals": 3},
    {"id": "EU10Y", "label": "EU 10Y", "tv": "TVC:EU10Y", "market": "bonds", "category": "bonds", "decimals": 3},
    {"id": "EU30Y", "label": "EU 30Y", "tv": "TVC:EU30Y", "market": "bonds", "category": "bonds", "decimals": 3},
    {"id": "AU02Y", "label": "AU 2Y", "tv": "TVC:AU02Y", "market": "bonds", "category": "bonds", "decimals": 3},
    {"id": "AU10Y", "label": "AU 10Y", "tv": "TVC:AU10Y", "market": "bonds", "category": "bonds", "decimals": 3},
    {"id": "AU30Y", "label": "AU 30Y", "tv": "TVC:AU30Y", "market": "bonds", "category": "bonds", "decimals": 3},
    {"id": "CA02Y", "label": "CA 2Y", "tv": "TVC:CA02Y", "market": "bonds", "category": "bonds", "decimals": 3},
    {"id": "CA10Y", "label": "CA 10Y", "tv": "TVC:CA10Y", "market": "bonds", "category": "bonds", "decimals": 3},
    {"id": "CA30Y", "label": "CA 30Y", "tv": "TVC:CA30Y", "market": "bonds", "category": "bonds", "decimals": 3},
    {"id": "IT02Y", "label": "IT 2Y", "tv": "TVC:IT02Y", "market": "bonds", "category": "bonds", "decimals": 3},
    {"id": "IT10Y", "label": "IT 10Y", "tv": "TVC:IT10Y", "market": "bonds", "category": "bonds", "decimals": 3},
    {"id": "IT30Y", "label": "IT 30Y", "tv": "TVC:IT30Y", "market": "bonds", "category": "bonds", "decimals": 3},
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
