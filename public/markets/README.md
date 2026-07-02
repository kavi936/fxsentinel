# Market picker icons (drop-in)

Place **one icon per market** here. They are served at `/markets/<filename>` (no import required).

## Single-market icons (`iconPath`)

| Market id | File (in use) |
|-----------|----------------|
| `BTCUSD` | `bitcoin.png` |
| `GOLD` (chip label: XAUUSD) | `gold.png` |

```js
iconPath: '/markets/bitcoin.png',
```

## FX pairs — combine two currency PNGs (`iconLegs`)

Put one PNG per **currency** (not per pair):

| Currency code | File (in use) |
|---------------|----------------|
| `EUR` | `EUR.png` |
| `USD` | `US.png` |
| `JPY` | `JPY.png` |
| `DXY` | `DXY.png` (optional, not used in picker yet) |

Register new codes in `src/components/markets/marketCurrencyAssets.js`, then in `marketCatalog.js`:

```js
// EUR/USD — base currency first, quote second
iconLegs: ['EUR', 'USD'],

// USD/JPY
iconLegs: ['USD', 'JPY'],
```

The chip shows both icons overlapping (EUR top-left, USD bottom-right for EUR/USD).

## Recommended format

| Format | When to use |
|--------|-------------|
| **SVG** | Best — sharp at any size, small file. Prefer **square** artboard, transparent background. |
| **PNG** | Fine — use **64×64** or **128×128**, transparent background. |
| **WebP** | OK — same sizes as PNG. |

Avoid JPG (no transparency). Do not use huge files (keep under ~50 KB per icon).

## Design specs (picker chip)

- **Canvas:** square (1:1)
- **Display size:** 32×32 px on screen (files can be 64–128 px for retina)
- **Background:** transparent (icon sits on chip, not a white box)
- **Style:** simple mark or logo — reads clearly on **black** UI

## Legal

Use assets you have rights to (your own art, licensed icons, or generic marks). Official exchange/broker logos may need permission.

## Alternative: bundled assets

For production optimization, you can instead put files in `src/assets/markets/` and import them in `src/components/markets/marketIcons.js` (see that folder’s README).
