# FXSentinel dashboard — styling & branding reference

**Purpose:** Single reference for **Markets tab** (and future tabs) so we reuse **fonts and brand tokens**, not duplicate Overview/Economies card layouts.

**Source of truth in code:** values below are extracted from `src/App.css`, `src/index.css`, `src/components/Dashboard.css`, `Overview.css`, `Economies.css`, `Alerts.css` (June 2026).

---

## 1. Brand palette

| Token | Hex / value | Used for |
|-------|-------------|----------|
| **Primary black** | `#000000` | Tab backgrounds (Overview full bleed, Economies, Alerts); Markets canvas target |
| **Secondary black** | `#0a0a0a` | Gradients, depth |
| **Dark gray** | `#1a1a1a` | Focus states, panels |
| **Medium gray** | `#2a2a2a` | Scrollbar track |
| **Border** | `#333333` (`--border-color`) | Dividers |
| **Text primary** | `#ffffff` | Body, headings |
| **Text muted** | `#cccccc` (`--text-gray`) | Nav tabs inactive, secondary labels |
| **Accent red** | `#ff4444` (`--accent-red`) | Brand accent, CTAs, active nav glow |
| **Accent red dark/light** | `#cc3333` / `#ff6666` | Hover variants |

**CSS variables (global):** defined in `src/App.css` `:root` — prefer these in new Markets CSS:

```css
var(--primary-black);
var(--accent-red);
var(--text-white);
var(--text-gray);
var(--border-color);
```

---

## 2. Typography

| Context | Font stack | Where |
|---------|------------|--------|
| **App / body default** | `'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif` | `App.css` `body`, `Dashboard.css` |
| **index.css tokens** | `--font-sans: 'Inter', system-ui, …` | Loaded via `index.html` |
| **Economies card headers** | `'Sen', 'SF Pro Display', -apple-system, …` | `Economies.css` `--economies-card-header-font-family` |
| **Monospace (timestamps, codes)** | `'Courier New', monospace` | e.g. `MarketStatusPopup.css` |

**Markets recommendation:** Use **Inter / system stack** (same as Dashboard navbar). Sen is optional for section titles if you want Economies-like headers— not required on black canvas.

| Element | Typical size | Weight |
|---------|--------------|--------|
| Nav tab | `0.85rem` | 500 inactive / 600 active |
| Section label (uppercase) | `0.7rem` | 700, letter-spacing `0.1–0.12em` |
| Body | `0.875–0.9rem` | 400–500 |
| Muted meta | `0.68–0.72rem` | 500 |

---

## 3. Dashboard chrome (shared across tabs)

### 3.1 Page offset

Fixed navbar ~**60px**. Full-screen tabs use:

```css
padding-top: 80px; /* 60px nav + breathing room */
```

See `Economies.css` `.economies-content`, Markets skeleton `.markets-content`.

### 3.2 Dashboard shell background

- Default `.dashboard`: dark **gradient** (not flat black):  
  `linear-gradient(135deg, #000000 0%, #0a0a0a 25%, #1a1a1a 50%, #0f0f0f 75%, #000000 100%)`
- **Economies active:** `.dashboard.economies-active { background: transparent }` so tab owns `#000`.

**Markets:** Use **flat `#000`** for the tab (like Economies), not the dashboard gradient—navbar still sits on Dashboard wrapper.

### 3.3 Nav tabs

| State | Style |
|-------|--------|
| Inactive | `color: #cccccc`, transparent bg |
| Hover | `rgba(255,255,255,0.08)` |
| **Active** | Red gradient bg `rgba(255,68,68,0.3→0.2)`, white text, light red shadow |

Do not redesign navbar for Markets; tab content starts below it.

---

## 4. Tab-specific patterns (reference only — do not clone wholesale)

### 4.1 Overview

- Full bleed `#000` on main areas
- **Cards / grids:** gradient panels  
  `linear-gradient(135deg, #0f0f0f 0%, #1a0a0a 25%, #1e0505 50%, …)` + border `1px solid rgba(255, 68, 68, 0.1)` + blur shadow
- **Bullish move green:** `#00ff88` (ticker / gauge — not the same as accent red)

### 4.2 Economies

- Tab bg: **`#000000`**
- **Pills / chips:** `rgba(255,255,255,0.05)` bg, `rgba(255,0,0,0.2)` border, `backdrop-filter: blur(10px)`, radius `20–25px`
- **Holistic scan CTA:** red gradient button (see `.holistic-scan-button`)
- Long-form analysis: emphasis utilities in `analysisEmphasis` (shared with AI copy)

### 4.3 Alerts

- Tab bg `#000`, Inter stack, red left borders on alert severity

---

## 5. Semantic colors (market / bias)

Use consistently when Markets shows bias or % change:

| Meaning | Color (current app) | Notes |
|---------|---------------------|--------|
| Bullish / up | `#00ff88`, `#4ade80`, `#86efac` | Overview vs newer greens vary—pick one set for Markets |
| Bearish / down | `#f87171`, `#ff4444`, `#fca5a5` | Align with brand red family |
| Neutral / lean | `#fde68a`, amber borders | Holistic / bias pills |

Document chosen Markets tokens in `MarketsLayout.css` when you lock them.

---

## 6. TradingView chart benchmark (Markets)

Not the same as dashboard cards:

- Background: **`#000000`** or TV default dark
- Grid: low-contrast white `~3–4%` opacity
- Candles: green up / red down (TV convention)
- Level lines: red / green / amber for R/S/POI—keep legend readable on black

See `docs/TRADINGVIEW_API_ACCESS_GUIDE.md` for Lightweight Charts.

---

## 7. What Markets should reuse vs avoid

| Reuse | Avoid |
|-------|--------|
| `--primary-black`, `--accent-red`, `--text-*` from `App.css` | Overview gradient **card** stacks |
| `padding-top: 80px` under navbar | Coming-soon orbs / animated red marketing bg |
| Nav tab active state (unchanged) | Copying `economies-main-card` layout |
| Optional `analysisEmphasis` for GPT prose blocks | Full `LiveNewsFeed` card UI |
| Bias semantic colors (pick one green) | Per-user “your analysis” framing |

---

## 8. Market picker icons

| Location | How |
|----------|-----|
| **Drop-in (easiest)** | `public/markets/btcusd.svg` → `iconPath: '/markets/btcusd.svg'` in `marketCatalog.js` |
| **Bundled** | `src/assets/markets/btcusd.svg` → import in `marketIcons.js` |

Specs: square SVG or PNG 64–128px, transparent background. See `public/markets/README.md`.

---

## 9. Markets tab modes (implementation)

| Mode | File entry | Use |
|------|------------|-----|
| **Canvas (current)** | `MarketsHub.jsx` → empty `.markets-canvas` | Phase 0 creativity; build top→bottom |
| **Section skeleton (archived)** | `MarketResearch.jsx`, `mockBtcusdResearch.json` | Re-enable sections one at a time when layout is decided |

---

## 10. Building Markets top → bottom (suggested order)

1. **Top bar** — instrument selector, updated time, optional run badge  
2. **Chart region** — black box → later Lightweight Charts  
3. **Verdict strip** — bias + day/swing + price  
4. **Side column or stack** — cross-asset, news, catalysts  
5. **Thesis + invalidation** — prose blocks  

Add each block to the canvas only when you are happy with the space above it.

---

## Revision log

| Date | Change |
|------|--------|
| 2026-06-03 | Initial extract from dashboard CSS for Markets Phase 0 |
