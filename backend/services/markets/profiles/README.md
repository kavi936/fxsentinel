# Market research profiles

One JSON file per enabled market id (e.g. `BTCUSD.json`).

These files define **platform context wiring** for `/api/markets/{id}/research`:

- `calendar_filter` → upcoming catalysts
- `economy_scans` → US/EU macro digest
- `news_filter` → server-side headline fallback
- `platform_context` → sentiment toggle
- `cross_assets` → aside cross-asset strip

If a profile file is missing on deploy, `market_profile.py` falls back to built-in defaults for `BTCUSD` only.

**Do not gitignore this folder** — profiles must ship with the backend.
