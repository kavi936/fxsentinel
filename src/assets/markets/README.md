# Market icons (bundled via Vite)

Production icons live here as **SVG** files. They are imported in `src/components/markets/marketIcons.js` so Vite emits hashed URLs at build time — no `/public/markets/` 404s.

## Files

| File | Used for |
|------|----------|
| `btcusd.svg` | BTC/USD picker chip |
| `gold.svg` | XAUUSD (coming soon) |
| `eur.svg` | EUR leg on FX pairs |
| `us.svg` | USD leg on FX pairs |
| `jpy.svg` | JPY leg on FX pairs |

## Adding a market

1. Add `yourmarket.svg` here (square, 32×32 viewBox, transparent background).
2. Import in `marketIcons.js` and add to `BUNDLED_MARKET_ICONS`.
3. Set `icon` fallback key in `marketCatalog.js` for `MarketSymbolIcon` built-in SVG.

## Format

Prefer **SVG**. PNG/WebP at **128×128** also works with Vite imports.
