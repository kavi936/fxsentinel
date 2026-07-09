# Markets — Master Product Vision

**Status:** Living source of truth for *what Markets is*  
**Last updated:** 2026-07-08  
**How to use this doc:** Talk through each section in chat (or edit the **Your voice** blocks directly). Agents treat those blocks as product intent over engineering detail in satellite docs.

**Satellite docs** (implementation detail — do not rewrite the vision here):

| Doc | Purpose |
|-----|---------|
| [`MARKETS_BTCUSD_STRATEGY.md`](./MARKETS_BTCUSD_STRATEGY.md) | BTCUSD sprint playbook |
| [`MARKETS_TAB_PRODUCT_SPEC.md`](./MARKETS_TAB_PRODUCT_SPEC.md) | Full product/engineering spec |
| [`MARKETS_BTCUSD_DATA_AND_UI_PLAN.md`](./MARKETS_BTCUSD_DATA_AND_UI_PLAN.md) | Data → UI surface matrix |
| [`MARKETS_TAB_IMPLEMENTATION_PLAN.md`](./MARKETS_TAB_IMPLEMENTATION_PLAN.md) | Phases + file map |
| [`DASHBOARD_BRANDING.md`](./DASHBOARD_BRANDING.md) | Fonts / colors |

**Canonical ids (until you change them):** Display **`BTCUSD`** · Venue data **`BTCUSDT`** (Binance)

---

## 0. How we keep this unified

1. **This file owns product intent** — job to be done, feel, what’s in/out, priorities.
2. **Strategy / data / implementation docs own execution** — sprints, APIs, spikes.
3. When intent and docs conflict: **update this file first**, then align satellites.
4. Prefer short **Your voice** bullets over long prose. Leave blanks; we fill them together.

---

## 1. One-sentence product

> Markets is FXSentinel’s **instrument-centric research desk**: chart + our structure + platform context + one shared narrative — so a trader gets directional bias without stitching Economies, Overview, calendar, and sentiment by hand.

*(Edit freely.)*

---

## 2. Your voice — what you imagine

*(Founder: fill these in over conversation. Agents read this before building.)*

### 2.1 Who is standing in front of the screen?

- 
- Horizon: day / swing / both?
- What are they deciding in the next 60 seconds?

### 2.2 What should feel true after 10 seconds on BTC?

- 
- 
- 

### 2.3 What Markets is *not*

- 
- 

### 2.4 What makes this “ours” vs TradingView / another terminal

- Structure:
- Context from the rest of FXSentinel:
- Narrative:

### 2.5 Success for BTC as the foundation example

- Shippable when:
- Would *not* ship if missing:
- Ready to copy the shell to Gold / EUR when:

### 2.6 Open product tensions (keep debating here)

| Tension | Lean A | Lean B | Current lean |
|---------|--------|--------|--------------|
| Chart density | Structure-only by default | Structure + volume by default | Volume on (as coded) |
| News weight for BTC | Thin strip (3–5) | Heavier because crypto is news-driven | |
| Access | Developer only until polished | Staging users earlier | |
| GPT timing | After platform context + volume zones | Narrative earlier as stub | Manual → cron after stable |

---

## 3. Agreed foundation (from prior Markets work)

Keep unless you overturn it in §2.

### 3.1 Three lanes (do not blur)

| Lane | Owns | Does not own |
|------|------|--------------|
| **A — Venue quant** | Levels, zones, POC — `structured_levels[]` | Prose, probability storytelling |
| **B — Platform context** | Calendar, US scan, sentiment, news, cross-assets — composed server-side | Drawing lines on the chart |
| **C — Narrative** | Global GPT: thesis, probability, zone-tap meaning (allowlisted IDs only) | Inventing prices / new zones |

**Hard rule:** GPT never invents levels. Quant never writes prose. Platform context never draws chart lines.

### 3.2 Aggregation hub, not a silo

```text
FXSentinel platform (calendar · news · economies · sentiment · …)
        │  market profile picks slices
        ▼
Markets tab (per instrument) — referral surface for traders
```

Compose in `market_research_service` / profile wiring. Do **not** rebuild Overview/Economies inside Markets.

### 3.3 Chart-first, Markets-native UI

- Hero = **research chart** (Lightweight Charts): our bars, our overlays.
- Not a TV workstation (no user drawings / studies in v1).
- Same brand fonts/tokens; **not** Economies card-stack layout.
- Aside: Analysis · Catalysts · News (+ Flow later).

### 3.4 BTCUSD is the template

- Prove wiring on BTC first; other markets = new **profile**, same shell.
- Narrative frame (current): *Risk-on liquidity vs crypto-specific shock.*
- Cross-assets (current): ETHUSDT, SPX, VIX, US10Y, GOLD.

---

## 4. Product surface map (target)

Edit this if the screen in your head differs.

```text
┌─ Market picker ────────────────────────────────────────────┐
├─ Headline / verdict (bias · day · swing · as_of) ──────────┤
├─ Chart (hero)          │  Aside tabs                        │
│  candles + overlays    │  Analysis | Catalysts | News       │
│  TF · layers · quote   │  (+ Flow in v1.1)                  │
├─ Thesis / invalidation (when GPT run exists) ──────────────┤
└─ Footer lineage (Binance · engine version · run as_of) ────┘
```

| Surface | Belongs | Does not belong |
|---------|---------|-----------------|
| Chart | Allowlisted price structure | Funding %, full news feed |
| Aside Analysis | Bias, thesis, structure list, cross-assets, macro digest | Infinite scroll news |
| Aside Catalysts | Profile-filtered calendar | Full calendar grid from Overview |
| Aside News | 3–5 market-filtered headlines | Live News Feed cards |
| GPT only | Dense scan text, optional prediction mkts | Fake S/R prices |

---

## 5. Build priority (unified)

Order from strategy — adjust in §2.6 if you disagree.

1. **Platform context polish** — profile-driven catalysts, US scan, sentiment visible and trustworthy  
2. **Venue quant differentiation** — volume zones (POC/VAH/VAL), not only PDH/PDL  
3. **Global GPT narrative** — allowlist validator; `latest_run` drives headline when fresh  
4. **Ship BTCUSD** — access beyond developer gate, empty states, lineage  
5. **v1.1 Flow** — funding / OI / depth (after research spikes)  
6. **Market #2** — only after BTC template feels right  

**Explicitly wait:** MT5 for BTC, full liquidation heatmap, Gold/EUR enabled in picker, per-user Markets GPT.

---

## 6. Where we are (honesty check — 2026-07-08)

Rough status vs vision (update when we re-audit):

| Piece | Rough status |
|-------|----------------|
| Binance OHLC + live quote | Shipped |
| Research chart + overlays | Shipped (dev preview) |
| level_engine + volume profile path | Largely shipped in code |
| Platform context service + UI panel | Largely shipped; polish TBD |
| `profiles/BTCUSD.json` on disk | Builtin fallback; formal JSON optional |
| Global GPT / `latest_run` | Not shipped |
| Non-developer access | Gated |
| Market #2 | Not started |

---

## 7. Session log — unify as we talk

Add a row every time we lock a product call.

| Date | Decision | Why |
|------|----------|-----|
| 2026-07-08 | Created this master doc | Single place to talk through product imagination vs scattered Markets docs |
| | | |

---

## 8. Working prompts for the next chat

Use any of these to drive the conversation (copy/paste):

1. “Update §2 with my answers: …”  
2. “I’m changing the product lean: …” → update §2.6 + §7  
3. “Reconcile strategy/spec with this master after we settle X”  
4. “Walk BTC screen top→bottom against §4 and tell me what’s wrong”  
5. “What’s the smallest next build that matches §5?”  

---

## Revision log

| Date | Change |
|------|--------|
| 2026-07-08 | Initial master vision — founder voice slots + unified foundation + satellite index |
