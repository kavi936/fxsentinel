# Market ticker: multi-asset implementation log

This document summarizes the work done to expand the Overview live market ticker beyond forex to include crypto, commodities (futures), and indices—without adding single-name equities. Use it when testing or continuing work in a follow-up chat.

## Goals

- Fetch quotes from TradingView across multiple scanner namespaces (not only `/forex/scan`).
- Return a single merged price map keyed by stable internal instrument ids.
- Expose a catalog to the frontend so the ticker picker can list instruments by category.
- Keep the existing `GET /api/forex-prices` route and `useForexPrices` hook path for compatibility.

## Architecture (high level)

1. **Backend whitelist** (`tradingview_instruments.py`) — Each row defines: internal `id`, display `label`, TradingView symbol `tv`, scanner `market` (URL segment), `category`, and `decimals`.
2. **Parallel fetches** (`tradingview_market_data.py`) — Instruments are grouped by `market`. For each group, one `POST` to `https://scanner.tradingview.com/{market}/scan` with the same column shape as before: `close`, `change`, `change_abs`. Results are merged into one dictionary keyed by `id`.
3. **API** — Successful responses include `prices` plus an `instruments` array `{ id, label, category, decimals }` for UI sync.
4. **Frontend** — `useForexPrices` now also returns `instruments` and caches it with `forexPrices` in `localStorage`. Overview uses the API catalog when present, otherwise a static `DEFAULT_TICKER_INSTRUMENTS` list. The ticker row uses per-instrument decimal formatting. The selection modal is split into sections: Forex, Crypto, Commodities, Indices.

## Files added

| File | Purpose |
|------|---------|
| `backend/services/tradingview_instruments.py` | Curated instrument list and `instruments_by_market()` helper. |
| `backend/services/tradingview_market_data.py` | `fetch_tradingview_quotes()` — parallel scanner POSTs and merge. |

## Files modified

| File | Changes |
|------|---------|
| `backend/app.py` | `get_tradingview_prices()` delegates to `fetch_tradingview_quotes()`. `GET /api/forex-prices` success payload includes `instruments`. |
| `src/hooks/useForexPrices.js` | State + cache for `instruments`; extended offline `fallbackPrices` for new ids. |
| `src/components/Overview.jsx` | Ticker catalog constants, `tickerInstrumentCatalog` from hook, `pair.id` lookups, `formatTickerPrice` / `formatTickerChange`, grouped ticker modal. |
| `src/components/Overview.css` | `.ticker-modal-sections`, section titles, `.ticker-modal-pairs-grid`. |

## Instrument catalog (24 items)

- **Forex (15):** `EURUSD` … `GBPCHF` — `FX:*` on `forex` scanner.
- **Crypto (2):** `BTCUSDT`, `ETHUSDT` — `BINANCE:*` on `crypto` scanner.
- **Commodities / futures (3):** `GOLD` (COMEX:GC1!), `SILVER` (COMEX:SI1!), `USOIL` (NYMEX:CL1!) — `futures` scanner.
- **Indices / vol (4):** `SPX` (SP:SPX), `DJI` (DJ:DJI), `IXIC` (TVC:IXIC), `VIX` (CBOE:VIX) — `cfd` scanner.

No individual stocks; index symbols are broad indices / volatility, not equity tickers.

## Data shape (per quote in `prices`)

Each entry may include:

- `price`, `change` (absolute), `changePercent`, `lastUpdate`, `source`
- `category`, `decimals`, `tvSymbol` (helps debugging and future providers)

## Compatibility notes

- **Market sentiment** (`market_sentiment_service.py`) still reads `get_tradingview_prices()`; it only uses major FX keys (`EURUSD`, `GBPUSD`, `USDJPY`, `USDCHF`). Extra keys in the dict do not break that path.
- **localStorage:** `fxSentinel_selectedTickerPairs` still stores an array of string ids (e.g. `EURUSD`). New ids (`BTCUSDT`, `GOLD`, …) work the same way.
- **Hook name** remains `useForexPrices` for now; the endpoint remains `/api/forex-prices`.

## TradingView / operational caveats

- Scanner usage is **unofficial**; rate limits (e.g. HTTP 429), schema changes, or blocking are possible.
- Requests use `Origin` / `Referer` similar to the browser to reduce avoidable friction.
- Delayed vs real-time data depends on TradingView’s rules for unauthenticated scanner access.

## How to test (quick checklist)

1. **Backend:** From `backend/`, run Python and call `fetch_tradingview_quotes()` or `get_tradingview_prices()`; expect up to 24 keys when TradingView responds.
2. **API:** `GET /api/forex-prices` — verify `prices` and `instruments` arrays.
3. **UI:** Open Overview — ticker shows selected instruments with sensible decimals; open the pencil modal — four sections; add e.g. BTC and SPX, confirm order badges and persistence after refresh.

## Suggested follow-ups (not implemented)

- Rename API/hook (`/api/market-quotes`, `useMarketQuotes`) when you are ready for a breaking or parallel rollout.
- Optional migration: prune unknown ids in `fxSentinel_selectedTickerPairs` if the catalog shrinks.
- Secondary data provider behind the same internal ids if TradingView becomes unreliable.
- Cap max ticker selections if the strip gets too crowded on mobile.

---

*Written for handoff to the next chat; update this file as you adjust behavior or symbols.*
