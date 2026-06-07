# Market icons (bundled via Vite)

Optional folder for icons **imported** into the JS bundle (cached, hashed filenames in production).

## Files

Same naming as `public/markets/`:

- `btcusd.svg`
- `gold.svg`
- `eurusd.svg`
- `usdjpy.svg`

## Wire-up

1. Add the file here (e.g. `btcusd.svg`).
2. Open `src/components/markets/marketIcons.js` and uncomment/add the import:

```js
import btcusdIcon from '../../assets/markets/btcusd.svg';

export const BUNDLED_MARKET_ICONS = {
  BTCUSD: btcusdIcon,
};
```

3. Leave `iconPath` empty in `marketCatalog.js` for that market (bundled wins over `iconPath`).

**Build note:** The file must exist before `npm run build`, or the import will fail.

## Format

Prefer **SVG** (square, transparent). PNG/WebP at **128×128** also works.

See `public/markets/README.md` for full design specs.
