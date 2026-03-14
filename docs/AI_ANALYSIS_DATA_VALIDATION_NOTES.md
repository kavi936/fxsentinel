## AI Analysis Data Validation & Inputs

### Live FX Market Data (TradingView / Fallback)

- **`current_prices`**
  - **Source**: Live market ticker (TradingView), with a small static fallback table only when TradingView is unavailable.
  - **Expectation**: Values should match the prices shown in the live ticker for major FX pairs (EUR/USD, GBP/USD, USD/JPY, USD/CHF, AUD/USD, USD/CAD, etc.).

- **`recent_volatility`**
  - **Source**: Live market ticker daily absolute change per pair.
  - **Logic**:
    - Compute absolute intraday move.
    - Map to `"Low" | "Medium" | "High"` using well‑defined thresholds (e.g. `< 0.1% = Low`, `< 0.5% = Medium`, else High).
  - **Expectation**: These buckets should be directly derivable from the same data powering the live ticker.

- **`market_sentiment`**
  - **Source**: Live market ticker daily percentage change per pair.
  - **Logic**:
    - If change is very small around 0 → `"neutral"`.
    - If change is a meaningful gain → `"bullish"`.
    - If change is a meaningful loss → `"bearish"`.
    - Thresholds must be simple and explicit (e.g. > +0.1% bullish, < −0.1% bearish, else neutral).
  - **Expectation**: No extra data source; sentiment is a thin wrapper around daily % move.

### Cross‑Asset / Positioning Context

- **`bond_yields`, `equity_indices`, `commodity_prices`, `key_levels`**
  - **Current state**: All `None` from `LiveMarketDataService` by design (we do not trust any synthetic values here).
  - **Expectation**: Only populate when we have **real external data** (e.g. stable bond/indices/commodities feeds).
  - **Key levels (`key_levels`)**:
    - When reintroduced, they must be:
      - Derived from robust technical logic (e.g. multi‑day highs/lows, VWAP bands, well‑tested pivot calculations).
      - Consistent with what a trader would recognize as reasonable levels.
    - We must **not** send arbitrary or noisy levels that could mislead the user.

- **`retail_sentiment`, `futures_positioning`, `institutional_flow`**
  - **Current state**: Kept as `None` and **not included in the GPT prompt**.
  - **Expectation**: Until we have solid, real positioning feeds, these fields should be considered deprecated for GPT prompts and can be removed from the prompt layer to avoid confusion.

### Meta Market Context

- **Market open/closed & active sessions**
  - **Source**: Internal trading‑session calendar (time‑of‑day + weekday/holiday logic).
  - **Usage**: Provide:
    - Whether FX markets are currently open or closed.
    - Which major sessions are active (Asia, London, New York).
  - **Expectation**: This context is correct and low‑cost to compute; it should continue to be included.

- **VIX “fear index”**
  - **Source**: Dedicated VIX data feed (or pre‑fetched daily snapshot).
  - **Usage**: Pass current value, daily change, and a qualitative level (e.g. low/normal/elevated).
  - **Expectation**: Used to anchor volatility commentary; should always reflect a real current (or last close) value.

- **Risk appetite level & safe‑haven preference**
  - **Source**: Combination of:
    - FX pair sentiment (`market_sentiment`).
    - VIX regime.
    - Any dedicated risk‑appetite metric if available.
  - **Logic**:
    - Derive a simple **risk appetite classification** (e.g. high / normal / low) from these inputs.
    - Derive a **safe‑haven bias** (e.g. preference for USD/JPY/CHF or pro‑risk crosses) based on the same inputs.
  - **Expectation**: This is a **summary signal**, not a separate hidden feed.

- **Currency‑specific FX pair sentiment snapshot**
  - **Source**: Same underlying FX data as above (prices, % change, volatility, RSI if available).
  - **Usage**:
    - Top 2–3 most relevant pairs for the event’s currency.
    - Provide direction %, RSI, and volatility for those pairs.
  - **Expectation**:
    - Do **not** simply restate what is already in `current_prices` / `market_sentiment` line‑by‑line.
    - This snapshot should be a concise, higher‑level view (e.g. “EUR/USD and EUR/JPY both bullish with elevated volatility”).


Summary of what we changed on the Market Sentiment card and related data:

---

## Market Sentiment Card – Summary of Changes

### **Card structure and sections**
- The main block is still the **Market Sentiment** card on the Overview (left column, grid position `marketSentiment`).
- **Header**: “MARKET SENTIMENT” with info tooltip and refresh button (unchanged).
- **Content order**: (1) **Fear Indicators** (VIX + Crypto Fear & Greed), (2) **Use in Context** (expandable), (3) **Market Conditions**, (4) **Major Pairs Sentiment**, (5) **Market Drivers**.

---

### **“Fear Indicators” (renamed from “VIX Fear Indicator”)**
- **Section title**: “VIX Fear Indicator” → **“Fear Indicators”** so it covers both metrics.
- **Header tooltip**: Now describes both VIX (S&P 500 implied vol) and **Crypto Fear & Greed** (0–100, Bitcoin-based, macro risk proxy; extreme fear often bleeds into FX).
- **VIX**: Still the same UI (current value, change, level badge, bar with markers 0–15–25–35–50, labels Low/Normal/High). Data still comes from backend **`vix`** (or parsed from Volatility Environment detail).
- **Crypto Fear & Greed**: New block below VIX, same visual pattern as VIX (label, number, classification badge, bar 0–100 with markers, labels Fear/Neutral/Greed). **Source line removed.** No API key; uses Alternative.me.

---

### **Backend data and field names**
- **`vix`** (unchanged): `{ value, change, level }` – from real VIX or parsed from market conditions.
- **`fng`** (new): `{ value: 0–100, classification: string }` (e.g. `"Extreme Fear"`, `"Greed"`). Fetched in `market_sentiment_service` via `_fetch_fear_greed_index()` and added to every sentiment response (normal, fallback, market-closed).
- **Market conditions** (Volatility, Risk Appetite):
  - **`percentage`**: Now a **continuous 0–100** value (no longer only 25/50/75).
    - **Volatility**: `(VIX / 50) * 100` (clamped); fallback path uses an approximate VIX scale.
    - **Risk Appetite**: `100 - (avg_safe_haven_movement / 0.5) * 100` (clamped). Higher safe-haven move → lower percentage.
  - **`value`** (level): Still `"low" | "medium" | "high"`, but **derived from** the continuous percentage (e.g. &lt;33 → low, 33–66 → medium, ≥66 → high) so it stays in sync with the bar.
- **Pairs sentiment**: Structure unchanged (`pair`, `sentiment`, `percentage`, `price_change`, `rsi`, `volatility`). RSI logic was only evaluated and documented; your revert left the **original** RSI calculation in place (no new RSI fields).

---

### **Frontend display and bar-fill**
- **Market Conditions bars**: Use **`condition.percentage`** for bar width (clamped 0–100). Label text shows both level and numeric percentage, e.g. **“High (72.3%)”**, **“Medium Volatility (34.0%)”**.
- **Fear Indicators**: VIX and F&G both use the same layout (value + badge + bar + range labels). F&G bar is 0–100 with color from level (fear = red, neutral = orange, greed = green).

---

### **“Use in Context”**
- **Titles**: “What VIX Actually Measures” → **“What These Indicators Measure”**; “When VIX Matters for FX & Gold” → **“When They Matter for FX & Gold”**.
- **Copy**: Explains both **VIX** (equity fear, downside protection) and **Crypto Fear & Greed** (Bitcoin sentiment, macro proxy, extreme fear bleeding into forex). Bullets updated to “both” (e.g. global risk-off, VIX spike + Crypto Extreme Fear). **New correlation bullet**: “Crypto Extreme Fear → risk-off often bleeds into FX (JPY, CHF bid).”

---

### **What was reverted / not changed**
- **RSI**: No change to backend RSI calculation or to pair fields; only evaluation and a doc (`docs/RSI_CALCULATION_AND_ACCURACY_NOTES.md`) were added. You reverted code changes; when you have OHLC or real RSI, we can plug that in.

---

### **Files touched (for reference)**
- **Backend**: `backend/services/market_sentiment_service.py` (Risk Appetite/Volatility continuous %, F&G fetch, `fng` on response; RSI logic unchanged after revert).
- **Frontend**: `src/components/Overview.jsx` (Fear Indicators title + F&G block, Use in Context text, conditions label + bar using percentage).
- **Styles**: `src/components/Overview.css` (F&G block: reuse of VIX-style classes, `.fng-display` wrapper with top border).
- **Docs**: `docs/RSI_CALCULATION_AND_ACCURACY_NOTES.md` (RSI accuracy and data limits; no code dependency).

That’s the full set of card, field names, and data changes in one place.    

### Economy / Policy Context

- **Event‑to‑indicator mapping**
  - **Requirement**: For events where we provide economy context, we must have a **reliable mapping** from the event title → indicator IDs (e.g. CPI, NFP, unemployment).
  - **Expectation**:
    - Only include economic context when that mapping exists.
    - For unmapped events, skip the ECONOMIC CONTEXT section rather than guessing.

- **Current macro indicators (per currency economy)**
  - **Focus**:
    - Unemployment.
    - CPI / inflation measures.
    - GDP and growth proxies.
    - Policy rate and recent rate path.
  - **Expectation**:
    - These values must come from a trusted, pre‑fetched dataset or cache.
    - GPT should reference these explicit numbers when explaining context.

- **Historical / statistical context**
  - **Focus**:
    - Where current readings sit vs historical averages / ranges.
    - How volatile or unusual the latest prints are.
  - **Expectation**: GPT should be instructed to emphasize:
    - “Current CPI is X% vs historical average Y%” style language.
    - Contextualizing the event relative to history, not just the last print.

- **Central bank policy target view**
  - **Focus**:
    - Are we above/below inflation/unemployment targets?
    - Policy pressure direction (toward hikes, cuts, or hold).
    - Current rate vs neutral/target range.
  - **Expectation**:
    - GPT uses these values to reason about policy trajectory, not just current rate in isolation.

- **Policy‑trajectory notes**
  - **Source**:
    - Derived from the same economy context dataset (targets, current levels, recent path).
  - **Expectation**:
    - The prompt should make it explicit that any “policy trajectory” commentary must tie back to **concrete target vs actual** relationships, not generic guesses.

### Economies tab data → AI injection (indicator mapping)

- **Data source for AI**
  - Economy context used in the GPT prompt comes from **`src/data/economyIndicators.json`** (same structure the Economies tab can use as fallback).
  - The backend does **not** call the Economies API (Google Sheets) for AI analysis; it uses this static JSON via **`backend/services/economy_context_service.py`** (`EconomyContextService.get_economy_context(currency)`).
  - So: keep **`economyIndicators.json`** in sync with the data you want GPT to see (or switch the service to use the API later).

- **Event title → indicator IDs**
  - **Currency-aware mapping** in **`backend/services/gpt_ai_analysis.py`**:
    - **Event currency** (from the calendar event) is used first. Only **USD, EUR, GBP, JPY** have economy context; other currencies get no indicator injection.
    - **Title → concepts**: `TITLE_KEYWORD_TO_CONCEPT` maps substrings in the event title (lowercased) to **concepts** (e.g. `'cpi'` / `'inflation'` → `inflation`, `'payrolls'` / `'unemployment'` → `employment`, `'gdp'` → `gdp`, `'fund rate'` / `'fomc'` → `rate`, `'average earnings'` → `wage_growth`, `'current account'` → `current_account`). Multiple concepts can match (e.g. "CPI and unemployment").
    - **Concept → indicator IDs per economy**: `CONCEPT_TO_INDICATORS_BY_CURRENCY` maps each concept to the **indicator IDs that exist in `economyIndicators.json` for that economy**. So e.g. inflation → US: `['inflation-YoY', 'core-inflation-YoY']`, EUR/GBP/JPY: `['inflation', 'core-inflation-YoY']`; employment → US: `['unemployment', 'nonfarm-payrolls']`, EUR/GBP/JPY: `['unemployment']`; wage_growth only for GBP: `['wage-growth']`; current_account only for EUR/JPY: `['current-account']`.
    - **`_get_relevant_indicators(event_title, currency)`** returns only indicator IDs that exist for that economy, so there are **no "missing" IDs** when the event is for a supported currency.
  - **Legacy** `EVENT_TYPE_MAPPING` remains for fallback when currency is missing or unsupported; the service still filters requested IDs by what exists in the JSON for that currency.

- **Per‑currency indicator IDs**
  - **US**: typically has `interest-rate`, `inflation-YoY`, `core-inflation-YoY`, `gdp-growth`, `unemployment`, `nonfarm-payrolls`.
  - **EUR / GBP / JPY**: may use `inflation` instead of `inflation-YoY`, and often do **not** have `nonfarm-payrolls` (US‑specific). So for CPI/inflation events they still get `core-inflation-YoY` + `interest-rate` if present; for NFP they get `unemployment` + `interest-rate`.
  - To get **good mapping** for all economies: either add the same indicator IDs to each country in the JSON where they exist, or add a currency‑aware mapping layer (e.g. for EUR map “inflation” event to `inflation` ID when currency is EUR).

- **Testing the mapping**
  - Run the validation script from repo root:
    - `python3 backend/scripts/test_economy_indicator_mapping.py`
  - It prints:
    1. Which indicator IDs exist per currency in the JSON.
    2. Sample event titles → which indicator IDs are requested.
    3. For each sample and currency, which requested IDs were found vs missing.
    4. Alignment summary: which mapped IDs are present or missing per currency.
  - **If “missing” appears**: with currency-aware mapping this should not happen for USD/EUR/GBP/JPY; if it does, add the indicator to `CONCEPT_TO_INDICATORS_BY_CURRENCY` for that economy or fix the concept→indicator list.
  - **If an event returns `[]`**: add a (keyword, concept) pair to `TITLE_KEYWORD_TO_CONCEPT` (e.g. `'rate decision'` or `'fund rate'` for central bank rate events) so that event title matches and the right indicators are requested.

### Internal Scenario / Meta Parameters

- **`time_to_event`**
  - **Usage**: Indicates time until (or since) the event; currently often set to 3600 seconds as a simple default.
  - **Expectation**: Good to keep; can be refined to use real event timestamps in future.

- **`liquidity_level`**
  - **Usage**: 1 = High, 2 = Medium, 3 = Low.
  - **Current**: Often set to 2 (medium).
  - **Concern**: May duplicate information also expressed via VIX, risk appetite, and trading sessions.
  - **Expectation**:
    - If kept, it should be derived from those same inputs (sessions, VIX, volumes if available) and treated as a **summary label**, not an independent mysterious input.

- **`scenario_probabilities` (`higher` / `lower` / `inline`)**
  - **Current default**: Approx. 30% / 50% / 20%, used as scaffolding in instructions.
  - **Expectation**:
    - GPT should not simply parrot these fixed numbers.
    - The prompt should nudge GPT to **infer realistic ranges** based on:
      - Event importance and impact.
      - Current macro skew (e.g. inflation above/below target).
      - Market pricing / expectations where available.
    - These probabilities should look like genuine reasoning, not a bluff fixed template.

### New Data to Integrate

- **Prediction Markets**
  - **Source**: New prediction markets feature in the app (probabilities of events such as rate moves, macro prints, etc.).
  - **Usage**:
    - Provide market‑implied probabilities for key scenarios (e.g. next rate hike/cut, specific print ranges).
    - Use them to inform:
      - Scenario probabilities (align or contrast with prediction markets).
      - Policy trajectory commentary (e.g. “markets price a 70% chance of a cut within 3 months”).
  - **Expectation**:
    - This data should be surfaced explicitly in the prompt as **market‑implied odds**, not hidden.

Summary of what was implemented:
1. backend/services/prediction_markets_context.py (new)
get_central_bank_context(central_bank, horizon_days=120, max_markets=5)
Uses prediction_markets_service.cached_markets.
Keeps Polymarket markets whose question/event_title/event_slug match the bank’s keywords (e.g. Fed: fed, federal reserve, fomc, powell).
Keeps markets with resolution_date within the horizon (future and last 30 days).
Sorts by active first, then volume and conviction; returns top max_markets.
Returns:
{ "provider": "prediction_markets", "as_of": "<iso>", "central_bank": "Fed", "markets": [ { "id", "question", "yes_probability", "price_delta_24h", "volume", "resolution_date", "conviction_level" }, ... ] }.
get_event_context(event_type, country, date=None, max_markets=3)
Filters by event_type (CPI, NFP, GDP, RATE_DECISION) and optional country.
Returns the same kind of structured payload for macro events.
get_fx_pair_context(pair, max_markets=7)
Maps pair (e.g. EURUSD, GBPUSD) to central banks (Fed, ECB, BOE, BOJ, SNB, BOC, RBA, RBNZ), calls get_central_bank_context for each, merges and dedupes by market id.
format_central_bank_context_for_prompt(payload)
Turns a get_central_bank_context result into a short text block for prompt injection (e.g. “Prediction market expectations (Polymarket, as of …): Fed: …”).
Central banks supported: Fed, ECB, BOE, BOJ, RBNZ, BOC, RBA, SNB.
2. backend/services/central_bank_ai_context.py (updated)
get_prediction_markets_context_for_currency(currency, max_markets=5, horizon_days=120)
Maps currency (USD, EUR, …) to bank (FED, ECB, …), then to prediction_markets bank name (Fed, ECB, …), calls get_central_bank_context and format_central_bank_context_for_prompt, returns the string.
get_context_for_currency(..., include_prediction_markets=True)
When include_prediction_markets is True (default), appends the prediction-markets string to the central bank document context. So a single call returns both document summaries and Polymarket expectations for that currency.
get_context_for_prompt(..., include_prediction_markets=True)
When True (default), for each distinct bank in the matched documents (up to 3), appends that bank’s prediction market block so multi-currency prompts get Fed/ECB/BOE etc. expectations.
Sample prompt usage
Added a short comment at the bottom of the file showing how the injected text looks and that the model should use prediction markets as one input and state when it relies on them.
3. Usage
Single currency (e.g. USD):
get_context_for_currency("USD", include_prediction_markets=True) → document context + Polymarket Fed expectations.
Multi-currency / general prompt:
get_context_for_prompt(currencies=["USD","EUR"], include_prediction_markets=True) → document context + Fed and ECB prediction market blocks.
Structured only (e.g. for your own prompt):
from services.prediction_markets_context import get_central_bank_context, get_event_context, get_fx_pair_context
Then call get_central_bank_context("Fed"), get_event_context("CPI","US"), or get_fx_pair_context("EURUSD") and use the returned dict in your pipeline or serialize it yourself.
All of this uses the existing cached markets from the prediction markets service; no extra API calls. If the cache is empty, the prediction-market section is empty and the rest of the context is unchanged.
    

- **Central Bank Analysis**
  - **Source**: The existing Central Bank Analysis feature (summaries of recent speeches, decisions, guidance).
  - **Usage**:
    - Provide a concise summary of:
      - Latest stance and guidance.
      - Key themes (e.g. “data‑dependent”, “higher for longer”, “concerned about inflation persistence”).
    - Use this to refine:
      - Policy implications section.
      - Policy‑trajectory reasoning.
  - **Expectation**:
    - Notes should come from your structured Central Bank Analysis data (not from GPT guessing).
    - Prompt should clearly label these as “central bank communication context” and require GPT to reconcile event outcomes with that stance.

Here’s what’s in place:
1. Location (backend only, not user-facing)
Item	Path
AI context data	backend/data/central_bank_documents_ai_context.json
Python helper	backend/services/central_bank_ai_context.py
Docs	docs/CENTRAL_BANK_AI_CONTEXT.md
The AI context file is not in public/ or src/, so it is not bundled or served to the frontend and is only used by the backend.
2. Structure of central_bank_documents_ai_context.json
Per document:
shortSummary: 1–2 sentence summary for prompts
aiNotes: list of short, factual statements
topics: topic tags for filtering (e.g. inflation, policy_normalization, fomc)
All 11 existing central bank documents are populated with these fields.
3. Using it in your AI code
from backend.services.central_bank_ai_context import (    get_context_for_currency,    get_context_for_prompt,)# For a USD event (e.g. NFP):ctx = get_context_for_currency("USD", max_docs=3, max_notes_per_doc=5)# → "CENTRAL BANK DOCUMENT CONTEXT:\n- FED (fed-2026-01-28-fomc-statement):\n  Summary: ...\n  Notes: ..."# For multi-currency or topic-based filtering:ctx = get_context_for_prompt(    currencies=["JPY", "EUR"],    topics=["inflation", "policy_normalization"],    max_docs=5,)
Then append ctx to the system or user prompt where you call the model.
4. Wiring it into your analyzers (calendar AI analysis – implemented)
- **gpt_ai_analysis.py**: In `_create_analysis_prompt()`, central bank document context and prediction market expectations are injected for the **event’s currency**:
  - Call: `get_context_for_currency(currency, max_docs=3, max_notes_per_doc=5, include_prediction_markets=True)`.
  - The result is inserted as a separate block **after** ECONOMIC CONTEXT and **before** MARKET CONTEXT, under the heading: "CENTRAL BANK & PREDICTION MARKET CONTEXT (use for policy stance and market-implied expectations)".
  - The model is instructed (PRIMARY ANALYSIS REQUIREMENTS, item 2) to: (1) use central bank docs for policy stance, recent communication, and key themes, and to reconcile the event outcome with that stance; (2) use prediction markets as one input among others, to cite them when relying on them (e.g. "Market-implied probability of a cut is X%"), and not to present market-implied probabilities as the model’s own forecast.
- For unsupported currencies, `get_context_for_currency` returns an empty string and no block or instruction is added.
- **enhanced_ai_analysis.py** and **enhanced_trader_analysis.py**: Same pattern can be applied when building their prompts if they need central bank + prediction market context.
5. Adding new documents
When you add a document to public/central-bank-documents.json:
Add an entry for that document’s id in backend/data/central_bank_documents_ai_context.json (inside the documents object).
Add its doc_id and bank to _DOC_ID_TO_BANK in central_bank_ai_context.py.
docs/CENTRAL_BANK_AI_CONTEXT.md has full details and a full integration example.
