# MT5 → FXSentinel bridge (spike)

**Status:** Not implemented — start after Windows VPS + demo account are ready.

Parent roadmap: [`docs/MARKETS_ADVANCED_CHARTS_ROADMAP.md`](../../docs/MARKETS_ADVANCED_CHARTS_ROADMAP.md)

---

## Goal

Stream broker OHLC from MetaTrader 5 into `backend/data/ohlc/` and serve via `/api/udf/*` (same layer as Binance v0).

---

## Environment checklist

- [ ] Windows VPS (or local Windows PC for dev only)
- [ ] MT5 terminal installed, logged into **demo** broker account
- [ ] Symbols visible in Market Watch: `EURUSD`, `GBPUSD`, `USDJPY`, `BTCUSD` (broker naming may differ)
- [ ] Python bridge runs on same machine **or** reachable host (EA connects outbound)

---

## Architecture

```text
MT5 Terminal
  └── FXSentinelBridgeEA.mq5  (TCP client, JSON lines)
         ↓ connect host:port
Python mt5_bridge_server.py   (TCP server)
         ↓
ohlc_store.save_bars()
         ↓
udf_datafeed.udf_history()    (existing)
```

### Why EA is TCP **client**

MQL5 Expert Advisors can only open **client** sockets. Python must **listen**.

---

## Planned JSON protocol (sketch)

**EA → Python (tick / bar close):**

```json
{"type":"bar","symbol":"EURUSD","resolution":"240","time":1710000000,"o":1.08,"h":1.09,"l":1.07,"c":1.085,"v":0}
```

**Python → EA (history request):**

```json
{"type":"history_request","id":"req-1","symbol":"EURUSD","resolution":"240","from":1700000000,"to":1710000000}
```

**EA → Python (history response):**

```json
{"type":"history","id":"req-1","bars":[...]}
```

Finalize message shapes during spike; keep one JSON object per line (NDJSON).

---

## Files to create (v1)

| File | Role |
|------|------|
| `FXSentinelBridgeEA.mq5` | EA in MT5 `Experts/` folder |
| `../services/markets/mt5_bridge_server.py` | Async TCP server |
| `../services/markets/ohlc_ingest_mt5.py` | Normalize + `save_bars` |

Enable in `market_registry.py`: set `ohlc_source: "mt5"` and `enabled: True` per symbol when feed is stable.

---

## Broker ToS

Confirm your broker allows displaying quotes to FXSentinel users (redistribution). See [`docs/MARKETS_CHART_DATAFEED_EVALUATION.md`](../../docs/MARKETS_CHART_DATAFEED_EVALUATION.md) §6.

---

## Testing without MT5

BTC uses **Binance** ingest today:

```bash
cd backend && python scripts/ingest_market_ohlc.py --market BTCUSD
curl -s "http://localhost:5001/api/udf/history?symbol=BTCUSD&resolution=240&from=0&to=2000000000" | head -c 500
```
