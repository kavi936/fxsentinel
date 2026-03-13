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

