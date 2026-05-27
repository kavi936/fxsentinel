# FXSentinel — AI Analysis Output Review
**Document Type:** Internal Development Reference
**Scope:** Economic Calendar, Live News, and Holistic Scan analysis sections
**Purpose:** Critique of current AI prompt structure and output quality, with actionable improvement recommendations for each section and cross-cutting issues that apply globally.

---

## Table of Contents
1. [Cross-Cutting Issues (All Sections)](#1-cross-cutting-issues-all-sections)
2. [Economic Calendar Analysis](#2-economic-calendar-analysis)
3. [Live News Analysis](#3-live-news-analysis)
4. [Holistic Scan](#4-holistic-scan)
5. [Prompt Improvement Templates](#5-prompt-improvement-templates)
6. [Priority Action List](#6-priority-action-list)

---

## 1. Cross-Cutting Issues (All Sections)

These problems appear in **all three** analysis sections and should be addressed at the system/prompt level before section-specific fixes.

---

### 1.1 Generic Language — No Actionable Conditionals

**Problem:** Across all three sections, the AI uses passive observational language that describes a situation without telling the trader what to do about it.

Examples seen:
- *"Monitor upcoming inflation indicators"*
- *"Watch EUR/USD closely"*
- *"Consider swing trading strategies"*
- *"Traders should remain vigilant"*

This language has zero trading utility. A trader reading during a live session needs a conditional trigger — not a reminder to pay attention.

**Fix:** Every analysis section must include at minimum one **"If X → then Y"** statement. Replace observational language with conditional action framing.

> Example replacement: *"If print exceeds 0.3%, expect EUR/USD to test 1.1580 — a sustained break below would confirm USD bullish follow-through."*

---

### 1.2 Unexplained Confidence Scores

**Problem:** Confidence scores appear in both the Economic Calendar (90%) and Holistic Scan (60%) with no methodology behind them. They read as auto-generated placeholders.

Worse: In the Holistic Scan, the scan reliability is flagged as **POOR** (indicators 28 days stale), yet the confidence score remains unchanged at 60%. This is a direct contradiction that erodes trust.

**Fix:**
- Define confidence scoring methodology (e.g. data freshness weighting, consensus spread, historical volatility of the release)
- Make confidence **dynamically responsive** to data staleness
- If data is stale, reduce the displayed confidence score and state explicitly why it was reduced

---

### 1.3 Price Levels Cited Without Justification

**Problem:** All three sections reference price levels (e.g. EUR/USD 1.16392, 1.1600 support, USD/JPY 159.397) without explaining their significance. Are these daily pivots? Prior swing highs/lows? Round numbers? Session opens?

Without context, these numbers are arbitrary and potentially misleading.

**Fix:** Every price level cited must carry a one-word or short qualifier explaining its basis.

> Example: *"EUR/USD 1.1600 (prior weekly support)"* or *"USD/JPY 159.40 (current spot anchor)"*

---

### 1.4 Personalization Is Acknowledged But Not Executed

**Problem:** All three sections reference trader personalization (swing profile, currency preferences, trading style) in the header or metadata — but the body of the analysis remains generic. The personalization label is cosmetic.

Specifically:
- Holistic Scan detects swing-trading profile and says "prioritize long-term regime" — but the long-term section is equally thin as the short-term section
- Live News flags EUR/USD as the key pair regardless of the trader's actual preferred pairs
- Economic Calendar doesn't adjust strategy framing for trader type (swing vs. scalper vs. position)

**Fix:** Personalization must cascade into the output structure itself:
- Swing trader → long-term section is structurally deeper, short-term treated as noise filter
- Scalper → immediate reaction and volatility spike framing prioritised
- Currency preference → only pairs relevant to the trader are surfaced; irrelevant pairs are excluded or pushed to a secondary section

---

### 1.5 Overuse of "NEUTRAL" Label — Loss of Signal

**Problem:** In all three sections, NEUTRAL is applied broadly to situations that actually have directional lean. When everything is NEUTRAL, the label loses meaning and traders stop reading it.

Examples:
- Holistic Scan: both short-term AND long-term scores are NEUTRAL, all four pairs are NEUTRAL
- Live News: Immediate reaction labelled NEUTRAL while body text describes "downward pressure on the euro" and "tempered bullish sentiment" — a clear bearish lean
- Economic Calendar: Neutral scenario defined so narrowly (exactly 0.3%) it is nearly impossible to trigger

**Fix:** Introduce sub-classifications:
- **NEUTRAL-BULLISH LEAN** — score or narrative tilts positive but lacks conviction
- **NEUTRAL-BEARISH LEAN** — score or narrative tilts negative but lacks conviction
- **TRUE NEUTRAL** — balanced drivers, genuinely no directional read

Force internal consistency: if the narrative implies a direction, the label must match.

---

### 1.6 Narrative and Quantitative Output Are Disconnected

**Problem:** In the Holistic Scan particularly, critical geopolitical themes (Hormuz closure labelled CRITICAL, energy shock) exist in the narrative but have no visible effect on the regime scores. A trader reading both will ask: "If this is CRITICAL, why is the score only -16?"

The same pattern appears in the Economic Calendar — market reaction section references strong USD moves but the probability scenarios don't fully reflect this.

**Fix:** Require the prompt to include a **bridge rule**: any theme flagged as CRITICAL or ELEVATED must either (a) show a measurable contribution to the composite score, or (b) include an explicit sentence explaining why it is being discounted in the score (e.g. offset by a countervailing factor).

---

## 2. Economic Calendar Analysis

**Test Event:** Core PCE Price Index m/m

---

### 2.1 Probability Scenarios Don't Sum to 100%

**Problem:** The three probability ranges given are:
- Bullish: 40–50%
- Neutral: 20–30%
- Bearish: 30–40%

These ranges overlap and don't sum cleanly to 100%. At minimum they sum to 90%, at maximum 120%. This is a basic mathematical error that will undermine trader trust immediately, especially alongside a "90% Analysis Confidence" claim.

**Fix:** Instruct the AI to output **single integer probabilities that must sum to exactly 100%**. If ranges are preferred for communicating uncertainty, define non-overlapping bands (e.g. 35–45% / 20–25% / 30–40% with explicit note they represent estimate spread, not simultaneous possibilities).

---

### 2.2 Neutral Scenario Trigger Is Unrealistically Precise

**Problem:** The neutral scenario is defined as "print is exactly 0.3%." In reality, a 0.2% or 0.3% print may both be read by the market as "in-line." Defining neutral as a single data point makes this scenario statistically near-zero and practically useless.

**Fix:** Define the neutral zone as a **range**, informed by historical standard deviation of the release and current consensus spread.

> Example: *"Neutral: print between 0.25%–0.35%, within one standard deviation of consensus — limited market reaction expected."*

---

### 2.3 "90% Analysis Confidence" Is Unanchored

**Problem:** No methodology is provided for why this event receives 90% confidence. Is it based on: historical consistency of this release? Strength of consensus? Analyst survey spread? Fed's recent communication clarity?

Without a basis it reads as a default placeholder.

**Fix:** Tie confidence to measurable inputs. Suggested factors:
- Consensus analyst spread (tight = higher confidence)
- Fed's recent explicit guidance on this indicator
- Historical market sensitivity to this specific release
- Data availability and freshness

---

### 2.4 Trading Plan Lacks Specific Structure

**Problem:** The trading plan section says:
- *"Consider swing trading strategies on USD pairs"*
- *"Avoid aggressive short-term trades immediately post-release"*
- *"Key levels: anchored to current spot"*

None of these are a trading plan. A trader needs: entry condition, directional trigger, approximate target, and stop logic — even if framed conditionally.

**Fix:** Require the trading plan section to follow a structured template:

```
If [scenario trigger]:
  Direction: [long/short which pair]
  Entry condition: [price action confirmation or level break]
  Target zone: [approximate level with basis]
  Invalidation: [what price action would kill the thesis]
  Sizing note: [any volatility-adjusted guidance]
```

---

### 2.5 Key Levels Are Just Spot Prices

**Problem:** EUR/USD 1.16392 and USD/JPY 159.397 are listed as "key levels" but are simply current spot prices at time of generation. Anchoring to spot is not technical analysis — it's a timestamp.

**Fix:** Pass real technical levels (prior session high/low, weekly pivots, significant round numbers, recent swing points) into the prompt from your data layer, and require the AI to reference these instead of spot.

---

## 3. Live News Analysis

**Test Event:** ECB/Guindos growth warning headline

---

### 3.1 Reaction Label Contradicts Body Text

**Problem:** The immediate reaction is labelled **NEUTRAL**, but the analysis body states:
- *"downward pressure on the euro"*
- *"temper the bullish sentiment"*
- *"dovish ECB expectations"*

This is a bearish lean, not neutral. A trader making a fast decision on a live news event reads the label first — if it says NEUTRAL but the text is bearish, the output is actively misleading.

**Fix:** Implement a consistency rule in the prompt: **the reaction label must match the directional lean of the body text**. If the body implies bearish, label must be BEARISH or BEARISH-LIGHT. Only use NEUTRAL when the analysis is genuinely balanced across both directions.

---

### 3.2 Trader's Pair Preferences Are Not Reflected

**Problem:** This section is described as tailored to the trader's onboarding profile and currency preferences — but the output references EUR/USD without any check against whether this trader actually trades EUR/USD.

If a trader's profile shows they trade GBP/USD and USD/CAD, the entire output is irrelevant noise. No filtering has occurred.

**Fix:**
- Always pass trader's active pairs into the prompt explicitly
- Instruct the AI to open with: *"Based on your active pairs, [X] is the most relevant to this event"*
- If the news event has no direct relevance to the trader's pairs, say so explicitly rather than forcing a connection

---

### 3.3 No Actionable Trigger Defined

**Problem:** The trading implications section ends with: *"monitoring sentiment indicators and ECB communications will be crucial in the next 2–4 hours."*

This tells the trader nothing they couldn't infer themselves. There is no trigger condition, no confirmation signal, no specific action.

**Fix:** Require a **"What triggers a trade"** field in the output — one sentence that defines the specific price action or confirmation that would warrant acting on this news:

> Example: *"A sustained break below EUR/USD 1.1620 in the next 30 minutes, on above-average volume, would confirm bearish follow-through from Guindos' comments."*

---

### 3.4 Support Level Cited Without Context

**Problem:** *"Key levels such as 1.1600 support"* — why is 1.1600 support? Prior low? Round number? Daily pivot? Without this context the level is arbitrary.

**Fix:** Same as the cross-cutting level justification fix — all levels must carry a short basis label. Ideally sourced from your data layer rather than AI-generated.

---

### 3.5 Correlation Risk Label Is Meaningless Without Specificity

**Problem:** The risk assessment shows **Correlation Risk: MEDIUM** with no explanation of which correlations are elevated or why.

**Fix:** If correlation risk is flagged, name the specific correlations relevant to the event:

> Example: *"Correlation risk: EUR/CHF may move in tandem — ECB growth concerns historically spill into CHF safe-haven demand. Monitor EUR/CHF for divergence signals."*

---

## 4. Holistic Scan

**Test Economy:** United States

---

### 4.1 Composite Scores Are Unexplained Black Boxes

**Problem:** Short-term score: -16.21, Long-term score: -13.37. A trader has no idea:
- What the scale is (-100 to +100? -50 to +50?)
- What constitutes neutral, bearish, or bullish territory
- What each sub-component contributed to the total
- Why two scores covering different time horizons are so close to each other

The false precision of ".21" and ".37" actually increases distrust — it implies mathematical rigour that isn't explained anywhere.

**Fix:**
- Define and display the score scale explicitly (e.g. *"-100 (extreme bearish) ↔ 0 (neutral) ↔ +100 (extreme bullish)"*)
- Show score as a position on that band, not just a number
- Display a component contribution table showing what each driver contributed numerically to the composite

> Example output format:
> ```
> Score: -16.21 / 100-point scale
> Neutral band: -20 to +20
> Position: Low-neutral, bearish lean
>
> Component contributions:
>   Rate momentum:      -8.4  (negative)
>   Growth momentum:    -6.2  (negative)
>   Inflation momentum: +4.1  (positive)
>   [etc.]
> ```

---

### 4.2 Confidence Does Not Reflect Data Staleness

**Problem:** Both regime scores carry 60% confidence. However, the scan reliability is flagged as **POOR** with the oldest indicator 28 days behind UTC. These two outputs directly contradict each other.

If the data is stale, the confidence should be lower. Presenting unchanged confidence while simultaneously warning about staleness creates an unresolvable signal conflict for the trader.

**Fix:**
- Build a staleness → confidence penalty mapping into the prompt logic
- Example rule: *"If oldest indicator > 14 days, reduce confidence by 10%. If > 21 days, reduce by 20%. If > 28 days, flag as LOW CONFIDENCE and add a visible disclaimer to each score."*
- The stale data warning in the header must cascade into every score and pair bias it affects

---

### 4.3 All Pairs Have Identical Commentary

**Problem:** All four pairs (EUR/USD, USD/JPY, GBP/USD, AUD/USD) have near-identical analysis:
- Range conditions prevail
- Monitor for geopolitical breaks
- Conviction reduced — inputs stale
- Invalidation: USD safe-haven bid

Each pair's analysis should be driven by the macroeconomic factors most specific to that pair's base/quote currencies. JPY is a safe-haven currency with BoJ policy specifics. AUD is a commodity currency with China exposure. GBP has UK-specific macro dynamics. None of this differentiation is present.

**Fix:** Require the prompt to generate pair-specific commentary driven by each currency's known sensitivities:
- JPY: risk-off flows, BoJ yield curve control status, Hormuz oil shock impact on Japan as energy importer
- AUD: commodity channel, China demand indicators, RBA policy stance
- GBP: UK growth/inflation divergence from US, BoE forward guidance
- EUR: ECB policy stance, European energy exposure, strategic autonomy divergence from USD

---

### 4.4 Critical Geopolitical Risk Not Reflected in Score

**Problem:** The Strait of Hormuz closure is labelled **CRITICAL** and described in significant detail — yet the regime scores sit at only -16 and -13 (within what appears to be a neutral band). A trader will reasonably ask why a CRITICAL geopolitical event produces a near-neutral score.

There is no bridge between the narrative and the quantitative output.

**Fix:** Require an explicit **score-narrative bridge sentence** whenever a CRITICAL or ELEVATED theme is present:

> Example: *"The Hormuz closure contributes approximately -8 to the composite score. The offset comes from the USD safe-haven bid (+6) and AI capex-driven growth resilience (+4), which partially neutralise the geopolitical drag — keeping the score in bearish-neutral territory rather than outright bearish."*

---

### 4.5 Swing Trader Personalization Is Not Executed in Output

**Problem:** The scan correctly identifies a swing-trading profile and states *"prioritize long-term regime and macro follow-through"* — but the long-term section receives no more depth, space, or structural emphasis than the short-term section.

For a swing trader, the short-term section should function as a noise filter (is now a bad time to enter a longer-term thesis?), while the long-term section should be the primary analysis with multi-week setup framing.

**Fix:** When swing-trading profile is detected, the output structure should change:
- Long-term section: expanded with multi-week directional thesis, macro follow-through narrative, and 3–12 month scenario framing
- Short-term section: condensed to a "current entry conditions" note — is the short-term regime aligned or opposed to the long-term thesis?
- Language: shift from "next 2–4 hours" to "over coming weeks/months"

---

### 4.6 Stale Data Warning Is Not Acted Upon

**Problem:** *"Inputs are stale — reduce conviction and refresh frequently"* appears in the header but produces no downstream effect on any output. Scores, confidence levels, and pair biases are presented identically to how they would appear with fresh data.

A warning that changes nothing is not a warning — it's a disclaimer that protects the system without protecting the trader.

**Fix:** Staleness must have concrete, visible consequences in the output:
- Confidence scores reduced (see 4.2)
- Each pair bias marked with a staleness flag visible at the pair level
- Score displayed with an uncertainty band rather than false precision
- A "last reliable as of [date]" timestamp shown prominently, not buried in source references

---

## 5. Prompt Improvement Templates

### 5.1 Economic Calendar — Additional Prompt Fields to Add

```
- Consensus range (min/max analyst estimates, not just central estimate)
- Previous 3 prints for this release
- Historical average market move on this release (pips, % move)
- Fed's current stated threshold or target for this indicator
- Instruction: probabilities must be single integers summing to 100
- Instruction: neutral zone must be a range, not a single value
- Technical levels for relevant pairs (from data layer, not AI-generated)
- Trader profile: style (swing/scalper/position) — adjust strategy framing accordingly
```

### 5.2 Live News — Additional Prompt Fields to Add

```
- Trader's active currency pairs (mandatory — filter all analysis through this)
- Trader's session preference (London / NY / Asia)
- Trader's risk profile (conservative / moderate / aggressive)
- Instruction: reaction label MUST match directional lean of body text
- Instruction: include one "What triggers a trade" sentence with specific price/action condition
- Key technical levels for trader's active pairs (from data layer)
- Instruction: if event has no relevance to trader's pairs, state this explicitly
```

### 5.3 Holistic Scan — Additional Prompt Fields to Add

```
- Score scale definition passed into prompt (e.g. -100 to +100, neutral band -20 to +20)
- Component weight definitions so AI can report contribution per driver
- Staleness → confidence penalty mapping rule
- Instruction: CRITICAL/ELEVATED themes must include score contribution bridge sentence
- Trader profile: when swing detected, expand long-term section and condense short-term
- Instruction: each pair must receive unique commentary based on its currency-specific sensitivities
- Instruction: neutral sub-classify as NEUTRAL-BULLISH, NEUTRAL-BEARISH, or TRUE NEUTRAL
- Per-pair technical levels (sourced externally, not AI-generated)
```

---

## 6. Priority Action List

Ordered by impact on trader trust and output quality:

| Priority | Issue | Affects | Action |
|---|---|---|---|
| 1 | Reaction label vs. body text contradiction | Live News | Add consistency rule to prompt |
| 2 | Probabilities don't sum to 100% | Economic Calendar | Force single integers, sum-to-100 rule |
| 3 | Confidence unchanged despite stale data | Holistic Scan | Build staleness → confidence penalty |
| 4 | Personalization cosmetic only | All Sections | Cascade profile into output structure |
| 5 | Score scale undefined | Holistic Scan | Define and display scale + component breakdown |
| 6 | Generic pair commentary | Holistic Scan | Per-pair currency-specific sensitivity prompt |
| 7 | No actionable triggers | All Sections | Require conditional "If X → then Y" statements |
| 8 | Price levels unjustified | All Sections | Source levels from data layer + add basis label |
| 9 | NEUTRAL overused | All Sections | Introduce sub-classifications |
| 10 | Narrative disconnected from score | Holistic Scan | Require score-narrative bridge sentence |

---

*Document generated from FXSentinel AI analysis review session. Covers Economic Calendar (Core PCE), Live News (ECB/Guindos), and Holistic Scan (United States) outputs.*
