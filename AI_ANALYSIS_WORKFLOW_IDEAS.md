# AI Analysis Workflow Ideas

Working notes to improve FXSentinel analysis quality, consistency, and trader usefulness.

## Current State

- Holistic economy scan exists.
- Economic news event analysis exists.
- Live news analysis exists.
- Outputs are useful but can feel fragmented.

## Problems We Feel Today

- Inconsistent output format between analysis types.
- Not enough workflow-level orchestration.
- Confidence can be hard to interpret for trading decisions.
- Some responses are insightful but not directly actionable.

## What A Better Workflow Should Do

- Ingest all relevant data sources with freshness checks.
- Score data quality and source trust before analysis.
- Route events to the right analysis path (fast vs deep).
- Produce one trader-ready output contract every time.
- Re-check outcomes after event release and learn over time.

## Workflow Building Blocks

### 1) Input Layer

- Economic calendar events
- Live news headlines
- Holistic macro context
- Market regime signals (volatility, trend, liquidity)

### 2) Decision Router

- Event type classification
- Impact scoring
- Conflict detection (macro bias vs headline bias)
- Escalation logic to advanced analysis

### 3) Analysis Layer

- Deterministic reasoning for stable baseline
- LLM reasoning for ambiguity and narrative interpretation
- Cross-check rules to avoid contradictory outputs

### 4) Output Layer (Trader Contract)

- Thesis (one sentence)
- Direction + confidence
- Time horizon
- Key pairs/instruments
- Invalidation conditions
- Risk notes and execution watchlist

### 5) Feedback Layer

- Track realized market reaction at multiple horizons
- Compare forecast vs outcome
- Recalibrate confidence and prompts

## Candidate Automations

- Pre-event scenario generation (T-30m, T-15m, T-5m)
- Post-event reassessment (T+1m, T+5m, T+30m)
- Conflict-triggered reconciliation analysis
- Regime-aware template switching
- Alert quality scoring and prioritization

## Metrics To Evaluate Improvement

- Directional accuracy by horizon
- Confidence calibration quality
- Time to actionable output
- False positive rate for high-confidence calls
- User engagement with signals

## Open Questions

- What exact output schema should all analysis types share?
- Which events must always trigger deep analysis?
- How do we define "actionable" for different trader profiles?
- What minimum data quality is required before publishing analysis?

## Next Steps

1. Define a single output JSON contract.
2. Define routing rules and escalation thresholds.
3. Add event lifecycle automations (pre/post release checks).
4. Add measurement dashboard for forecast quality.
5. Run A/B test: current flow vs workflow-driven flow.

Kavi (Developer onboarding settings): 

Swing Trader 
Advanced 
Pairs listed:
EURUSD,GBPJPY,USDJPY,XAUUSD,XAGUSD,BTCUSD,ETHUSD

// Analysis of calendar event (April Data USD CPI y/y):

```
Consumer Price Index Analysis - Neutral Bias Expected
USD
CPI data expected to show inflation trends with moderate USD impact.
Analysis Confidence
75%
Consumer Impact
Moderate
Volatility
Medium
Risk Level
Normal
Market Sentiment
Neutral
Probability Scenarios
Bullish
Strong CPI above 3.7%: USD strengthens, EUR/USD targets 1.08, USD/JPY tests 149.0

Neutral
CPI in line with 3.7%: Range trading likely, EUR/USD 1.08-1.09, USD/JPY 148.0-149.0

Bearish
Weak CPI below 3.7%: USD weakens, EUR/USD targets 1.09, USD/JPY tests 148.0

Market Scenarios
Above
>3.7%
Bearish
On forecast
3.7%
Ranging
Below
<3.7%
Bullish
For the USD Currency

In-depth analysis
Release: Consumer Price Index report for 2026-05-12

Outcome: CPI expected to show inflation trends with moderate market impact.

Actual
Data pending
Expected
3.7%
Previous
3.3%
Market reaction
Price action: USD pairs expected to show moderate volatility with neutral bias. EUR/USD and USD/JPY primary movers.

Volatility: Moderate volatility expected with 15-25 pip movements on data surprises.

Why: Inflation data directly impacts Federal Reserve policy expectations and USD strength.

Implications
Economic context: CPI is the primary gauge of inflation, directly affecting Federal Reserve monetary policy decisions.

Policy implications: Neutral inflation data suggests neutral Federal Reserve policy bias.

Risk level: Moderate risk with potential for sharp USD movements.

Trading plan
Best approach: Range trading with breakout potential. Monitor EUR/USD 1.08-1.09 and USD/JPY 148.0-149.0 levels.

Avoid: Avoid aggressive positioning before data release. Use tight stops due to volatility.

Key levels: EUR/USD: 1.08 support, 1.09 resistance. USD/JPY: 148.0 support, 149.0 resistance.

Position sizing: Conservative position sizing recommended due to high volatility.

Big picture
Economic outlook: Inflation trends suggest neutral economic conditions with implications for growth and monetary policy.

Medium-term direction: USD likely to maintain neutral bias based on inflation trends.

Policy trajectory: Federal Reserve policy trajectory influenced by inflation data trends.

Forward focus: Monitor for follow-up inflation data and Federal Reserve communications.

Next catalysts:
Federal Reserve FOMC meetings
PPI data releases
Other inflation indicators (Core CPI, Personal Consumption Expenditures)
```

// Hollistic Scan analysis (Holistic Scan - United States):

```
Economy: United States
Scanned: 5/10/2026, 9:24:40 AM
Regime Strip
Bearish · Score -35.27 · 80% confidence
Neutral · Score -18.04 · 80% confidence
Top Pair Bias
EURUSD → BULLISH (medium)
|
Calendar Stress
100/100
High event density — regime signal may reprice sharply. Size accordingly.
Personalization: swing-trading profile detected — prioritize long-term regime and macro follow-through.
2Y Yield
3.89%
-0.02
10Y Yield
4.36%
-0.02
30Y Yield
4.94%
-0.02
Short-Term (2-6 weeks)
BEARISH
Score: -35.27|Confidence: 80
Long-Term (3-12 months)
NEUTRAL
Score: -18.04|Confidence: 80
Key takeaways
Personalized focus
LONG-TERM
Long-term regime is prioritized based on your onboarding trading style preference.

Short-term regime
BEARISH
Composite score -35.27 with 80% confidence on a 2–6 week horizon.

Long-term regime
NEUTRAL
Composite score -18.04 with 80% confidence on a 3–12 month horizon.

Geopolitical risk & energy prices
ELEVATED
Heightened conflict risk involving Israel, Iran, and U.S. involvement can lift oil risk premia, widen inflation uncertainty, and tighten financial conditions through energy and safe-haven channels. Oil moves feed into headline inflation expectations and can complicate central bank reaction functions even when core trends differ. The Fed’s reaction function remains sensitive to inflation surprises; energy shocks can temporarily dominate headlines even when core PCE is the operational focus. Geopolitical stress often coincides with USD bid and curve volatility.

Central bank document context
FED · 2026-03-18
FOMC Press Conference - March 18, 2026 — Federal Reserve FOMC press conference transcript/materials from March 18, 2026. Includes Chair commentary on policy decision rationale, inflation progress, labo…

Live sovereign yields
DOVISH REPRICING
2Y / 10Y / 30Y: 3.89% / 4.36% / 4.94%. Session change (Δ): -0.02 / -0.02 / -0.02.

Curve diagnostics
2s10s +0.47 pp
10s30s +0.58 pp. Steepening often ties to growth/reflation; flat/inverted warns late-cycle or recession pricing.

FX map (correlated pairs)
EURUSD → BULLISH; USDJPY → BEARISH
Bias uses base/quote orientation vs this economy’s currency; strength label reflects composite short-term score.

Calendar stress (14 days)
100 / 100
Higher = more high/medium-impact events for this currency in the next two weeks; raises volatility of interpretation.

Scan reliability
FAIR
Oldest indicator ~11d behind UTC. Missing signal families: 0 ().

Comprehensive Context
Short-term macro
United States short-term macro conditions currently screen as BEARISH. Sovereign benchmark yields for this economy are at 2Y / 10Y / 30Y of 3.89% / 4.36% / 4.94%, with session moves of -0.02 / -0.02 / -0.02. Together that reads as a dovish repricing rate backdrop; markets are repricing near-term policy and growth expectations, which is the main bridge from rates into FX.

Geopolitical & energy
Heightened conflict risk involving Israel, Iran, and U.S. involvement can lift oil risk premia, widen inflation uncertainty, and tighten financial conditions through energy and safe-haven channels. Oil moves feed into headline inflation expectations and can complicate central bank reaction functions even when core trends differ. Higher oil tends to support USD via terms-of-trade and safe-haven flows in risk-off episodes; energy-importing regions (e.g. euro area, Japan) face terms-of-trade and inflation pass-through headwinds unless offset by policy or FX adjustment. The Fed’s reaction function remains sensitive to inflation surprises; energy shocks can temporarily dominate headlines even when core PCE is the operational focus. Geopolitical stress often coincides with USD bid and curve volatility.

Policy communications
Policy communication context (FED, from the same document catalog as Overview’s Central Bank Analysis): “Federal Reserve FOMC press conference transcript/materials from March 18, 2026. Includes Chair commentary on policy decision rationale, inflation progress, labor market conditions, and forward guidance.” (see FOMC Press Conference - March 18, 2026 dated 2026-03-18).

Long-term regime
On a longer horizon, the regime reads NEUTRAL. The indicator composite and yield-curve shape are blended to estimate whether policy is moving toward tightening persistence, neutral stabilization, or easing repricing. This keeps long-term direction anchored to macro structure instead of one-off event noise.

FX mapping
FX implications are mapped into correlated pairs using base/quote orientation. When United States has a stronger yield and policy profile, pairs where this economy's currency is the base tend to inherit bullish bias, while quote-side exposure tends to inherit bearish bias; the reverse applies when the scan weakens.

Source references
Overlay context
1.0.0
File: backend/data/holistic_scan_context.json; last updated: 2026-03-25

Central bank documents
FED
File: src/data/central-bank-documents.json; catalog version: 1.0.0; sampled: 3 docs

Live market inputs
TRADINGVIEW
Indicator staleness: 11d 9h; yield staleness: 0h; calendar staleness: N/A; scan model: economy_scan_v1.2; generated UTC: 2026-05-10T09:24:40.971380

Short-Term Trading Range View
Short-term regime is bearish. Daily yield impulse and event risk suggest breakout-prone conditions over coming sessions.
Long-Term Trading Range View
Long-term regime is neutral. Curve structure (dovish_repricing) implies gradual macro trend development across weeks to months.
Short-Term Drivers
Rate momentum - Policy-rate direction over recent prints
Negative
Inflation momentum - Disinflation supports easing; re-acceleration supports tightening
Positive
Growth momentum - Near-term growth surprise impulse
Negative
Long-Term Drivers
Policy alignment - Real-rate / policy alignment proxy
Negative
Growth trend - Medium-term growth trajectory
Negative
Inflation trend - Inflation regime pressure
Positive
Labor trend - Employment backdrop resilience
Positive
Top Pair Biases
EURUSD - BULLISH (medium) - US short-term bearish regime with dovish repricing yield backdrop. - Conviction normal on available signal set.
Invalidated if oil/geopolitical stress triggers USD safe-haven bid and reverses current rate impulse.
USDJPY - BEARISH (medium) - US short-term bearish regime with dovish repricing yield backdrop. - Conviction normal on available signal set.
Invalidated if oil/geopolitical stress triggers USD safe-haven bid and reverses current rate impulse.
GBPUSD - BULLISH (medium) - US short-term bearish regime with dovish repricing yield backdrop. - Conviction normal on available signal set.
Invalidated if oil/geopolitical stress triggers USD safe-haven bid and reverses current rate impulse.
AUDUSD - BULLISH (medium) - US short-term bearish regime with dovish repricing yield backdrop. - Conviction normal on available signal set.
Invalidated if oil/geopolitical stress triggers USD safe-haven bid and reverses current rate impulse.
Reliability & Missing Signals
Dataset keys used for scan math: inflation → inflation-YoY; interest → interest-rate; growth → gdp-growth; labor → unemployment. (Older snapshots may omit this block.)

None
```

// Live news analysis (Bloomberg 08:08 GST • 5 hrs ago Low US Awaits Iran Reply as Aramco Says Hormuz Opening No Quick Fix The wait stretched on for Iran’s response to a US proposal to end 10 weeks of war, as the world’s largest oil company warned it would take months for the market to return to normal even if the Strait of Hormuz reopened immediately. ):

```
NEUTRAL
Confidence: 80%
Market Impact
The US awaits Iran's response, with Aramco cautioning that even if the Strait of Hormuz reopens promptly, it could take months for the oil market to stabilize. This uncertainty could lead to heightened risk aversion, impacting safe-haven currencies like JPY. Given the closed market status, immediate reactions may be limited.

Immediate Reaction:
NEUTRAL
Key Pairs:
USD/JPY, EUR/USD
Volatility:
LOW
Timeframe:
when markets reopen
Trading Implications
Traders should closely monitor USD/JPY for potential safe-haven flows and risk sentiment shifts. Key levels to watch include 156.00 support and 157.50 resistance. Expect subdued market activity until trading resumes, with potential for increased volatility upon reopening.

Risk Assessment
Market Volatility:
LOW
Liquidity Impact:
MEDIUM
Correlation Risk:
MEDIUM
Analyzed just now
```

The core problem is that your AI outputs are generated by strong but separate engines (calendar, holistic scan, and live news), so traders receive insights that can feel inconsistent, generic, or occasionally contradictory (especially in scenario labeling and confidence meaning), which lowers trust and actionability even when the underlying logic is good; the solution is to introduce a single workflow orchestration layer that unifies all analyses into one standardized trader output contract (thesis, direction, confidence definition, invalidation, horizon, key levels), applies routing and conflict-reconciliation rules between modules, anchors every view to current market context, and closes the loop with outcome tracking/calibration so confidence and recommendations become consistently reliable for real trading decisions.

