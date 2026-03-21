import React, { useMemo, useState, useEffect, useRef } from 'react';
import './Economies.css';
import economyIndicatorsData from '../data/economyIndicators.json';
import { config } from '../config';

/** Display order: US (by maturity 2Y→30Y), then EUR, then GBP. Wheel cycles this flat list. */
const YIELD_ECONOMY_ORDER = ['US', 'EUR', 'GBP'];

const YIELD_MARKETS = [
  { symbol: 'OANDA:USB02YUSD', label: 'US 2Y', economy: 'US', title: 'US 2Y T-Note (OANDA)' },
  { symbol: 'OANDA:USB05YUSD', label: 'US 5Y', economy: 'US', title: 'US 5Y T-Note (OANDA)' },
  { symbol: 'OANDA:USB10YUSD', label: 'US 10Y', economy: 'US', title: 'US 10Y T-Note (OANDA)' },
  { symbol: 'OANDA:USB30YUSD', label: 'US 30Y', economy: 'US', title: 'US T-Bond (OANDA)' },
  { symbol: 'OANDA:DE10YBEUR', label: 'DE 10Y', economy: 'EUR', title: 'Bund (OANDA)' },
  { symbol: 'OANDA:UK10YBGBP', label: 'UK 10Y', economy: 'GBP', title: 'UK 10Y Bond Yield (OANDA)' }
];

function TradingViewYieldWidget({ symbol }) {
  const containerRef = useRef(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const script = document.createElement('script');
    script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js';
    script.type = 'text/javascript';
    script.async = true;
    script.innerHTML = `
      {
        "allow_symbol_change": false,
        "calendar": false,
        "details": false,
        "hide_side_toolbar": true,
        "hide_top_toolbar": true,
        "hide_legend": false,
        "hide_volume": true,
        "hotlist": false,
        "interval": "D",
        "locale": "en",
        "save_image": false,
        "style": "1",
        "symbol": "${symbol}",
        "theme": "dark",
        "timezone": "Etc/UTC",
        "backgroundColor": "#0F0F0F",
        "gridColor": "rgba(242, 242, 242, 0.06)",
        "watchlist": [],
        "withdateranges": false,
        "compareSymbols": [],
        "show_popup_button": true,
        "popup_height": "650",
        "popup_width": "1000",
        "studies": [],
        "autosize": true
      }`;
    container.appendChild(script);

    return () => {
      script.remove();
    };
  }, [symbol]);

  const symbolPath = symbol.replace(':', '-');

  return (
    <div
      className="tradingview-widget-container yield-single-widget"
      ref={containerRef}
      style={{ height: '100%', width: '100%' }}
    >
      <div
        className="tradingview-widget-container__widget"
        style={{ height: 'calc(100% - 32px)', width: '100%' }}
      />
      <div className="tradingview-widget-copyright">
        <a href={`https://www.tradingview.com/symbols/${symbolPath}/`} rel="noopener nofollow" target="_blank">
          <span className="blue-text">{symbol} chart</span>
        </a>
        <span className="trademark"> by TradingView</span>
      </div>
    </div>
  );
}

const indicatorDetails = {
  'interest-rate': {
    overview:
      'The [[Federal Funds Rate (FFR)]] is the primary monetary policy tool of the U.S. Federal Reserve. It represents the [[target range]] for the overnight interest rate at which U.S. banks lend reserve balances to one another and acts as the [[benchmark for short-term interest rates]] globally.\n\n' +
      'For traders, the FFR is a [[core macro driver]] that influences USD valuation, yield differentials, risk sentiment, and cross-asset capital flows.\n\n' +
      '[[Why It Matters to Markets]]\n\n' +
      'The Federal Funds Rate anchors the entire U.S. yield curve and directly impacts:\n\n' +
      '• [[FX markets]]: USD strength or weakness via yield differentials\n\n' +
      '• [[Equities]]: Cost of capital and valuation multiples\n\n' +
      '• [[Fixed income]]: Short-term yields, curve shape, and volatility\n\n' +
      '• [[Commodities]]: Particularly gold, via real yields and risk appetite\n\n' +
      'Markets trade [[expectations of future rate changes]], often well ahead of actual FOMC decisions.',
    measurement:
      'The [[Federal Open Market Committee (FOMC)]] meets [[eight times per year]] to set a target range for the Federal Funds Rate.\n\n' +
      '[[Key policy signals]] traders monitor:\n\n' +
      '• [[Rate decision]] (hold / cut / hike)\n\n' +
      '• [[Statement language changes]]\n\n' +
      '• [[Dot Plot]] (rate path projections)\n\n' +
      '• [[Chair Powell\'s press conference]]\n\n' +
      'The [[Effective Federal Funds Rate (EFFR)]] reflects actual overnight trading and typically remains within the target range via Fed liquidity operations.',
    impact:
      '[[Market Transmission Mechanism]]\n\n' +
      '[[Rates → FX]]\n\n' +
      '• Higher relative U.S. rates attract capital → [[USD support]]\n\n' +
      '• Falling rate expectations compress yield advantage → [[USD pressure]]\n\n' +
      '[[Rates → Risk Assets]]\n\n' +
      '• Higher rates tighten financial conditions\n\n' +
      '• Lower rates generally support equities and credit\n\n' +
      '[[Rates → Commodities]]\n\n' +
      '• Gold reacts inversely to real yields\n\n' +
      '• Energy responds indirectly via growth expectations\n\n' +
      '[[Hawkish vs Dovish Signals]]\n\n' +
      '[[Hawkish Bias]]\n\n' +
      '• Delayed or fewer cuts\n\n' +
      '• Persistent inflation pressures\n\n' +
      '• Strong labor market data\n\n' +
      '• Emphasis on inflation risks\n\n' +
      'Typical reaction: [[USD strength]], higher yields, pressure on equities and gold\n\n' +
      '[[Dovish Bias]]\n\n' +
      '• Rate cuts or easing guidance\n\n' +
      '• Cooling inflation momentum\n\n' +
      '• Labor market softening\n\n' +
      '• Focus on growth risks\n\n' +
      'Typical reaction: [[USD weakness]], yield compression, support for risk assets and carry trades\n\n' +
      '[[Expectations vs Reality]]\n\n' +
      'FX and rates markets are [[forward-looking]]. Price action is often driven by:\n\n' +
      '• Inflation releases (CPI, PCE)\n\n' +
      '• Employment data (NFP, unemployment)\n\n' +
      '• Wage growth trends\n\n' +
      '• Fed communication tone\n\n' +
      'This makes the FFR less useful as a standalone signal and more powerful when aligned with [[data momentum and expectations]].',
    context:
      '[[Current Policy Context (Late 2025)]]\n\n' +
      'The Federal Reserve has shifted from restrictive policy toward [[cautious easing]], cutting rates to 3.50%–3.75% amid:\n\n' +
      '• Moderating (but still elevated) inflation\n\n' +
      '• Signs of labor market softening\n\n' +
      '• Slower economic momentum\n\n' +
      'Key characteristics of the current regime:\n\n' +
      '• [[Strong emphasis on data-dependence]]\n\n' +
      '• [[Gradual easing]], not aggressive stimulus\n\n' +
      '• [[Elevated sensitivity]] to inflation surprises\n\n' +
      '• Ongoing geopolitical and fiscal uncertainty\n\n' +
      'This environment favors [[expectation-driven and event-driven trading]].\n\n' +
      '[[Institutional & Bank Outlook]]\n\n' +
      'Major global banks broadly expect [[further rate cuts into 2026]], but emphasize a measured and data-dependent pace rather than aggressive easing.\n\n' +
      'Consensus themes among institutions:\n\n' +
      '• Policy is easing, but not returning to ultra-loose levels\n\n' +
      '• Inflation remains above target, limiting downside\n\n' +
      '• Labor data will be decisive for the next phase of cuts\n\n' +
      'Markets currently price [[1–3 additional 25bp cuts]], with timing sensitive to incoming data.\n\n' +
      '[[Political Overlay – Trump & Fed Independence]]\n\n' +
      'President Donald Trump has publicly called for significantly lower interest rates, arguing that easier policy would support growth and reduce government financing costs. He has openly pressured the Federal Reserve to cut faster and deeper.\n\n' +
      'Trump has also stated that future Fed leadership should align with his preference for lower rates, raising questions around [[central bank independence]].\n\n' +
      'Trader implication: While the Fed remains operationally independent, [[political pressure adds headline-driven volatility]] and can influence market narratives, particularly around leadership transitions and policy credibility.',
    traderImplications:
      '[[What Traders Should Monitor Next]]\n\n' +
      'High-impact drivers for rate repricing:\n\n' +
      '• [[Core inflation trends]]\n\n' +
      '• [[Labor market deterioration or resilience]]\n\n' +
      '• [[Changes in Fed communication tone]]\n\n' +
      '• [[Fed Funds Futures & OIS pricing]]\n\n' +
      '• [[Yield curve dynamics]] (2Y vs 10Y, real yields)\n\n' +
      'The [[highest-conviction trades]] emerge when data, expectations, and policy guidance align.\n\n' +
      '[[FXSentinel Usage]]\n\n' +
      'Within FXSentinel, the Federal Funds Rate functions best as:\n\n' +
      '• [[Macro regime filter]] (tightening vs easing)\n\n' +
      '• [[USD directional bias tool]]\n\n' +
      '• [[Cross-asset sentiment anchor]]',
  },
  'inflation-YoY': {
    overview:
      'U.S. Inflation (Year-Over-Year) measures the annual change in consumer prices, most commonly tracked through the [[Consumer Price Index (CPI)]]. It is one of the [[most influential macro indicators globally]], directly shaping Federal Reserve policy expectations, USD valuation, and cross-asset risk sentiment.\n\n' +
      'Inflation is a [[leading driver of interest rate decisions]], making it a critical input for FX, rates, and commodities traders.\n\n' +
      'Why Inflation Matters to Traders:\n\n' +
      '• [[Interest rate expectations]] and Fed policy paths\n\n' +
      '• [[Real yields]], a key driver of USD and gold\n\n' +
      '• [[Risk sentiment]], affecting equities and carry trades\n\n' +
      'Markets react less to the absolute level of inflation and more to [[surprises versus expectations and trend momentum]].',
    measurement:
      'The [[U.S. Bureau of Labor Statistics (BLS)]] calculates CPI by tracking price changes for a representative basket of goods and services across urban consumers. The [[year-over-year (YoY)]] measure compares current prices to the same month in the previous year.\n\n' +
      'Key components:\n\n' +
      '• [[Headline CPI]]: Includes all items, including volatile food and energy components.\n\n' +
      '• [[Core CPI]]: Excludes food and energy to reveal underlying inflation trends.\n\n' +
      '• [[Shelter and services]]: Major components that have remained sticky, slowing the pace of overall disinflation.\n\n' +
      '• [[Goods inflation]]: Has eased but remains sensitive to supply chain and tariff effects.\n\n' +
      'Data is released monthly, typically around the [[10th-15th of each month]] for the previous month, with revisions possible in subsequent releases. Frequency: Monthly. Unit: Percent (%).',
    impact:
      'Inflation readings have [[profound implications]] for currency markets through multiple channels:\n\n' +
      '[[Above-Expectation Inflation]]\n\n' +
      '• [[Reinforces hawkish bias]] and supports USD via higher real yields\n\n' +
      '• [[Pressures equities and gold]] as markets price in tighter policy\n\n' +
      '• Increases [[inflation expectations]], potentially steepening yield curves and supporting USD\n\n' +
      '[[Below-Expectation Inflation]]\n\n' +
      '• [[Strengthens easing expectations]] and weakens USD\n\n' +
      '• [[Supports risk assets and carry trades]] as policy pressure eases\n\n' +
      '• Relieves pressure on policymakers, potentially [[weakening USD]] if it leads to dovish policy\n\n' +
      '[[Market dynamics]]: Inflation remains the [[primary constraint on Fed easing]]. Cooling inflation supports additional rate cuts, while sticky core components cap the pace and depth of easing. Inflation surprises quickly [[reprice Fed Funds Futures and short-dated yields]]. For markets, inflation prints act as [[confirmation or invalidation events]] for existing rate expectations.',
    context:
      '[[Current Inflation Trend (Late 2025)]]\n\n' +
      'Headline U.S. CPI is running at approximately [[2.7% YoY]], down from earlier 2025 highs near 3.0%. This moderation reflects [[easing shelter inflation, base effects, and slower goods price growth]].\n\n' +
      'Core inflation (excluding food and energy) has also cooled, but remains [[above the Federal Reserve\'s 2% target]], reinforcing a cautious policy stance rather than aggressive easing.\n\n' +
      'Key takeaway: Inflation is easing, but not fully neutralized — keeping policy expectations finely balanced.\n\n' +
      '[[Key Drivers Behind Current Inflation]]\n\n' +
      'Consumer Prices & Shelter:\n\n' +
      '• [[Shelter and services inflation remain sticky]], slowing the pace of overall disinflation\n\n' +
      '• [[Goods inflation has eased]], but remains sensitive to supply chain and tariff effects\n\n' +
      'Tariffs & Policy Effects:\n\n' +
      '• [[Ongoing tariff policies]] have contributed to persistent goods price pressures, particularly through gradual pass-through to consumers\n\n' +
      '• These effects have [[limited how quickly inflation can fall back to target]]\n\n' +
      'Inflation Expectations:\n\n' +
      '• [[Consumer inflation expectations remain elevated]] around 3.0–3.2%, reinforcing wage and pricing stickiness\n\n' +
      '• [[Anchored but elevated expectations]] increase the Fed\'s caution around rapid easing\n\n' +
      '[[What Banks & Institutions Are Saying]]\n\n' +
      'Major financial institutions broadly agree that inflation is cooling, but warn against declaring victory. Consensus themes:\n\n' +
      '• [[Inflation may remain slightly above target]] into early 2026\n\n' +
      '• [[Tariff-driven pressures]] could delay full normalization\n\n' +
      '• [[Recent CPI prints may be distorted]] by reporting disruptions and base effects\n\n' +
      'Several banks describe current inflation as a [["low-grade persistence" environment]] rather than a clean disinflation cycle.\n\n' +
      '[[Political & Structural Context]]\n\n' +
      'Trade and tariff policy continues to act as an [[upward structural force on prices]].\n\n' +
      'Data quality concerns emerged during 2025 due to [[government shutdown-related disruptions]], adding short-term noise to CPI readings.\n\n' +
      'Political pressure for easier monetary policy contrasts with inflation still running above target.\n\n' +
      'Trader implication: Inflation data may generate [[outsized volatility as markets debate signal vs noise]].',
    traderImplications:
      '[[Market & Fed Implications]]\n\n' +
      'Inflation remains the [[primary constraint on Fed easing]]. Cooling inflation supports additional rate cuts, while sticky core components cap the pace and depth of easing. Inflation surprises quickly [[reprice Fed Funds Futures and short-dated yields]]. For markets, inflation prints act as [[confirmation or invalidation events]] for existing rate expectations.\n\n' +
      '[[What Traders Should Monitor Next]]\n\n' +
      'High-impact inflation signals include:\n\n' +
      '• [[Monthly CPI & Core CPI prints]]\n\n' +
      '• [[PCE inflation]] (Fed-preferred measure)\n\n' +
      '• [[Wage growth and services inflation]]\n\n' +
      '• [[Inflation expectations surveys]]\n\n' +
      '• [[Tariff-related price pass-through indicators]]\n\n' +
      'Alignment between inflation trend, expectations, and Fed guidance creates the [[highest-conviction macro trades]].\n\n' +
      '[[FXSentinel Usage]]\n\n' +
      'Within FXSentinel, U.S. Inflation (YoY) functions best as:\n\n' +
      '• [[Rate-expectation driver]]\n\n' +
      '• [[USD bias validator]]\n\n' +
      '• [[Real-yield and gold signal]]\n\n' +
      '• [[Volatility trigger around data releases]]',
  },
  'gdp-growth': {
    overview:
      '[[Gross Domestic Product (GDP)]] measures the total value of goods and services produced within the United States. [[Real GDP growth]] (adjusted for inflation) is the primary gauge of economic momentum and a core input into monetary policy, risk sentiment, and cross-asset pricing.\n\n' +
      'For traders, GDP growth provides context on [[demand strength, recession risk, and policy durability]], influencing FX flows, yields, and equity valuations.\n\n' +
      'Why GDP Matters for Markets:\n\n' +
      '• [[FX]]: Strong growth supports USD via real yield support and capital inflows\n\n' +
      '• [[Rates]]: Faster growth can delay or limit rate cuts\n\n' +
      '• [[Equities]]: Supports earnings outlook but may cap valuation upside if rates stay elevated\n\n' +
      '• [[Risk Sentiment]]: Sustained expansion favors risk-on positioning',
    measurement:
      'The [[U.S. Bureau of Economic Analysis (BEA)]] calculates GDP growth as the percentage change in real GDP from one quarter to the previous quarter, [[annualized for comparability]]. The calculation uses chained dollars to adjust for inflation.\n\n' +
      'GDP is measured through three approaches:\n\n' +
      '• [[Expenditure approach]]: Sum of consumption, investment, government spending, and net exports.\n\n' +
      '• [[Income approach]]: Sum of all income earned in production.\n\n' +
      '• [[Production approach]]: Value added at each stage of production.\n\n' +
      'Data is released quarterly, typically around the [[end of the month]] following the quarter end, with [[multiple revisions]] as more comprehensive data becomes available. Release Frequency: Quarterly. Unit: Percent (%).',
    impact:
      'GDP growth has [[profound implications]] for currency markets through multiple transmission channels:\n\n' +
      '[[Stronger GDP]]\n\n' +
      '• [[Supports USD and real yields]]\n\n' +
      '• [[Reduces rate-cut urgency]]\n\n' +
      '• [[Favors cyclical assets]]\n\n' +
      '[[Weaker GDP]]\n\n' +
      '• [[Reopens recession risk pricing]]\n\n' +
      '• [[Increases rate-cut probability]]\n\n' +
      '• [[Supports defensive FX and bonds]]\n\n' +
      '[[Market dynamics]]: GDP surprises tend to [[reprice rate expectations first]], with FX and equity volatility following. Markets react not just to the headline number but to [[components and revisions]], with consumption and investment data particularly scrutinized for forward-looking signals.',
    context:
      '[[Latest Growth Snapshot]]\n\n' +
      'Q3 2025 Real GDP: [[+4.3% (annualized)]]\n\n' +
      '[[Strongest quarterly expansion in over two years]]\n\n' +
      'Growth exceeded consensus expectations\n\n' +
      'Key contributors:\n\n' +
      '• [[Resilient consumer spending]]\n\n' +
      '• [[Rebound in exports]]\n\n' +
      '• [[Continued government and fiscal support]]\n\n' +
      'Earlier in 2025, GDP briefly contracted before rebounding sharply in Q2 and accelerating further in Q3, highlighting [[uneven but resilient economic momentum]].\n\n' +
      '[[Forward Outlook]]\n\n' +
      'Q4 2025 GDP (GDPNow estimate): [[~3.0%]]\n\n' +
      'Growth expected to [[moderate but remain expansionary]]\n\n' +
      'Full-year 2025 growth projected near [[~1.8–2.0% on an annual basis]]\n\n' +
      'Markets interpret recent strength as [[reducing near-term recession risk]], while acknowledging downside risks from tighter financial conditions and slowing labor trends.\n\n' +
      '[[Policy & Fed Implications]]\n\n' +
      'Stronger-than-expected GDP [[complicates the Federal Reserve\'s easing path]]:\n\n' +
      '• [[Robust growth reduces urgency]] for aggressive rate cuts\n\n' +
      '• [[Persistent expansion alongside sticky inflation]] increases data-dependence\n\n' +
      '• Markets [[recalibrate expectations]] based on growth-inflation balance\n\n' +
      'The Fed remains focused on [[preventing re-acceleration while avoiding overtightening]] into late-cycle growth.\n\n' +
      '[[Institutional & Bank Views]]\n\n' +
      'Economists note Q3 growth was [[broad-based, not purely statistical]]\n\n' +
      'Consensus expects [[slower but positive growth into 2026]]\n\n' +
      'Risks cited include:\n\n' +
      '• [[Cooling consumer demand]]\n\n' +
      '• [[Softer job creation]]\n\n' +
      '• [[Fiscal uncertainty and geopolitical spillovers]]\n\n' +
      'Banks emphasize that quarterly strength does not eliminate late-cycle risks, but [[materially lowers near-term recession probabilities]].',
    traderImplications:
      '[[What Traders Should Watch]]\n\n' +
      'Key data linked to GDP momentum:\n\n' +
      '• [[Retail sales & consumer spending]]\n\n' +
      '• [[Business investment and capex]]\n\n' +
      '• [[Trade balance and exports]]\n\n' +
      '• [[Labor market resilience]]\n\n' +
      '• [[Inflation persistence vs growth strength]]\n\n' +
      'GDP surprises tend to [[reprice rate expectations first]], with FX and equity volatility following.\n\n' +
      '[[Market Impact Summary]]\n\n' +
      'Stronger GDP:\n\n' +
      '• [[Supports USD and real yields]]\n\n' +
      '• [[Reduces rate-cut urgency]]\n\n' +
      '• [[Favors cyclical assets]]\n\n' +
      'Weaker GDP:\n\n' +
      '• [[Reopens recession risk pricing]]\n\n' +
      '• [[Increases rate-cut probability]]\n\n' +
      '• [[Supports defensive FX and bonds]]',
  },
  unemployment: {
    overview:
      'The [[U.S. Unemployment Rate (U-3)]] measures the percentage of the civilian labor force that is unemployed but actively seeking work. It is one of the [[most closely watched indicators of economic health, consumer resilience, and monetary policy direction]].\n\n' +
      'For traders, unemployment trends are critical because they influence [[Federal Reserve policy expectations, wage inflation, consumer spending, and cross-asset risk sentiment]].\n\n' +
      'Why Unemployment Matters for Markets:\n\n' +
      '• [[Monetary Policy]]: Rising unemployment increases pressure on the Fed to ease policy\n\n' +
      '• [[Inflation]]: Labor slack reduces wage-driven inflation risks\n\n' +
      '• [[Consumer Demand]]: Higher unemployment weakens household spending\n\n' +
      '• [[Risk Sentiment]]: Labor deterioration can shift markets toward defensive positioning\n\n' +
      'Labor data often [[leads policy shifts]], making it a high-signal indicator for traders.',
    measurement:
      'The [[U.S. Bureau of Labor Statistics (BLS)]] calculates the unemployment rate from the [[Current Population Survey (CPS)]], a monthly survey of approximately 60,000 households. The rate represents the percentage of the [[civilian labor force]] (employed + unemployed) that is unemployed.\n\n' +
      'Key definitions:\n\n' +
      '• [[Unemployed]]: People without jobs who have actively looked for work in the past 4 weeks.\n\n' +
      '• [[Labor force]]: Employed + unemployed (excludes those not seeking work).\n\n' +
      '• [[U-6 rate]]: Broader measure including discouraged workers and part-time workers seeking full-time employment.\n\n' +
      'Data is released monthly, typically on the [[first Friday]] of each month for the previous month, with revisions possible in subsequent releases. Release Frequency: Monthly. Unit: Percent (%).',
    impact:
      'Unemployment readings have [[significant implications]] for currency markets through policy and economic health channels:\n\n' +
      '[[Dovish Signals]]\n\n' +
      '• [[Unemployment rising faster than expected]]\n\n' +
      '• [[Weak payroll growth]]\n\n' +
      '• [[Cooling wage pressures]]\n\n' +
      '→ Markets price [[earlier or deeper rate cuts]]\n\n' +
      '[[Hawkish Signals]]\n\n' +
      '• [[Unemployment stabilizing or falling]]\n\n' +
      '• [[Strong job creation]]\n\n' +
      '• [[Accelerating wages]]\n\n' +
      '→ [[Rate cut expectations are delayed or reduced]]\n\n' +
      '[[Market Impact Summary]]\n\n' +
      'FX Markets:\n\n' +
      '• [[Rising unemployment tends to weigh on USD]] via lower rate expectations\n\n' +
      '• [[High sensitivity in USD/JPY, EUR/USD, and GBP/USD]] around jobs data\n\n' +
      'Rates:\n\n' +
      '• [[Short-dated Treasury yields respond first]]\n\n' +
      '• [[Softer labor data steepens the yield curve]] via front-end repricing\n\n' +
      'Equities:\n\n' +
      '• [[Mild labor cooling can support equities]] via rate cuts\n\n' +
      '• [[Sharp labor deterioration increases recession risk]] and volatility',
    context:
      '[[Latest Labor Market Snapshot]]\n\n' +
      'Unemployment Rate: [[~4.6%]]\n\n' +
      'Trend: [[Gradually rising through late 2025]]\n\n' +
      'Context: [[Highest level since 2021]], signaling a cooling labor market\n\n' +
      'Recent employment gains have been concentrated in:\n\n' +
      '• [[Healthcare]]\n\n' +
      '• [[Construction]]\n\n' +
      '• [[Social assistance]]\n\n' +
      'Meanwhile, [[federal workforce reductions and slower hiring across cyclical sectors]] have weighed on overall labor conditions.\n\n' +
      '[[Labor Market Trend Assessment]]\n\n' +
      'The labor market has shifted from tight to [[balanced-to-soft]], marked by:\n\n' +
      '• [[Slowing monthly payroll growth]]\n\n' +
      '• [[Reduced labor mobility]] (lower quit rates)\n\n' +
      '• [[Fewer job openings]] relative to prior years\n\n' +
      '• [[Stable but flattening labor force participation]]\n\n' +
      'While unemployment remains historically moderate, the [[direction of travel suggests increasing economic slack]], particularly if hiring continues to decelerate.\n\n' +
      '[[Federal Reserve Policy Implications]]\n\n' +
      'The recent rise in unemployment [[strengthens the case for continued, cautious rate cuts]], especially if paired with easing inflation.\n\n' +
      'Key policy dynamics:\n\n' +
      '• The Fed [[balances labor market cooling against inflation persistence]]\n\n' +
      '• [[Rising unemployment reduces urgency]] to maintain restrictive rates\n\n' +
      '• [[Policy decisions remain highly data-dependent]] rather than pre-committed\n\n' +
      'Labor weakness without a sharp collapse supports [[gradual easing, not emergency stimulus]].',
    traderImplications:
      '[[What Traders Should Monitor]]\n\n' +
      'High-impact labor indicators linked to unemployment:\n\n' +
      '• [[Monthly Non-Farm Payrolls (NFP)]]\n\n' +
      '• [[Initial & Continuing Jobless Claims]]\n\n' +
      '• [[JOLTS Job Openings]]\n\n' +
      '• [[Wage growth]] (Average Hourly Earnings)\n\n' +
      '• [[Labor force participation rate]]\n\n' +
      'Alignment between unemployment, inflation, and GDP often signals [[macro inflection points]].\n\n' +
      '[[Market Impact Summary]]\n\n' +
      'FX Markets:\n\n' +
      '• [[Rising unemployment tends to weigh on USD]] via lower rate expectations\n\n' +
      '• [[High sensitivity in USD/JPY, EUR/USD, and GBP/USD]] around jobs data\n\n' +
      'Rates:\n\n' +
      '• [[Short-dated Treasury yields respond first]]\n\n' +
      '• [[Softer labor data steepens the yield curve]] via front-end repricing\n\n' +
      'Equities:\n\n' +
      '• [[Mild labor cooling can support equities]] via rate cuts\n\n' +
      '• [[Sharp labor deterioration increases recession risk]] and volatility',
  },
  'nonfarm-payrolls': {
    overview:
      '[[Non-Farm Payrolls (NFP)]] measure the monthly change in employment across the U.S. economy, excluding farm workers, private household workers, and nonprofit organizations. It is derived from the [[Bureau of Labor Statistics (BLS) Establishment Survey]] and is one of the [[foremost indicators of labor market strength and economic momentum]].\n\n' +
      'NFP is a [[high-impact release for financial markets]] because it directly influences consumer spending expectations, inflation dynamics, monetary policy outlooks, and USD valuation.\n\n' +
      'Why NFP Matters for Markets:\n\n' +
      '• [[Labor market momentum]]: Direct read on hiring or layoffs\n\n' +
      '• [[Wage pressure]]: Drives inflation and real wage expectations\n\n' +
      '• [[Consumer demand]]: Jobs growth supports consumption — ~70% of GDP\n\n' +
      '• [[Fed policy expectations]]: Strong NFP data can delay rate cuts; weak data can accelerate them\n\n' +
      'NFP surprises often [[trigger USD volatility]], especially in pairs like USD/JPY, EUR/USD, AUD/USD, and can ripple into rates, equities, and commodities.',
    measurement:
      'The [[U.S. Bureau of Labor Statistics (BLS)]] calculates NFP from the [[Establishment Survey]], which covers approximately 145,000 businesses and government agencies representing about 697,000 worksites. The survey measures [[non-farm employment]] across all major industry sectors.\n\n' +
      'Key components:\n\n' +
      '• [[Total non-farm employment]]: The headline number reported in thousands (K), seasonally adjusted.\n\n' +
      '• [[Private sector employment]]: Excludes government workers, providing a cleaner read on private labor demand.\n\n' +
      '• [[Average hourly earnings]]: Wage growth component, critical for inflation expectations.\n\n' +
      '• [[Average workweek]]: Hours worked, indicating labor demand intensity.\n\n' +
      'Data is released monthly on the [[first Friday]] of each month at 8:30 AM ET for the previous month, with [[revisions]] common in subsequent months as more complete data arrives. Frequency: Monthly. Unit: Jobs Added / Lost (Seasonally Adjusted).',
    impact:
      'NFP releases have [[profound market-moving effects]] through multiple transmission channels:\n\n' +
      '[[Bullish USD / Hawkish Implications]]\n\n' +
      '• [[Job growth significantly above expectations]]\n\n' +
      '• [[Upward revisions to prior months]]\n\n' +
      '• [[Wage acceleration stronger than expected]]\n\n' +
      '→ [[USD supports, rate-cut expectations tempered, yield curve steepening]]\n\n' +
      '[[Dovish USD / Easing Implications]]\n\n' +
      '• [[Weak or declining payrolls]]\n\n' +
      '• [[Lower private sector job creation]]\n\n' +
      '• [[Unemployment rising alongside low job gains]]\n\n' +
      '→ [[USD pressure, markets price earlier rate cuts, lower yields]]\n\n' +
      '[[Market dynamics]]: NFP is known as the [["king of economic indicators"]] due to its market impact. The release often causes [[immediate and significant volatility]] in USD pairs, with EUR/USD, GBP/USD, and USD/JPY particularly sensitive. Markets react not just to the headline number but to [[revisions, wage data, and unemployment rate]] released simultaneously.',
    context:
      '[[Latest NFP Data (Nov 2025)]]\n\n' +
      'Non-farm Payrolls (Nov 2025): [[+64,000 jobs added]]\n\n' +
      'Forecast consensus: [[~51,000 jobs]]\n\n' +
      'Prior (Oct 2025): [[–105,000 jobs]] (sharp decline due to federal workforce reductions and shutdown effects)\n\n' +
      'The November report showed [[continued modest job growth]] following October\'s significant contraction, with gains concentrated in:\n\n' +
      '• [[Healthcare]]\n\n' +
      '• [[Construction]]\n\n' +
      '• [[Social assistance]]\n\n' +
      'Total nonfarm employment has shown [[very little net change since April 2025]], suggesting labor market activity has broadly flattened.\n\n' +
      'Important context: Due to the October federal government shutdown, October household survey data were not published, and payroll data were delayed and consolidated with the November release — an [[unusual deviation from the typical jobs report cycle]].\n\n' +
      '[[Labor Market Trend Signals]]\n\n' +
      'Slowing Job Growth:\n\n' +
      'November\'s modest gain comes after October\'s contraction, underlining a [[broad cooling in labor demand]]. Despite headline job creation, employment has shown [[limited trend strength since mid-2025]].\n\n' +
      'Private Sector Weakness:\n\n' +
      'ADP data — an independent private payroll measure — reported a [[decline in private jobs in November]], highlighting underlying weakness outside public sector support.\n\n' +
      'Residual Data Noise:\n\n' +
      'Ongoing disruptions from the government shutdown have [[complicated interpretation]]. Analysts caution that [[seasonal adjustments and reporting gaps]] may introduce noise into short-term comparisons.\n\n' +
      '[[Monetary Policy & Market Implications]]\n\n' +
      'Current Context:\n\n' +
      'Even with small gains in November, the overall trend suggests [[sluggish labor demand and a softening job market]] — which supports a dovish tilt in monetary policy pricing. Combined with rising unemployment and slowing wage pressures, this environment keeps markets [[sensitive to labor data surprises]].',
    traderImplications:
      '[[Market & Policy Signals to Watch]]\n\n' +
      'Leading indicators around NFP:\n\n' +
      '• [[Average Hourly Earnings]]: Critical for inflation expectations\n\n' +
      '• [[Labor Force Participation]]: Tracks labor supply trends\n\n' +
      '• [[Initial and Continuing Claims]]: Early signals of layoffs\n\n' +
      '• [[Private vs Public Payroll Divergence]]: Shows structural labor strength/weakness\n\n' +
      'Risk events tied to NFP:\n\n' +
      '• [[Revisions to prior months\' payroll totals]]\n\n' +
      '• [[Fed commentary in reaction to labor trends]]\n\n' +
      '• [[Correlation shifts between jobs, inflation, and core prices]]\n\n' +
      '[[Market Impact Summary]]\n\n' +
      'FX Markets:\n\n' +
      '• NFP releases are the [[most market-moving economic events]], causing immediate and significant USD moves\n\n' +
      '• [[High sensitivity in USD/JPY, EUR/USD, AUD/USD]] around jobs data\n\n' +
      'Rates:\n\n' +
      '• [[Short-dated Treasury yields respond first]] to NFP surprises\n\n' +
      '• [[Strong data steepens yield curve]] via front-end repricing\n\n' +
      'Equities & Commodities:\n\n' +
      '• NFP data triggers [[simultaneous moves across asset classes]] as markets reassess growth, policy, and risk outlooks\n\n' +
      '• [[Weak labor data supports rate-cut expectations]], potentially supporting equities via lower yields',
  },
  // EUR Interest Rate
  'interest-rate-EUR': {
    overview:
      'The [[European Central Bank (ECB)]] has paused its easing cycle after delivering substantial rate cuts through 2024–2025. Policy rates are now held at levels deemed [[broadly neutral]], reflecting inflation that has converged toward target and a euro area economy showing [[modest but improving resilience]].\n\n' +
      '[[Current Policy Stance]]\n\n' +
      'Main Refinancing Rate: [[2.15%]]\n\n' +
      'Deposit Facility Rate: [[2.00%]]\n\n' +
      'Marginal Lending Facility: [[2.40%]]\n\n' +
      'The ECB has emphasized that [[future decisions will be strictly data-dependent]], with no pre-committed rate path.\n\n' +
      '[[Policy Objective & Inflation Backdrop]]\n\n' +
      'The ECB\'s primary mandate is [[price stability]], defined as inflation close to 2% over the medium term.\n\n' +
      '• [[Headline inflation has cooled significantly]] from post-pandemic peaks\n\n' +
      '• [[Core inflation remains sticky]] but is trending lower\n\n' +
      '• [[ECB staff projections]] place inflation near target through 2025–2026\n\n' +
      'This environment has [[reduced urgency for further easing]] while limiting justification for renewed tightening.',
    measurement:
      '[[Governance & Key Decision-Makers]]\n\n' +
      'ECB President: [[Christine Lagarde]]\n\n' +
      'Decision Body: [[ECB Governing Council]] (Executive Board + national central bank governors)\n\n' +
      'Policy decisions reflect a [[balance between divergent national economic conditions]], with a strong emphasis on institutional independence and credibility.\n\n' +
      'Lagarde\'s leadership has focused on:\n\n' +
      '• [[Maintaining inflation-fighting credibility]]\n\n' +
      '• [[Avoiding premature policy commitments]]\n\n' +
      '• [[Anchoring medium-term expectations]] rather than short-term market reactions\n\n' +
      'The ECB Governing Council meets [[approximately eight times per year]] to set policy rates. Update Frequency: Policy meetings (≈8 per year).',
    impact:
      '[[FX & Macro Implications]]\n\n' +
      '• A [[steady ECB while other central banks ease]] may support the euro\n\n' +
      '• [[Weak growth differentials versus the U.S.]] remain a structural EUR headwind\n\n' +
      '• [[EUR crosses remain sensitive]] to inflation surprises and ECB communication tone\n\n' +
      '[[Scenario Framework]]\n\n' +
      '[[Hawkish Risk]]\n\n' +
      '• [[Inflation re-accelerates]] due to wages or energy\n\n' +
      '• [[Growth outperforms expectations]]\n\n' +
      '→ [[Rates remain restrictive for longer]]\n\n' +
      '[[Base Case]]\n\n' +
      '• [[Inflation stabilizes near 2%]]\n\n' +
      '• [[Growth remains modest]]\n\n' +
      '→ [[Policy rates unchanged]]\n\n' +
      '[[Dovish Risk]]\n\n' +
      '• [[Sharp growth slowdown]]\n\n' +
      '• [[Core inflation undershoots target]]\n\n' +
      '→ [[Potential return to easing]]',
    context:
      '[[Economic Growth Context]]\n\n' +
      'Eurozone growth remains [[subdued but positive]], supported by:\n\n' +
      '• [[Gradual recovery in consumer demand]]\n\n' +
      '• [[Stabilizing energy prices]]\n\n' +
      '• [[Easing financial conditions]] following prior rate cuts\n\n' +
      'However, growth remains [[uneven across member states]], complicating policy transmission and reinforcing the ECB\'s cautious approach.\n\n' +
      '[[Political & Institutional Considerations]]\n\n' +
      'While the ECB operates independently, monetary policy exists within a broader political and fiscal landscape:\n\n' +
      '• Some euro area governments favor [[looser policy to support growth]]\n\n' +
      '• [[Fiscal policy divergence]] across member states affects inflation outcomes\n\n' +
      '• Ongoing debate exists around the eurozone\'s [["neutral rate" level]]\n\n' +
      'Despite these pressures, the ECB has consistently [[reinforced its independence]], prioritizing inflation dynamics over political preferences.\n\n' +
      '[[Market Expectations & Forward Outlook]]\n\n' +
      'Markets currently price:\n\n' +
      '• [[High probability of rate stability]] through 2026\n\n' +
      '• [[Low probability of near-term cuts or hikes]], absent a macro shock\n\n' +
      'Future rate direction will depend primarily on:\n\n' +
      '• [[Core inflation persistence]]\n\n' +
      '• [[Wage growth dynamics]]\n\n' +
      '• [[Eurozone growth momentum]]\n\n' +
      '• [[External shocks]] (energy prices, geopolitics, global trade)',
    traderImplications:
      '[[Key Indicators to Monitor]]\n\n' +
      'High-impact drivers for rate repricing:\n\n' +
      '• [[Eurozone CPI]] (headline & core)\n\n' +
      '• [[Wage growth and labor market data]]\n\n' +
      '• [[ECB meeting statements and press conferences]]\n\n' +
      '• [[Financial conditions and credit transmission metrics]]\n\n' +
      'The [[highest-conviction trades]] emerge when data, expectations, and policy guidance align.\n\n' +
      '[[FXSentinel Usage]]\n\n' +
      'Within FXSentinel, ECB monetary policy functions best as:\n\n' +
      '• [[Macro regime filter]] (tightening vs easing)\n\n' +
      '• [[EUR directional bias tool]]\n\n' +
      '• [[Cross-asset sentiment anchor]]',
  },
  // GBP Interest Rate
  'interest-rate-GBP': {
    overview:
      'The [[Bank of England\'s Bank Rate]] (also known as the base rate) is the interest rate at which the BoE lends to commercial banks overnight. It is the [[primary monetary policy tool]] of the Bank of England, set by the [[Monetary Policy Committee (MPC)]] to achieve the 2% CPI inflation target while supporting economic growth and employment.\n\n' +
      'The Bank Rate anchors the [[entire UK yield curve]], influencing borrowing costs for households, businesses, and the government. Changes in the Bank Rate transmit through bank lending rates, mortgage costs, corporate borrowing, and currency markets, affecting economic activity and asset prices.\n\n' +
      'For traders, the Bank Rate is a [[core macro driver]] that influences GBP valuation via yield differentials, signals BoE policy stance, affects UK asset pricing, and influences risk sentiment. Markets trade [[expectations of future rate changes]], often well ahead of actual MPC decisions.\n\n' +
      'The Bank Rate is set at [[MPC meetings held approximately every six weeks]], with decisions announced immediately and detailed minutes published subsequently. The rate is not subject to revisions, but accompanying economic forecasts and statements provide forward guidance on policy direction.',
    measurement:
      'The [[Monetary Policy Committee (MPC)]] consists of nine members: the Governor, three Deputy Governors, the Chief Economist, and four external members appointed by the Chancellor. The MPC meets [[approximately every six weeks]] to set the Bank Rate based on economic data, inflation forecasts, and growth projections.\n\n' +
      'Key policy signals traders monitor:\n\n' +
      '• [[Rate decision]] (hold / cut / hike)\n\n' +
      '• [[Voting split]] (reveals internal divisions and policy bias)\n\n' +
      '• [[Monetary Policy Summary]] (forward guidance and policy tone)\n\n' +
      '• [[Inflation Report]] (quarterly economic forecasts and projections)\n\n' +
      '• [[Governor Bailey\'s press conference]] (policy communication and Q&A)\n\n' +
      'The Bank Rate influences the [[Effective Bank Rate]], which reflects actual overnight interbank lending and typically remains close to the Bank Rate through BoE liquidity operations. The rate affects [[mortgage rates, corporate borrowing costs, and savings rates]] across the UK economy.',
    impact:
      'Bank Rate decisions have [[profound implications]] for GBP markets through multiple transmission channels:\n\n' +
      '[[Rate Cuts]]\n\n' +
      '• [[Reduce GBP support]] via lower yield differentials\n\n' +
      '• [[Support bond prices]] and compress yields\n\n' +
      '• [[Boost equities]] via lower borrowing costs\n\n' +
      '• [[Stimulate growth]] but may fuel inflation if too aggressive\n\n' +
      '[[Rate Hikes]]\n\n' +
      '• [[Support GBP strength]] via higher yield differentials\n\n' +
      '• [[Pressure bond prices]] and raise yields\n\n' +
      '• [[Weigh on equities]] via higher borrowing costs\n\n' +
      '• [[Cool inflation]] but may slow growth\n\n' +
      '[[Market Dynamics]]\n\n' +
      'GBP crosses remain sensitive to Bank Rate expectations and decisions, with [[above-expectation cuts tending to weaken GBP]] via dovish repricing, while [[below-expectation cuts or pauses support GBP]] through reduced easing pressure. The interplay between Bank Rate, inflation, wage growth, and growth data is crucial for BoE policy anticipation. Markets focus on [[expectations versus outcomes]], with significant deviations from consensus driving immediate volatility.',
    context:
      '[[Current Policy Context (Late 2025)]]\n\n' +
      'As of December 18, 2025, the Bank Rate stands at [[3.75%]], following a 25 basis point cut from 4.00%. This marks the [[lowest level since February 2023]] and reflects a shift from restrictive policy toward easing, driven by moderating inflation, weak growth, and a softening labor market.\n\n' +
      'Recent trend: The BoE has cut rates multiple times since August 2024, with the most recent cuts including [[December 18, 2025 (3.75%), August 7, 2025 (4.00%), May 8, 2025 (4.25%)]]. The [[5-4 voting split]] in recent decisions indicates internal division on the pace of easing, with some members favoring faster cuts and others cautioning on inflation risks.\n\n' +
      '[[Economic Backdrop]]\n\n' +
      'Inflation: CPI inflation stood at [[3.2% in November 2025]], down from 3.6% in October, but still above the 2% target. The decline provided room for rate cuts, but persistent inflation concerns limit aggressive easing.\n\n' +
      'Growth: The UK economy has shown [[minimal growth]], with GDP expanding by only 0.1% in Q2 2025, down from 0.7% in Q1. The BoE reduced its UK economic growth forecast for 2025 from 1.5% to 0.75%, indicating heightened concerns about the economic outlook.\n\n' +
      'Labor Market: Unemployment has risen to [[5.1%]], the highest since January 2021, indicating potential challenges in the labor market. Wage growth remains a concern for inflation persistence.\n\n' +
      '[[Institutional & Bank Commentary]]\n\n' +
      'Major financial institutions interpret the recent rate cuts as appropriate given easing inflation and weak growth, but note risks from persistent inflation and wage pressures. The 5-4 voting split reflects uncertainty about the pace of easing.\n\n' +
      'Consensus themes among institutions:\n\n' +
      '• [[Further cuts are likely]], but the pace depends on incoming data\n\n' +
      '• [[Inflation remains above target]], limiting aggressive easing\n\n' +
      '• [[Weak growth and rising unemployment]] support continued cuts\n\n' +
      '• [[Wage growth remains a concern]] for inflation persistence\n\n' +
      'Markets price [[additional cuts into 2026]], with timing sensitive to inflation, wage growth, and labor market data.\n\n' +
      '[[Central Bank & Policy Context]]\n\n' +
      'The BoE\'s MPC sets the Bank Rate to achieve the [[2% CPI inflation target]] while supporting economic growth and employment. The reaction function weighs inflation persistence, wage growth, growth momentum, and labor market conditions.\n\n' +
      'Current context: The Bank Rate at 3.75% reflects a shift toward easing, balancing [[moderating inflation against weak growth and a softening labor market]]. The 5-4 voting split indicates internal division, with some members favoring faster cuts and others cautioning on inflation risks.\n\n' +
      'Governor Andrew Bailey noted that the UK has [["passed the recent peak in inflation and it has continued to fall"]], allowing for rate reductions. However, the BoE emphasizes [[data dependence]], with no pre-committed rate path, and remains ready to adjust policy based on incoming information.\n\n' +
      '[[Political & Structural Overlay]]\n\n' +
      'The BoE operates with [[operational independence]], but political pressure and fiscal policy affect the economic environment. Government spending and tax policy influence growth and inflation, affecting monetary policy trade-offs.\n\n' +
      'Brexit and trade: Trade relationships and supply chain shifts affect inflation and growth. [[Trade tensions and tariffs]] can affect import costs and competitiveness, while trade deals can support growth but may affect inflation.\n\n' +
      'Structural factors: The UK\'s [[services-heavy economy]] (especially financial services) affects rate transmission, while [[housing market sensitivity]] to rates affects consumption and growth. [[Productivity challenges]] affect growth potential and inflation dynamics.\n\n' +
      'The distinction between political narrative and policy reality is important: public statements emphasize growth support and inflation control, but [[actual policy is constrained by the inflation target and economic conditions]]. The BoE maintains operational independence, but political pressure can affect communication and expectations.',
    traderImplications:
      '[[What Traders Should Monitor Next]]\n\n' +
      'High-impact drivers for Bank Rate repricing:\n\n' +
      '• [[MPC meetings]] (approximately every six weeks)\n\n' +
      '• [[CPI inflation releases]] (primary target, especially services and core components)\n\n' +
      '• [[Wage growth data]] (affects inflation persistence and policy trade-offs)\n\n' +
      '• [[Unemployment and labor market data]] (affects growth and inflation dynamics)\n\n' +
      '• [[GDP growth figures]] (affects policy trade-offs and rate decisions)\n\n' +
      '• [[Housing market indicators]] (affects consumption and growth)\n\n' +
      '• [[MPC minutes and communications]] (forward guidance and policy tone)\n\n' +
      '[[Thresholds & Inflection Points]]\n\n' +
      'A move below [[3.50%]] would signal more aggressive easing and likely pressure GBP. A pause or move above [[4.00%]] would signal a more cautious stance and support GBP. The 3.75% level appears to be a near-term equilibrium, with significant deviations likely to shift market narratives.\n\n' +
      '[[Signals That Could Change the Narrative]]\n\n' +
      'Unexpected shifts in inflation, especially if driven by wage growth or services inflation, could alter Bank Rate expectations. Changes in labor market conditions, especially unemployment and wage growth, could affect policy trade-offs. Growth surprises, especially if driven by consumption or investment, could influence rate decisions. Changes in BoE communication tone, especially around forward guidance, could shift market expectations.\n\n' +
      '[[FXSentinel Usage]]\n\n' +
      'Within FXSentinel, the Bank of England Bank Rate functions best as:\n\n' +
      '• [[GBP directional bias tool]] (via yield differentials)\n\n' +
      '• [[BoE policy expectation driver]]\n\n' +
      '• [[Cross-asset sentiment anchor]]\n\n' +
      '• [[Volatility trigger around MPC meetings]]',
  },
  // JPY Interest Rate
  'interest-rate-JPY': {
    overview:
      'The [[Bank of Japan\'s Policy Rate]] is the interest rate at which the BoJ lends to financial institutions overnight. It is the [[primary monetary policy tool]] of the Bank of Japan, set by the [[Policy Board]] to achieve the 2% inflation target while supporting economic growth.\n\n' +
      'The Policy Rate anchors the [[entire Japanese yield curve]], influencing borrowing costs for households, businesses, and the government. Changes in the Policy Rate transmit through bank lending rates, corporate borrowing, and currency markets, affecting economic activity and asset prices.\n\n' +
      'For traders, the Policy Rate is a [[core macro driver]] that influences JPY valuation via yield differentials, signals BoJ policy stance, affects Japanese asset pricing, and influences risk sentiment. Markets trade [[expectations of future rate changes]], often well ahead of actual Policy Board decisions.\n\n' +
      'The Policy Rate is set at [[Policy Board meetings held approximately every six weeks]], with decisions announced immediately and detailed statements published subsequently. The rate is not subject to revisions, but accompanying economic forecasts and statements provide forward guidance on policy direction.',
    measurement:
      'The [[Policy Board]] consists of nine members: the Governor, two Deputy Governors, and six other members. The Policy Board meets [[approximately every six weeks]] to set the Policy Rate based on economic data, inflation forecasts, and growth projections.\n\n' +
      'Key policy signals traders monitor:\n\n' +
      '• [[Rate decision]] (hold / hike / cut)\n\n' +
      '• [[Policy statement]] (forward guidance and policy tone)\n\n' +
      '• [[Outlook Report]] (quarterly economic forecasts and projections)\n\n' +
      '• [[Governor Ueda\'s press conference]] (policy communication and Q&A)\n\n' +
      '• [[Yield Curve Control (YCC)]] adjustments (affects long-term yields)\n\n' +
      'The Policy Rate influences the [[Effective Policy Rate]], which reflects actual overnight interbank lending and typically remains close to the Policy Rate through BoJ liquidity operations. The rate affects [[mortgage rates, corporate borrowing costs, and savings rates]] across the Japanese economy.',
    impact:
      'Policy Rate decisions have [[profound implications]] for JPY markets through multiple transmission channels:\n\n' +
      '[[Rate Hikes]]\n\n' +
      '• [[Support JPY strength]] via higher yield differentials\n\n' +
      '• [[Pressure bond prices]] and raise yields\n\n' +
      '• [[May weigh on equities]] via higher borrowing costs\n\n' +
      '• [[Cool inflation]] but may slow growth if too aggressive\n\n' +
      '[[Rate Cuts]]\n\n' +
      '• [[Reduce JPY support]] via lower yield differentials\n\n' +
      '• [[Support bond prices]] and compress yields\n\n' +
      '• [[Boost equities]] via lower borrowing costs\n\n' +
      '• [[Stimulate growth]] but may fuel inflation if too aggressive\n\n' +
      '[[Market Dynamics]]\n\n' +
      'JPY crosses remain sensitive to Policy Rate expectations and decisions, with [[above-expectation hikes tending to support JPY]] via hawkish repricing, while [[below-expectation hikes or pauses weaken JPY]] through reduced normalization pressure. The interplay between Policy Rate, inflation, wage growth, and growth data is crucial for BoJ policy anticipation. Markets focus on [[expectations versus outcomes]], with significant deviations from consensus driving immediate volatility.',
    context:
      '[[Current Policy Context (Late 2025)]]\n\n' +
      'As of December 19, 2025, the Policy Rate stands at [[0.75%]], following a 25 basis point hike from 0.50%. This marks the [[highest level since September 1995]] and reflects a shift from ultra-loose policy toward normalization, driven by sustained inflation above the 2% target, stronger wage growth, and confidence in achieving stable inflation.\n\n' +
      'Recent trend: The BoJ has raised rates multiple times since ending negative rates, with the most recent hikes including [[December 19, 2025 (0.75%), January 24, 2025 (0.50%), and March 19, 2024 (0% to 0.1%)]]. The December 2025 hike to 0.75% aims to [[curb inflation, which stood at 3% in November]], exceeding the BoJ\'s 2% target.\n\n' +
      '[[Economic Backdrop]]\n\n' +
      'Inflation: CPI inflation stood at [[3% in November 2025]], above the 2% target. The sustained inflation above target supports continued normalization, but the pace depends on inflation persistence and wage growth.\n\n' +
      'Wage Growth: [[Wage growth has strengthened]], supporting sustainable inflation and confidence in achieving the 2% target. The interplay between wage growth and inflation is crucial for policy decisions.\n\n' +
      'Growth: The Japanese economy has shown [[modest growth]], with the BoJ balancing normalization with growth support. The export-oriented economy remains sensitive to global conditions.\n\n' +
      '[[Institutional & Bank Commentary]]\n\n' +
      'Major financial institutions interpret the normalization as appropriate given sustained inflation and wage growth, but note risks from global uncertainties and the need for a gradual approach. The shift from negative rates to 0.75% reflects confidence in achieving stable inflation, but the pace of normalization remains cautious.\n\n' +
      'Consensus themes among institutions:\n\n' +
      '• [[Further normalization is likely]], but the pace will be gradual and data-dependent\n\n' +
      '• [[Inflation remains above target]], supporting continued normalization\n\n' +
      '• [[Wage growth has strengthened]], supporting sustainable inflation\n\n' +
      '• [[The BoJ will balance normalization]] with economic growth support\n\n' +
      'Markets price [[additional normalization into 2026]], with timing sensitive to inflation, wage growth, and economic growth data.\n\n' +
      '[[Central Bank & Policy Context]]\n\n' +
      'The BoJ\'s Policy Board sets the Policy Rate to achieve the [[2% inflation target]] while supporting economic growth. The reaction function weighs inflation persistence, wage growth, growth momentum, and financial stability.\n\n' +
      'Current context: The Policy Rate at 0.75% reflects a shift toward normalization, balancing [[persistent inflation (3% in November 2025, above the 2% target) against global uncertainties and growth concerns]]. The December 2025 hike to 0.75% aims to curb inflation while supporting economic growth.\n\n' +
      'Governor Ueda has emphasized [[data dependence]], with no pre-committed rate path, and remains ready to adjust policy based on incoming information. The BoJ\'s forward guidance focuses on achieving the 2% inflation target sustainably, with policy adjustments based on economic and price developments.\n\n' +
      '[[Political & Structural Overlay]]\n\n' +
      'The BoJ operates with [[operational independence]], but political pressure and fiscal policy affect the economic environment. Government spending and tax policy influence growth and inflation, affecting monetary policy trade-offs.\n\n' +
      'Structural factors: Japan\'s [[aging population]] affects growth potential and inflation dynamics, while the [[export-oriented economy]] affects rate transmission and currency dynamics. [[Productivity challenges]] affect growth potential and inflation dynamics. [[Financial sector profitability concerns]] affect policy trade-offs.\n\n' +
      'The distinction between political narrative and policy reality is important: public statements emphasize inflation control and growth support, but [[actual policy is constrained by the inflation target and economic conditions]]. The BoJ maintains operational independence, but political pressure can affect communication and expectations.',
    traderImplications:
      '[[What Traders Should Monitor Next]]\n\n' +
      'High-impact drivers for Policy Rate repricing:\n\n' +
      '• [[Policy Board meetings]] (approximately every six weeks)\n\n' +
      '• [[CPI inflation releases]] (primary target, especially services and core components)\n\n' +
      '• [[Wage growth data]] (affects inflation persistence and policy trade-offs)\n\n' +
      '• [[Economic growth figures]] (affects policy trade-offs and rate decisions)\n\n' +
      '• [[Yield Curve Control (YCC) adjustments]] (affects long-term yields and policy stance)\n\n' +
      '• [[Policy Board statements and communications]] (forward guidance and policy tone)\n\n' +
      '[[Thresholds & Inflection Points]]\n\n' +
      'A move above [[1.0%]] would signal more aggressive normalization and likely support JPY. A pause or move below [[0.50%]] would signal a more cautious stance and weigh on JPY. The 0.75% level appears to be a near-term equilibrium, with significant deviations likely to shift market narratives.\n\n' +
      '[[Signals That Could Change the Narrative]]\n\n' +
      'Unexpected shifts in inflation, especially if driven by wage growth or services inflation, could alter Policy Rate expectations. Changes in wage growth, affecting inflation persistence and policy trade-offs, could influence rate decisions. Changes in economic growth, affecting policy trade-offs, could shift market expectations. Changes in BoJ communication tone, especially around forward guidance, could affect market positioning.\n\n' +
      '[[FXSentinel Usage]]\n\n' +
      'Within FXSentinel, the Bank of Japan Policy Rate functions best as:\n\n' +
      '• [[JPY directional bias tool]] (via yield differentials)\n\n' +
      '• [[BoJ policy expectation driver]]\n\n' +
      '• [[Cross-asset sentiment anchor]]\n\n' +
      '• [[Volatility trigger around Policy Board meetings]]',
  },
  // EUR Inflation
  'inflation-EUR': {
    overview:
      'The [[Harmonised Index of Consumer Prices (HICP)]] is the official inflation measure for the Eurozone, calculated by Eurostat using a standardized methodology across all euro area member states. It provides a [[comparable and consistent measure of consumer price inflation]] and serves as the primary inflation gauge for ECB monetary policy decisions.\n\n' +
      'HICP tracks the [[year-over-year change in prices paid by households]] for a representative basket of goods and services, ensuring uniform treatment of consumption patterns across countries.\n\n' +
      'Why HICP Matters to Markets:\n\n' +
      '• It is the [[ECB\'s primary inflation target]], guiding interest rate policy\n\n' +
      '• It shapes [[rate expectations, bond yields, and EUR valuation]]\n\n' +
      '• [[Deviations from target]] influence forward guidance and market volatility\n\n' +
      'Because of its harmonized structure, HICP is [[more relevant for cross-border investors]] than national CPI figures.',
    measurement:
      '[[Eurostat]] calculates HICP by tracking price changes for a representative basket of goods and services across all eurozone member states using a [[standardized methodology]]. The [[year-over-year (YoY)]] measure compares current prices to the same month in the previous year.\n\n' +
      'Key components:\n\n' +
      '• [[Headline HICP]]: Includes all items, including volatile food and energy components\n\n' +
      '• [[Core HICP]]: Excludes food, energy, alcohol, and tobacco to reveal underlying inflation trends\n\n' +
      'HICP is composed of several major categories:\n\n' +
      '• [[Services inflation]]: Remains the most persistent component, reflecting wage growth and domestic demand\n\n' +
      '• [[Food, alcohol & tobacco]]: Moderating but still sensitive to global supply conditions\n\n' +
      '• [[Non-energy industrial goods]]: Generally subdued, reflecting weak demand and easing input costs\n\n' +
      '• [[Energy]]: Volatile but currently exerting limited upward pressure on headline inflation\n\n' +
      'Data is released monthly, typically around the [[middle of each month]] for the previous month, with revisions possible in subsequent releases. Source: Eurostat. Used by: European Central Bank. Release Frequency: Monthly. Unit: Percent (%).',
    impact:
      'HICP readings have [[profound implications]] for currency markets through ECB policy channels:\n\n' +
      '[[FX Markets]]\n\n' +
      '• [[Inflation above expectations tends to support EUR]], particularly against lower-yielding peers\n\n' +
      '• [[Soft inflation surprises often weaken EUR]] via lower rate expectations\n\n' +
      '[[Rates & Bonds]]\n\n' +
      '• [[HICP outcomes directly affect rate futures]] and yield curve pricing\n\n' +
      '• [[Stable inflation near target]] typically compresses volatility in front-end rates\n\n' +
      '[[Cross-Asset Effects]]\n\n' +
      '• [[Inflation stability supports equity valuation certainty]]\n\n' +
      '• [[Sudden HICP deviations can trigger broad risk repricing]]\n\n' +
      '[[Market dynamics]]: Markets react most strongly to [[surprises versus consensus]], not absolute inflation levels. HICP remains a [[primary constraint on ECB easing]]. Cooling inflation supports additional rate cuts, while sticky core components cap the pace and depth of easing.',
    context:
      '[[Current Inflation Context]]\n\n' +
      'Eurozone HICP inflation stands at approximately [[2.1% year-over-year]], placing it very close to the ECB\'s 2% medium-term target. Inflation has [[stabilized after declining sharply]] from post-pandemic and energy-shock peaks.\n\n' +
      'Key characteristics of the current inflation backdrop:\n\n' +
      '• [[Headline inflation is largely anchored near target]]\n\n' +
      '• [[Price pressures have normalized]] following easing energy and supply-chain costs\n\n' +
      '• [[Inflation persistence is increasingly driven by domestic components]] rather than external shocks\n\n' +
      'This environment supports a [[more balanced ECB policy stance]], rather than aggressive tightening or easing.\n\n' +
      '[[Inflation Composition & Underlying Trends]]\n\n' +
      'Markets closely monitor [[services inflation as a proxy for underlying price momentum]] and wage pass-through effects.\n\n' +
      '[[ECB Policy Framework]]\n\n' +
      'The ECB operates under a [[symmetric 2% inflation target over the medium term]], meaning it treats deviations above and below target with equal concern.\n\n' +
      'Policy implications:\n\n' +
      '• [[Inflation near target allows the ECB]] to avoid restrictive bias\n\n' +
      '• [[Sustained inflation above target]] would reintroduce tightening risk\n\n' +
      '• [[Persistent undershooting]] could revive easing expectations\n\n' +
      '[[Short-term volatility in HICP]] is less influential than trend persistence, particularly in core and services components.\n\n' +
      '[[Macro & Political Considerations]]\n\n' +
      'Inflation dynamics in the euro area are influenced by:\n\n' +
      '• [[Wage negotiations]] across major economies (Germany, France, Italy)\n\n' +
      '• [[Fiscal policy and government support measures]]\n\n' +
      '• [[Energy price volatility and geopolitical developments]]\n\n' +
      '• [[External demand conditions and EUR exchange-rate movements]]\n\n' +
      'While political pressures exist at the national level, ECB policy remains [[inflation-driven, with HICP as the central reference point]].',
    traderImplications:
      '[[What Traders Should Monitor]]\n\n' +
      'High-impact drivers for rate repricing:\n\n' +
      '• [[Monthly HICP releases vs expectations]]\n\n' +
      '• [[Core and services inflation trends]]\n\n' +
      '• [[ECB Governing Council commentary]]\n\n' +
      '• [[Wage growth and labor cost indicators]]\n\n' +
      '• [[Energy price shocks and geopolitical risks]]\n\n' +
      '[[Persistent divergence between headline HICP and underlying components]] often precedes shifts in ECB communication.\n\n' +
      '[[FXSentinel Usage]]\n\n' +
      'Within FXSentinel, Eurozone HICP functions best as:\n\n' +
      '• [[ECB policy constraint indicator]]\n\n' +
      '• [[EUR directional bias tool]]\n\n' +
      '• [[Rate-expectation driver]]\n\n' +
      '• [[Volatility catalyst around HICP releases]]',
  },
  // EUR Core Inflation
  'core-inflation-YoY-EUR': {
    overview:
      'Eurozone Core Inflation measures the [[year-over-year change in the Harmonised Index of Consumer Prices (HICP) excluding food and energy]]. By removing the most volatile components, core inflation provides a [[clearer view of underlying, domestically driven price pressures]], particularly in services and non-energy goods.\n\n' +
      'This measure is [[closely monitored by the ECB]] as it better reflects persistent inflation dynamics linked to wages, demand conditions, and pricing power, making it a [[critical input in monetary policy decisions]].\n\n' +
      '[[Why Core Inflation Matters]]\n\n' +
      'Core inflation is often [[more influential than headline inflation]] for markets because:\n\n' +
      '• It captures [[persistent price trends rather than temporary shocks]]\n\n' +
      '• It is [[strongly linked to wage growth and services inflation]]\n\n' +
      '• It shapes [[ECB rate expectations and forward guidance]]\n\n' +
      '• It influences [[EUR valuation via real yield expectations]]\n\n' +
      'Sustained core inflation above target typically [[constrains the ECB\'s ability to ease policy aggressively]].',
    measurement:
      '[[Eurostat]] calculates Core HICP by taking the Harmonised Index of Consumer Prices and [[excluding food, energy, alcohol, and tobacco components]]. The year-over-year change compares current prices to the same month in the previous year.\n\n' +
      'Key components:\n\n' +
      '• [[Core HICP]]: All items except food, energy, alcohol, and tobacco, representing the underlying inflation trend\n\n' +
      '• [[Services inflation]]: Remains the most persistent component, reflecting wage growth and domestic demand\n\n' +
      '• [[Non-energy industrial goods]]: Generally subdued, reflecting weak demand and easing input costs\n\n' +
      '• [[Excluded items]]: Food, energy, alcohol, and tobacco—the most volatile components\n\n' +
      'Core HICP is the [[ECB\'s preferred inflation gauge]] for assessing persistent price pressures and making monetary policy decisions.\n\n' +
      'Data is released monthly, typically around the [[middle of each month]] for the previous month, with revisions possible in subsequent releases. Source: Eurostat. Used by: European Central Bank. Release Frequency: Monthly. Unit: Percent (%).',
    impact:
      'Core inflation has [[profound implications]] for currency markets through ECB policy channels:\n\n' +
      '[[FX Markets (EUR)]]\n\n' +
      '• [[Core inflation above expectations tends to support EUR]], reinforcing higher real rate assumptions\n\n' +
      '• [[Downside surprises often weaken EUR]] through dovish repricing of ECB expectations\n\n' +
      '[[Rates & Bonds]]\n\n' +
      '• [[Sticky core inflation limits front-end yield declines]]\n\n' +
      '• [[Sustained moderation would steepen the curve]] via easing expectations\n\n' +
      '[[Risk Assets]]\n\n' +
      '• [[Persistent core inflation can cap equity upside]] by delaying monetary easing\n\n' +
      '• [[Stability, rather than acceleration, generally reduces volatility]]\n\n' +
      '[[Market dynamics]]: Markets react most strongly to [[deviations from consensus]], not absolute levels. Core inflation remains a [[primary constraint on ECB easing]]. A decisive downward break in core inflation would materially alter ECB policy pricing.',
    context:
      '[[Current Core Inflation Context]]\n\n' +
      'Eurozone core inflation is running at approximately [[2.4% year-over-year]], remaining above headline HICP (~2.1%) and slightly above the ECB\'s 2% medium-term target.\n\n' +
      'Key observations:\n\n' +
      '• [[Core inflation has stabilized, rather than fallen sharply]], in recent months\n\n' +
      '• [[Disinflation has been slower than headline measures]], reflecting sticky domestic price pressures\n\n' +
      '• [[Services inflation continues to be the dominant contributor]]\n\n' +
      'This persistence suggests that while inflation is no longer accelerating, it is [[not yet fully neutralized from a policy perspective]].\n\n' +
      '[[Trend & Inflation Dynamics]]\n\n' +
      'Core inflation has hovered around the [[2.3%–2.5% range]], indicating resilience despite easing energy and goods prices.\n\n' +
      'Monthly momentum remains positive, implying that [[inflationary pressure is cooling gradually rather than collapsing]].\n\n' +
      'The [[gap between headline and core inflation]] underscores the role of wages, rents, and services costs.\n\n' +
      'For policymakers, this reinforces [[caution against premature policy easing]].\n\n' +
      '[[ECB Policy Interpretation]]\n\n' +
      'The ECB\'s inflation framework emphasizes a [[symmetric 2% target over the medium term]], with core inflation playing a central role in assessing persistence.\n\n' +
      'Policy implications of current core inflation levels:\n\n' +
      '• [[Supports a measured and data-dependent approach]] to rate cuts\n\n' +
      '• [[Reduces urgency for aggressive easing]] despite headline inflation nearing target\n\n' +
      '• [[Keeps focus on labor market data and wage growth indicators]]\n\n' +
      'ECB officials frequently cite [[services and core inflation as key constraints]] on faster normalization of policy.\n\n' +
      '[[Macro & Political Overlay]]\n\n' +
      '[[Wage negotiations across major euro area economies]] (notably Germany and France) remain a key driver of services inflation.\n\n' +
      '[[Fiscal policy and labor market tightness]] influence cost pass-through.\n\n' +
      'While political pressures vary by country, ECB independence remains intact, with policy decisions [[anchored in inflation persistence rather than political signaling]].\n\n' +
      'Core inflation therefore remains a [[structural macro variable, not a politically driven one]].',
    traderImplications:
      '[[What Traders Should Monitor]]\n\n' +
      'High-impact drivers for rate repricing:\n\n' +
      '• [[Monthly core HICP releases vs expectations]]\n\n' +
      '• [[Services inflation and wage growth trends]]\n\n' +
      '• [[ECB commentary referencing "persistence" or "second-round effects"]]\n\n' +
      '• [[Labor market tightness indicators]]\n\n' +
      '• [[Divergence between headline and core inflation paths]]\n\n' +
      'A [[decisive downward break in core inflation]] would materially alter ECB policy pricing.\n\n' +
      '[[FXSentinel Usage]]\n\n' +
      'Within FXSentinel, Eurozone Core Inflation functions best as:\n\n' +
      '• [[ECB policy constraint indicator]]\n\n' +
      '• [[EUR directional bias tool]]\n\n' +
      '• [[Rate-expectation driver]]\n\n' +
      '• [[Volatility catalyst around core HICP releases]]',
  },
  // EUR GDP Growth
  'gdp-growth-EUR': {
    overview:
      '[[Gross Domestic Product (GDP)]] measures the total economic output of the euro area — a key indicator of [[economic momentum, private demand, investment, and external trade]]. Eurozone GDP growth is a [[core macro driver]] influencing:\n\n' +
      '• [[Monetary policy expectations]] (ECB rate bias)\n\n' +
      '• [[Currency valuation]] (EUR relative to other majors)\n\n' +
      '• [[Risk sentiment]] across equities and bonds\n\n' +
      '• [[Cross-asset pricing dynamics]]\n\n' +
      'Eurozone GDP is reported quarterly and published by [[Eurostat]].',
    measurement:
      '[[Eurostat]] calculates Eurozone GDP growth as the percentage change in real GDP from one quarter to the previous quarter, with [[year-over-year (YoY)]] measures also reported for annual comparisons. The calculation uses [[chained volumes]] to adjust for inflation and price changes.\n\n' +
      'GDP is measured through three approaches:\n\n' +
      '• [[Expenditure approach]]: Sum of consumption, investment, government spending, and net exports\n\n' +
      '• [[Income approach]]: Sum of all income earned in production\n\n' +
      '• [[Production approach]]: Value added at each stage of production\n\n' +
      'Key components tracked:\n\n' +
      '• [[Household consumption]]: Consumer spending across euro area member states\n\n' +
      '• [[Government expenditure]]: Fiscal spending and public investment\n\n' +
      '• [[Investment]]: Business investment and capital formation\n\n' +
      '• [[Net exports]]: Trade balance contribution to GDP\n\n' +
      'Data is released quarterly, typically around the [[end of the month]] following the quarter end, with [[multiple revisions]] as more comprehensive data becomes available. Source: Eurostat / ECB Staff Projections. Release Frequency: Quarterly. Unit: Percent (%).',
    impact:
      'Eurozone GDP growth has [[profound implications]] for currency markets through multiple transmission channels:\n\n' +
      '[[FX (EUR)]]\n\n' +
      '• [[Stronger-than-expected GDP prints tend to support EUR]], especially if accompanied by resilient inflation\n\n' +
      '• [[Growth moderation or downside surprises can pressure EUR]] via dovish repricing of ECB expectations\n\n' +
      '[[Rates & Yield Curves]]\n\n' +
      '• [[Durable growth can flatten or steepen curves]] depending on inflation signals\n\n' +
      '• [[Weak growth tends to lower front-end yields]] via easing expectations\n\n' +
      '[[Equities & Credit]]\n\n' +
      '• [[Positive GDP data typically bolster European equities]]\n\n' +
      '• [[Credit spreads may tighten on stable growth]], but widen if growth falters\n\n' +
      '[[Market dynamics]]: Markets pay particular attention to [[growth surprises vs consensus]], which often drive near-term repricing.\n\n' +
      '[[Hawkish vs Dovish Growth Signals]]\n\n' +
      '[[Hawkish Growth Scenario]]\n\n' +
      '• [[GDP surprises to the upside]]\n\n' +
      '• [[Broad-based strength]] across consumption, investment, exports\n\n' +
      '• [[Labor markets accelerating]]\n\n' +
      '→ [[Reduces likelihood of rate cuts; supports EUR appreciation]]\n\n' +
      '[[Dovish Growth Scenario]]\n\n' +
      '• [[GDP undershoots consensus]]\n\n' +
      '• [[Manufacturing contraction persists]]\n\n' +
      '• [[Slowing consumption momentum]]\n\n' +
      '→ [[Increases odds of easing; weighs on EUR and yields]]',
    context:
      '[[Latest Data – Q3 2025]]\n\n' +
      'Quarter-on-Quarter (QoQ): [[+0.3%]]\n\n' +
      'Year-on-Year (YoY): [[~1.4%]]\n\n' +
      'The euro area economy remains in [[positive but moderate expansion]], with growth driven by consumption, government spending, and export activity. Investment has stabilized after prior weakness, while trade conditions remain mixed.\n\n' +
      'ECB projections for the full year place real GDP growth near [[~1.3%–1.4% for 2025]], with a modest slowdown in 2026 before moderate recovery thereafter.\n\n' +
      '[[Trend & Economic Drivers]]\n\n' +
      'Growth in the euro area reflects a [[balanced but subdued expansion]], characterized by:\n\n' +
      '• [[Household Consumption]]: Continues to contribute positively as labor markets remain reasonably tight and wages grow modestly\n\n' +
      '• [[Government Expenditure]]: Fiscal support in key member states helps sustain demand\n\n' +
      '• [[Investment]]: Recovering from earlier declines but not yet robust\n\n' +
      '• [[Net Exports]]: Positive contributor, though global trade headwinds persist\n\n' +
      'Overall expansion is [[uneven across member states]], with Spain and France outpacing core economies like Germany, which has exhibited softer growth.\n\n' +
      '[[Monetary Policy & ECB Implications]]\n\n' +
      'Eurozone growth at current levels [[supports the European Central Bank\'s strategy of holding interest rates steady]]:\n\n' +
      '• [[Growth is positive and non-recessionary]], reducing pressure for aggressive easing\n\n' +
      '• However, it is [[not strong enough to justify tightening]] in the absence of persistent inflation overshoot\n\n' +
      '• [[Growth data reinforce the ECB\'s data-dependent framework]], where policy adjustments are contingent on incoming economic momentum alongside inflation dynamics\n\n' +
      'ECB staff projections align with this [[cautious stance]], forecasting moderate growth through 2026.\n\n' +
      '[[Political & Structural Context]]\n\n' +
      'Eurozone GDP growth is influenced by:\n\n' +
      '• [[Heterogeneous national conditions]]: Core economies (e.g., Germany) lag peripheral countries in growth momentum\n\n' +
      '• [[Structural constraints]]: Demographic headwinds and productivity challenges limit long-term potential\n\n' +
      '• [[Fiscal policy variation]]: National fiscal responses and EU recovery funds influence domestic spending\n\n' +
      '• [[External geopolitical factors]]: Trade disruptions, energy price volatility, and global supply chain risks impart uncertainty\n\n' +
      'While political debate exists over fiscal stimulus and structural reforms, ECB policy remains [[anchored to inflation and growth fundamentals]], not political cycles.',
    traderImplications:
      '[[What Traders Should Monitor]]\n\n' +
      'Key data and indicators that provide forward signals for euro area growth:\n\n' +
      '• [[Quarterly GDP revisions and detailed component breakdowns]]\n\n' +
      '• [[Business sentiment]] (PMI surveys)\n\n' +
      '• [[Labor market indicators]] (employment, unemployment, job openings)\n\n' +
      '• [[Investment and capex reports]]\n\n' +
      '• [[Euro area trade data and global demand indicators]]\n\n' +
      'The [[interplay between growth and inflation data]] (HICP and core inflation) is crucial for ECB policy anticipation.\n\n' +
      '[[FXSentinel Usage]]\n\n' +
      'Within FXSentinel, Eurozone GDP Growth functions best as:\n\n' +
      '• [[ECB policy context indicator]]\n\n' +
      '• [[EUR directional bias tool]]\n\n' +
      '• [[Growth-inflation balance gauge]]\n\n' +
      '• [[Volatility catalyst around GDP releases]]',
  },
  // GBP GDP Growth
  'gdp-growth-GBP': {
    overview:
      '[[Gross Domestic Product (GDP)]] measures the total value of goods and services produced within the United Kingdom. [[Real GDP growth]] (adjusted for inflation) is the primary gauge of economic momentum and a core input into monetary policy, risk sentiment, and cross-asset pricing.\n\n' +
      'For traders, GDP growth provides context on [[demand strength, recession risk, and policy durability]], influencing FX flows, yields, and equity valuations. Strong growth supports GBP via real yield support and capital inflows, while weak growth increases rate-cut probability and supports defensive FX and bonds.\n\n' +
      'Why GDP Matters for Markets:\n\n' +
      '• [[FX]]: Strong growth supports GBP via real yield support and capital inflows\n\n' +
      '• [[Rates]]: Faster growth can delay or limit rate cuts\n\n' +
      '• [[Equities]]: Supports earnings outlook but may cap valuation upside if rates stay elevated\n\n' +
      '• [[Risk Sentiment]]: Sustained expansion favors risk-on positioning\n\n' +
      'GDP growth is published quarterly, typically around the [[end of the month following the quarter end]], with revisions possible as more comprehensive data becomes available.',
    measurement:
      'The [[Office for National Statistics (ONS)]] calculates GDP growth as the percentage change in real GDP from one quarter to the previous quarter, [[annualized for comparability]]. The calculation uses chained dollars to adjust for inflation.\n\n' +
      'GDP is measured through three approaches:\n\n' +
      '• [[Expenditure approach]]: Sum of consumption, investment, government spending, and net exports\n\n' +
      '• [[Income approach]]: Sum of all income earned in production\n\n' +
      '• [[Production approach]]: Value added at each stage of production\n\n' +
      'Key components:\n\n' +
      '• [[Services sector]]: Primary driver of growth (currently strong)\n\n' +
      '• [[Production sector]]: More volatile but can drive growth trends (currently mixed)\n\n' +
      '• [[Construction sector]]: Affects growth and employment (currently flat)\n\n' +
      'Data is released quarterly, typically around the [[end of the month following the quarter end]], with [[multiple revisions]] as more comprehensive data becomes available. Release Frequency: Quarterly. Unit: Percent (%).',
    impact:
      'GDP growth has [[profound implications]] for GBP markets through multiple transmission channels:\n\n' +
      '[[Stronger GDP]]\n\n' +
      '• [[Supports GBP and real yields]]\n\n' +
      '• [[Reduces rate-cut urgency]]\n\n' +
      '• [[Favors cyclical assets]]\n\n' +
      '[[Weaker GDP]]\n\n' +
      '• [[Reopens recession risk pricing]]\n\n' +
      '• [[Increases rate-cut probability]]\n\n' +
      '• [[Supports defensive FX and bonds]]\n\n' +
      '[[Market Dynamics]]\n\n' +
      'GDP surprises tend to [[reprice rate expectations first]], with FX and equity volatility following. Markets react not just to the headline number but to [[components and revisions]], with consumption and investment data particularly scrutinized for forward-looking signals. GBP crosses remain sensitive to GDP surprises, with [[above-expectation growth supporting GBP]] via reduced easing pressure, while [[below-expectation growth pressuring GBP]] via increased easing expectations.',
    context:
      '[[Latest Growth Snapshot]]\n\n' +
      'Q1 2025 Real GDP: [[+0.7% quarter-on-quarter]]\n\n' +
      '[[Fastest growth in a year]], surpassing expectations of 0.6%\n\n' +
      'Q2 2025 Real GDP: [[+0.3% quarter-on-quarter]], moderating from Q1 but still above forecasts of 0.1%\n\n' +
      'Annual Growth: [[2024 GDP grew by 1.1%]], revised up from initial estimate of 0.9%, and an improvement from 0.4% growth in 2023\n\n' +
      'Key contributors:\n\n' +
      '• [[Services sector]]: Primary driver, with 0.7% increase in Q1 2025, driven by retail, wholesale, and computer programming\n\n' +
      '• [[Production sector]]: Rose 1.1% in Q1 2025 but declined 0.7% in March 2025\n\n' +
      '• [[Construction sector]]: Showed no growth in Q1 2025, following a 0.3% increase in Q4 2024\n\n' +
      '[[Institutional & Bank Commentary]]\n\n' +
      'Major financial institutions view the Q1 2025 strength as positive but expect moderation due to global uncertainties, inflation pressures, and domestic challenges.\n\n' +
      'Consensus themes among institutions:\n\n' +
      '• [[Growth is positive but modest]] relative to historical standards\n\n' +
      '• [[Services sector remains the primary driver]] of growth\n\n' +
      '• [[Business investment remains subdued]] due to weak demand, high costs, and uncertainties\n\n' +
      '• [[Consumer spending is modest]] due to slower real income growth\n\n' +
      'Forecasts vary:\n\n' +
      '• [[Bank of England]]: Revised 2025 growth down to 0.75% from 1.5%, citing global uncertainties and domestic challenges\n\n' +
      '• [[International Monetary Fund]]: Projects 1.3% growth for 2025, positioning the UK as the second-fastest-growing major economy after the U.S.\n\n' +
      '• [[Confederation of British Industry]]: Projects 1.4% growth for 2025 (upgraded from earlier forecasts) and 1.3% for 2026\n\n' +
      '• [[EY ITEM Club]]: Upgraded 2025 forecast to 1.5%, citing stronger-than-expected momentum\n\n' +
      '[[Central Bank & Policy Context]]\n\n' +
      'The Bank of England monitors GDP growth as part of its [[assessment of economic momentum and policy trade-offs]]. The MPC sets the Bank Rate based on growth, inflation, wage growth, and labor market conditions.\n\n' +
      'Current context: Q1 2025 growth of 0.7% supports the BoE\'s shift toward easing, but the Bank revised its 2025 growth forecast down to [[0.75% from 1.5%]], reflecting concerns about global uncertainties and domestic challenges. The BoE cut the Bank Rate to 4.50% in early 2025, reflecting concerns over growth and inflation.\n\n' +
      'The BoE\'s reaction function weighs [[growth momentum, inflation persistence, wage growth, and labor market conditions]]. Current levels support continued easing, but the pace depends on incoming data, especially growth and inflation dynamics. The BoE emphasizes [[data dependence]], with no pre-committed rate path, and remains ready to adjust policy based on incoming information.\n\n' +
      '[[Political & Structural Overlay]]\n\n' +
      'Fiscal policy: Government spending and tax policy affect growth through demand and supply channels. The [[Labour government has introduced measures]] aimed at stimulating long-term growth, including infrastructure investments and efforts to improve post-Brexit EU relations.\n\n' +
      'Brexit and trade: Trade relationships and supply chain shifts affect growth and competitiveness. [[Global trade tensions, particularly with the U.S.]], have introduced uncertainties affecting export performance and overall economic stability.\n\n' +
      'Structural factors: The UK\'s [[services-heavy economy]] affects growth dynamics and rate transmission, while [[housing market sensitivity]] to rates affects consumption and growth. [[Productivity challenges]] affect growth potential and inflation dynamics. [[Business investment remains subdued]] due to weak demand, high costs, and uncertainties.\n\n' +
      'The distinction between political narrative and policy reality is important: public statements emphasize growth support and competitiveness, but [[actual policy is constrained by fiscal rules, trade agreements, and structural factors]]. The BoE maintains operational independence, but political pressure can affect communication and expectations.',
    traderImplications:
      '[[What Traders Should Monitor Next]]\n\n' +
      'High-impact growth signals include:\n\n' +
      '• [[Quarterly GDP releases]] (typically around the end of the month following the quarter end)\n\n' +
      '• [[Monthly GDP estimates]] (provide early signals of quarterly trends)\n\n' +
      '• [[Component breakdowns]] (consumption, investment, government spending, net exports)\n\n' +
      '• [[Sectoral performance]] (services, production, construction)\n\n' +
      '• [[Revisions to previous quarters]] (can affect market expectations and policy assessments)\n\n' +
      '• [[BoE communications on growth]] and their implications for policy\n\n' +
      '[[Thresholds & Inflection Points]]\n\n' +
      'A move above [[0.8% quarter-on-quarter]] would signal stronger momentum and likely support GBP via reduced easing pressure. A move below [[0.0% (contraction)]] would signal recession risk and likely pressure GBP via increased easing expectations. The 0.3-0.7% range appears to be a near-term equilibrium, with significant deviations likely to shift market narratives.\n\n' +
      '[[Signals That Could Change the Narrative]]\n\n' +
      'Unexpected shifts in growth, especially if driven by consumption or investment, could alter Bank Rate expectations. Changes in services sector performance, affecting overall growth, could influence rate decisions. Changes in business investment, affecting growth potential, could shift market expectations. Changes in BoE communication tone, especially around forward guidance, could affect market positioning.\n\n' +
      '[[FXSentinel Usage]]\n\n' +
      'Within FXSentinel, UK GDP Growth functions best as:\n\n' +
      '• [[GBP directional bias tool]] (via growth momentum signals)\n\n' +
      '• [[BoE policy expectation driver]]\n\n' +
      '• [[Recession risk indicator]]\n\n' +
      '• [[Volatility trigger around data releases]]',
  },
  // JPY GDP Growth
  'gdp-growth-JPY': {
    overview:
      '[[Gross Domestic Product (GDP)]] measures the total value of goods and services produced within Japan. [[Real GDP growth]] (adjusted for inflation) is the primary gauge of economic momentum and a core input into monetary policy, risk sentiment, and cross-asset pricing.\n\n' +
      'For traders, GDP growth provides context on [[demand strength, recession risk, and policy durability]], influencing FX flows, yields, and equity valuations. Strong growth supports JPY via real yield support and capital inflows, while weak growth increases rate-cut probability and supports defensive FX and bonds.\n\n' +
      'Why GDP Matters for Markets:\n\n' +
      '• [[FX]]: Strong growth supports JPY via real yield support and capital inflows\n\n' +
      '• [[Rates]]: Faster growth can support rate hikes\n\n' +
      '• [[Equities]]: Supports earnings outlook but may cap valuation upside if rates stay elevated\n\n' +
      '• [[Risk Sentiment]]: Sustained expansion favors risk-on positioning\n\n' +
      'GDP growth is published quarterly, typically around the [[end of the month following the quarter end]], with revisions possible as more comprehensive data becomes available.',
    measurement:
      'The [[Cabinet Office, Government of Japan]] calculates GDP growth as the percentage change in real GDP from one quarter to the previous quarter, [[annualized for comparability]]. The calculation uses chained dollars to adjust for inflation.\n\n' +
      'GDP is measured through three approaches:\n\n' +
      '• [[Expenditure approach]]: Sum of consumption, investment, government spending, and net exports\n\n' +
      '• [[Income approach]]: Sum of all income earned in production\n\n' +
      '• [[Production approach]]: Value added at each stage of production\n\n' +
      'Key components:\n\n' +
      '• [[Consumption]]: Affects growth momentum and policy trade-offs\n\n' +
      '• [[Investment]]: Affects growth potential and competitiveness\n\n' +
      '• [[Exports]]: Affects growth and currency dynamics\n\n' +
      '• [[Government spending]]: Affects growth and fiscal policy trade-offs\n\n' +
      'Data is released quarterly, typically around the [[end of the month following the quarter end]], with [[multiple revisions]] as more comprehensive data becomes available. Release Frequency: Quarterly. Unit: Percent (%).',
    impact:
      'GDP growth has [[profound implications]] for JPY markets through multiple transmission channels:\n\n' +
      '[[Stronger GDP]]\n\n' +
      '• [[Supports JPY and real yields]]\n\n' +
      '• [[Supports rate hike expectations]]\n\n' +
      '• [[Favors cyclical assets]]\n\n' +
      '[[Weaker GDP]]\n\n' +
      '• [[Reopens recession risk pricing]]\n\n' +
      '• [[Reduces rate hike urgency]]\n\n' +
      '• [[Supports defensive FX and bonds]]\n\n' +
      '[[Market Dynamics]]\n\n' +
      'GDP surprises tend to [[reprice rate expectations first]], with FX and equity volatility following. Markets react not just to the headline number but to [[components and revisions]], with consumption and investment data particularly scrutinized for forward-looking signals. JPY crosses remain sensitive to GDP surprises, with [[above-expectation growth supporting JPY]] via increased normalization expectations, while [[below-expectation growth pressuring JPY]] via reduced normalization expectations.',
    context:
      '[[Latest Growth Snapshot]]\n\n' +
      'Q3 2025 Real GDP: [[-2.3% annualized]]\n\n' +
      '[[First contraction in six quarters]], steepest in two years\n\n' +
      'Q2 2025 Real GDP: [[+2.2% annualized]], driven by resilient exports and business investment\n\n' +
      'Q1 2025 Real GDP: [[-0.2% quarter-on-quarter]], first negative growth in four quarters\n\n' +
      'Annual Growth: [[2024 GDP grew by 0.1%]], reflecting challenges such as weak domestic demand and external uncertainties\n\n' +
      'Key contributors:\n\n' +
      '• [[Exports]]: Declined 1.2% in Q3 2025, partly due to U.S. tariffs impacting the auto industry\n\n' +
      '• [[Capital expenditure]]: Reduced, contributing to Q3 2025 contraction\n\n' +
      '• [[Consumption]]: Weaker than expected in Q4 2024, leading to downward revision\n\n' +
      '• [[Business investment]]: Remains robust due to high corporate profits and government subsidies\n\n' +
      '[[Institutional & Bank Commentary]]\n\n' +
      'Major financial institutions view the Q3 2025 contraction as concerning but note underlying resilience, with domestic demand expected to support growth going forward. The volatility reflects the impact of U.S. trade tariffs and external uncertainties, but domestic factors such as wage growth and business investment remain supportive.\n\n' +
      'Consensus themes among institutions:\n\n' +
      '• [[Growth is volatile]] but shows underlying resilience\n\n' +
      '• [[Domestic demand, bolstered by strong wage growth]], is expected to drive growth\n\n' +
      '• [[External factors, particularly U.S. tariffs]], pose challenges to export-driven growth\n\n' +
      '• [[Business investment remains robust]] due to high corporate profits and government subsidies\n\n' +
      'Forecasts vary:\n\n' +
      '• [[Japanese government]]: Revised FY2026 real GDP growth projection to 1.3%, up from 0.9%, reflecting expectations of eased inflation supporting private consumption and business investment\n\n' +
      '• [[OECD]]: Projects 0.7% growth in 2025 and 0.4% in 2026, driven primarily by domestic demand\n\n' +
      '• [[IMF]]: Projects 1.2% growth for 2025 and 0.8% for 2026, with domestic demand expected to be the primary driver\n\n' +
      '[[Central Bank & Policy Context]]\n\n' +
      'The Bank of Japan monitors GDP growth as part of its [[assessment of economic momentum and policy trade-offs]]. The Policy Board sets the Policy Rate based on growth, inflation, wage growth, and financial stability.\n\n' +
      'Current context: Q3 2025 contraction of 2.3% annualized reflects external challenges, particularly U.S. tariffs affecting exports, but domestic demand remains supportive. The BoJ raised the Policy Rate to 0.75% in December 2025, citing persistent inflation above target, but the contraction may affect the pace of normalization.\n\n' +
      'The BoJ\'s reaction function weighs [[growth momentum, inflation persistence, wage growth, and financial stability]]. Current levels support continued normalization, but the pace depends on incoming data, especially growth and inflation dynamics. The BoJ emphasizes [[data dependence]], with no pre-committed rate path, and remains ready to adjust policy based on incoming information.\n\n' +
      '[[Political & Structural Overlay]]\n\n' +
      'Fiscal policy: Government spending and tax policy affect growth through demand and supply channels. The [[Japanese government approved a 21.3 trillion yen ($135.4 billion) stimulus package]] in November 2025, aimed at revitalizing the economy through subsidies, tax cuts, and consumer aid. The government has implemented fiscal stimulus packages aimed at supporting medium-term investments in areas like artificial intelligence and semiconductors, as well as enhancing defense capabilities.\n\n' +
      'Trade relations: Trade relationships and supply chain shifts affect growth and competitiveness. The [[imposition of U.S. tariffs has introduced uncertainties]], particularly affecting the automotive sector. While some sectors have shown resilience, ongoing trade tensions pose risks to export-driven growth.\n\n' +
      'Structural factors: Japan\'s [[aging population]] affects growth potential and inflation dynamics, while the [[export-oriented economy]] affects rate transmission and currency dynamics. [[Productivity challenges]] affect growth potential and inflation dynamics. [[Labor market dynamics]]: Efforts are needed to increase labor market participation, especially among seniors and women, and to enhance labor mobility to address shortages.\n\n' +
      'The distinction between political narrative and policy reality is important: public statements emphasize growth support and competitiveness, but [[actual policy is constrained by fiscal rules, trade agreements, and structural factors]]. The BoJ maintains operational independence, but political pressure can affect communication and expectations.',
    traderImplications:
      '[[What Traders Should Monitor Next]]\n\n' +
      'High-impact growth signals include:\n\n' +
      '• [[Quarterly GDP releases]] (typically around the end of the month following the quarter end)\n\n' +
      '• [[Component breakdowns]] (consumption, investment, government spending, net exports)\n\n' +
      '• [[Export performance]] (affects overall growth and currency dynamics)\n\n' +
      '• [[Business investment trends]] (affects growth potential and competitiveness)\n\n' +
      '• [[Revisions to previous quarters]] (can affect market expectations and policy assessments)\n\n' +
      '• [[BoJ communications on growth]] and their implications for policy\n\n' +
      '[[Thresholds & Inflection Points]]\n\n' +
      'A move above [[1.0% quarter-on-quarter]] would signal stronger momentum and likely support JPY via increased normalization expectations. A move below [[-0.5% (contraction)]] would signal recession risk and likely pressure JPY via reduced normalization expectations. The current volatility suggests no clear equilibrium, with significant deviations likely to shift market narratives.\n\n' +
      '[[Signals That Could Change the Narrative]]\n\n' +
      'Unexpected shifts in growth, especially if driven by consumption or investment, could alter Policy Rate expectations. Changes in export performance, affecting overall growth, could influence rate decisions. Changes in business investment, affecting growth potential, could shift market expectations. Changes in BoJ communication tone, especially around forward guidance, could affect market positioning.\n\n' +
      '[[FXSentinel Usage]]\n\n' +
      'Within FXSentinel, Japan GDP Growth functions best as:\n\n' +
      '• [[JPY directional bias tool]] (via growth momentum signals)\n\n' +
      '• [[BoJ policy expectation driver]]\n\n' +
      '• [[Recession risk indicator]]\n\n' +
      '• [[Volatility trigger around data releases]]',
  },
  // EUR Unemployment Rate
  'unemployment-EUR': {
    overview:
      'The [[Euro Area Unemployment Rate]] measures the percentage of the labor force that is unemployed and actively seeking work within the eurozone. Published monthly by [[Eurostat]], the statistical office of the European Union, this seasonally adjusted indicator covers all 20 eurozone countries and serves as a [[critical gauge of labor market health]] and economic performance.\n\n' +
      'The indicator is structurally important because it reflects [[labor market tightness]], influences [[wage dynamics]], and signals the [[output gap]]—the difference between actual and potential economic output. It feeds directly into the [[European Central Bank\'s reaction function]], influencing expectations for interest rates, asset purchases, and forward guidance. In a currency union, unemployment data also highlights [[cross-country divergences]] that can complicate policy trade-offs.\n\n' +
      'For traders, the Euro Area Unemployment Rate is a [[leading indicator of ECB policy shifts]] and EUR strength. Low unemployment supports wage growth and inflation persistence, potentially constraining ECB easing, while rising unemployment increases pressure for accommodative policy, typically weighing on EUR.\n\n' +
      'Markets react less to absolute unemployment levels and more to [[surprises versus expectations, trend momentum, and the interplay with wage growth and inflation data]].',
    measurement:
      '[[Eurostat]] calculates the Euro Area Unemployment Rate using the [[International Labour Organization (ILO) definition]]: unemployed persons are those aged 15-74 who are without work, available to start work within two weeks, and have actively sought employment in the previous four weeks.\n\n' +
      'Key methodological points:\n\n' +
      '• [[Seasonally adjusted]]: Removes seasonal patterns to reveal underlying trends\n\n' +
      '• [[Harmonized methodology]]: Ensures comparability across all EU member states\n\n' +
      '• [[Labor force participation]]: Only includes those actively seeking work, excluding discouraged workers\n\n' +
      '• [[Country-level breakdowns]]: Available for individual member states, revealing structural divergences\n\n' +
      'Data is published approximately [[one month after the reference period]], typically around the 2nd of each month, with revisions possible in subsequent releases. Frequency: Monthly. Unit: Percentage (%).',
    impact:
      'Unemployment readings have [[profound implications]] for EUR markets through multiple transmission channels:\n\n' +
      '[[Low and Falling Unemployment]]\n\n' +
      '• [[Tightens labor market conditions]], supporting wage growth and inflation persistence\n\n' +
      '• [[Constrains ECB easing]], potentially supporting EUR via higher real rate expectations\n\n' +
      '• [[Signals economic resilience]], supporting risk-on positioning in EUR crosses\n\n' +
      '• [[Reduces output gap]], limiting scope for accommodative policy\n\n' +
      '[[Rising Unemployment]]\n\n' +
      '• [[Increases economic slack]], reducing wage pressures and inflation risks\n\n' +
      '• [[Strengthens case for ECB easing]], potentially weighing on EUR\n\n' +
      '• [[Signals economic deterioration]], increasing recession risk pricing\n\n' +
      '• [[Opens policy space]] for accommodative measures, supporting bond markets\n\n' +
      '[[Market Dynamics]]\n\n' +
      'EUR crosses remain sensitive to unemployment surprises, with [[above-expectation readings tending to weaken EUR]] via dovish repricing of ECB expectations, while [[below-expectation readings support EUR]] through reduced easing pressure. The interplay between unemployment, wage growth, and inflation is crucial for ECB policy anticipation. Markets focus on [[expectations versus outcomes]], with significant deviations from consensus driving immediate volatility.',
    context:
      '[[Current Reading & Trend (Late 2025)]]\n\n' +
      'As of October 2025, the euro area unemployment rate stood at [[6.4%]], stable compared to September 2025 but up from 6.3% in October 2024. The broader EU unemployment rate was 6.0% in October 2025, also stable month-on-month but up from 5.8% a year earlier.\n\n' +
      'The trend shows [[near-term stability but a slight year-on-year increase]], suggesting the labor market is holding up despite sluggish economic growth. The rate remains low by historical standards, but the uptick from 2024 levels indicates some softening. The stability in recent months points to a resilient labor market, though underlying growth concerns remain.\n\n' +
      '[[Institutional & Bank Commentary]]\n\n' +
      'Major financial institutions interpret the current unemployment level as [[resilient given weak growth]], but note risks from trade tensions, energy costs, and structural headwinds in major economies like Germany. The European Commission revised its 2025 euro area growth forecast down to [[0.9% (from 1.3%)]], citing trade tensions, a stronger euro, and declining energy prices.\n\n' +
      'Analysts highlight that while the unemployment rate remains low, [[the slight year-on-year increase serves as a warning sign]], with divergence between low unemployment and weak GDP growth creating uncertainty. Consensus suggests cautious optimism, with some divergence regarding the sustainability of low unemployment amid these challenges.\n\n' +
      '[[Central Bank & Policy Context]]\n\n' +
      'The ECB monitors unemployment as a key input for [[price stability and economic growth]]. It feeds into wage dynamics, inflation expectations, and the output gap. The ECB\'s reaction function links labor market tightness to wage pressures and, in turn, inflation persistence.\n\n' +
      'Current context: Unemployment near 6.4% with low inflation suggests [[limited wage-driven inflation pressure]], allowing the ECB to focus on growth support. However, the slight year-on-year increase and weak growth create a trade-off between supporting activity and maintaining price stability. The ECB balances these considerations, with internal views varying on the urgency of easing versus maintaining a cautious stance.\n\n' +
      'The ECB\'s forward guidance and rate decisions depend on the [[unemployment-inflation-wage nexus]]. If unemployment rises while inflation remains low, the case for easing strengthens. If unemployment stays low but wage growth accelerates, the focus shifts to inflation risks. The current environment—stable unemployment, low inflation, weak growth—supports a [[cautious, data-dependent approach]].\n\n' +
      '[[Political & Structural Overlay]]\n\n' +
      'Political leaders acknowledge the importance of maintaining low unemployment, but [[fiscal constraints and cross-country differences limit coordinated action]]. Trade tensions, particularly with the United States, add uncertainty and affect business confidence and investment. Structural issues in major economies (e.g., Germany\'s energy costs and export competitiveness) contribute to the slowdown.\n\n' +
      'Fiscal policy debates center on stimulus versus consolidation, with high-debt countries facing constraints. Structural reforms to improve labor market flexibility and competitiveness are discussed but face implementation challenges. The distinction between political narrative and policy reality is important: public statements emphasize employment support, but actual fiscal and structural responses are [[limited by institutional and economic constraints]].',
    traderImplications:
      '[[What Traders Should Monitor Next]]\n\n' +
      'High-impact drivers for unemployment and policy repricing:\n\n' +
      '• [[Monthly Eurostat unemployment releases]] (typically around the 2nd of each month)\n\n' +
      '• [[Country-level divergences]] (especially Germany, France, Italy, Spain)\n\n' +
      '• [[Wage growth trends]] (unemployment-wage nexus is critical for ECB policy)\n\n' +
      '• [[Job vacancy rates and labor force participation]] (early signals of labor market shifts)\n\n' +
      '• [[ECB communications on labor market conditions]] and their implications for policy\n\n' +
      '[[Thresholds & Inflection Points]]\n\n' +
      'A move above [[6.6%]] would signal deterioration and likely increase easing expectations. A move below [[6.2%]] would suggest tightening and could support a less dovish ECB stance. The 6.4% level appears to be a near-term equilibrium, with significant deviations likely to shift market narratives.\n\n' +
      '[[Signals That Could Change the Narrative]]\n\n' +
      'Unexpected shifts in unemployment, especially if accompanied by changes in wage growth, inflation, or GDP, could alter ECB policy expectations. Country-level divergences (e.g., rising unemployment in Germany while it falls in France) could affect policy trade-offs. Changes in job vacancy rates, labor force participation, and sector-specific employment trends provide [[early signals of labor market shifts]].\n\n' +
      '[[FXSentinel Usage]]\n\n' +
      'Within FXSentinel, the Euro Area Unemployment Rate functions best as:\n\n' +
      '• [[ECB policy expectation driver]]\n\n' +
      '• [[EUR bias validator]] (via wage-inflation-policy nexus)\n\n' +
      '• [[Growth momentum signal]]\n\n' +
      '• [[Volatility trigger around data releases]]',
  },
  // EUR Current Account
  'current-account-EUR': {
    overview:
      'The [[Euro Area Current Account Balance]] measures the net flow of goods, services, primary income (investment income, compensation of employees), and secondary income (transfers, remittances) between the eurozone and the rest of the world over a given period. Published monthly by the [[European Central Bank (ECB)]] and compiled from national central bank data, it reflects the eurozone\'s external economic position and competitiveness.\n\n' +
      'A surplus indicates the eurozone is a [[net lender to the rest of the world]], while a deficit suggests it is a [[net borrower]]. The current account is part of the balance of payments and reflects trade competitiveness, savings-investment dynamics, and capital flow drivers.\n\n' +
      'For traders, the current account influences EUR valuation through [[capital flows]], reflects [[export competitiveness]], signals [[structural imbalances]], and affects [[ECB policy considerations]]. A sustained surplus supports EUR via capital inflows, while a narrowing surplus or deficit can pressure EUR and signal economic challenges.\n\n' +
      'Markets focus less on absolute current account levels and more on [[trend direction, component breakdowns, and the interplay with growth, inflation, and monetary policy expectations]].',
    measurement:
      'The [[European Central Bank (ECB)]] compiles current account data from [[national central banks]] within the eurozone using standardized balance of payments methodology aligned with [[International Monetary Fund (IMF) guidelines]].\n\n' +
      'The current account consists of four main components:\n\n' +
      '• [[Goods balance]]: Exports minus imports of physical goods\n\n' +
      '• [[Services balance]]: Exports minus imports of services (tourism, financial services, transportation)\n\n' +
      '• [[Primary income]]: Investment income (dividends, interest) and compensation of employees from cross-border activities\n\n' +
      '• [[Secondary income]]: Current transfers, remittances, and other unilateral transfers\n\n' +
      'Data is published monthly, typically with a [[lag of approximately six weeks]] after the reference month. Quarterly data provides more detailed breakdowns, including geographic patterns and component analysis. Frequency: Monthly (with quarterly detailed breakdowns). Unit: Billions of euros (€), also expressed as percentage of GDP.',
    impact:
      'Current account readings have [[profound implications]] for EUR markets through multiple transmission channels:\n\n' +
      '[[Sustained Surplus]]\n\n' +
      '• [[Supports EUR strength]] via capital inflows and demand for eurozone assets\n\n' +
      '• [[Reflects export competitiveness]] and structural economic strength\n\n' +
      '• [[Signals net lending position]], supporting currency valuation\n\n' +
      '• [[Reduces external vulnerability]], supporting risk sentiment\n\n' +
      '[[Narrowing Surplus or Deficit]]\n\n' +
      '• [[Reduces EUR support]] via weaker capital flows\n\n' +
      '• [[Signals competitiveness challenges]] or structural shifts\n\n' +
      '• [[Increases external vulnerability]], potentially weighing on EUR\n\n' +
      '• [[May affect ECB policy considerations]] if combined with growth concerns\n\n' +
      '[[Market Dynamics]]\n\n' +
      'EUR crosses remain sensitive to current account trends, with [[sustained surpluses supporting EUR]] through capital flow dynamics, while [[narrowing surpluses or deficits can pressure EUR]] via reduced capital inflows. Markets focus on [[trend direction and component breakdowns]], with shifts in goods, services, or primary income providing signals about competitiveness and structural position. The interplay between current account, growth, inflation, and ECB policy is crucial for EUR valuation.',
    context:
      '[[Current Reading & Trend (Late 2025)]]\n\n' +
      'As of October 2025, the euro area recorded a current account surplus of [[€26 billion]], up from €24 billion in September 2025. Over the 12 months ending October 2025, the cumulative surplus amounted to [[€313 billion (2.0% of GDP)]], down from €419 billion (2.8% of GDP) in the preceding 12-month period.\n\n' +
      'The October 2025 surplus was driven by [[goods (€31 billion) and services (€13 billion)]], partially offset by deficits in [[secondary income (€16 billion) and primary income (€3 billion)]].\n\n' +
      'The trend shows a [[narrowing surplus]], declining from 2.8% of GDP in 2024 to 2.0% of GDP in the 12 months to October 2025. This reflects a [[shift from surplus to deficit in primary income]] and a larger secondary income deficit, despite continued goods and services surpluses.\n\n' +
      'In 2024, the euro area recorded a full-year surplus of [[€426 billion (2.8% of GDP)]], up from €243 billion (1.7% of GDP) in 2023, driven by larger surpluses in goods (€372 billion, up from €264 billion), services (€169 billion, up from €127 billion), and primary income (€54 billion, up from €20 billion).\n\n' +
      '[[Institutional & Bank Commentary]]\n\n' +
      'Major financial institutions interpret the narrowing surplus as a sign of [[structural shifts in the eurozone\'s external position]]. The decline from 2.8% to 2.0% of GDP reflects weaker primary income flows and larger secondary income outflows, even as goods and services remain in surplus.\n\n' +
      'Consensus themes among institutions:\n\n' +
      '• [[The surplus remains structurally positive]] but is moderating\n\n' +
      '• [[Primary income turning negative]] suggests weaker investment returns or higher outbound income payments\n\n' +
      '• [[The goods surplus remains robust]], indicating export competitiveness\n\n' +
      '• [[The services surplus supports]] the overall position\n\n' +
      'Geographic patterns show the euro area maintains [[significant bilateral surpluses with the United Kingdom (€198 billion) and Switzerland (€73 billion)]], while recording the [[largest deficit with China (€134 billion)]], reflecting import dependency and trade structure.\n\n' +
      '[[Central Bank & Policy Context]]\n\n' +
      'The ECB monitors the current account as part of its [[assessment of external stability and competitiveness]]. While not a direct policy target, it informs policy considerations through its relationship with growth, inflation, and financial stability.\n\n' +
      'Current context: The surplus remains positive but narrowing, consistent with [[moderate growth and external competitiveness]]. The shift in primary income suggests changing investment return dynamics. The ECB balances external position with domestic growth and inflation objectives.\n\n' +
      'The ECB\'s reaction function considers the current account alongside inflation, growth, and financial conditions. A narrowing surplus alone is unlikely to drive policy, but [[combined with weak growth or inflation concerns]], it can influence the policy stance.\n\n' +
      '[[Political & Structural Overlay]]\n\n' +
      'Trade tensions, particularly with the United States and China, affect the current account through [[tariffs, supply chain shifts, and export competitiveness]]. The large deficit with China reflects import dependency and trade structure.\n\n' +
      'Energy dynamics: Energy import costs affect the goods balance, though recent normalization has reduced pressure. [[Energy security and diversification efforts]] may reshape trade patterns over time.\n\n' +
      'Structural factors: Germany\'s export-oriented model drives the goods surplus, while services competitiveness supports the services surplus. [[Demographic trends and savings patterns]] influence the overall position.\n\n' +
      'The distinction between political narrative and policy reality is important: public statements emphasize trade competitiveness and external strength, but [[actual policy responses are constrained by fiscal rules, trade agreements, and structural factors]]. The narrowing surplus reflects underlying economic shifts rather than policy choices.',
    traderImplications:
      '[[What Traders Should Monitor Next]]\n\n' +
      'High-impact drivers for current account and EUR repricing:\n\n' +
      '• [[Monthly ECB balance of payments releases]] (typically around six weeks after reference month)\n\n' +
      '• [[Quarterly detailed breakdowns]] with component and geographic analysis\n\n' +
      '• [[Goods balance trends]] (export competitiveness and import dynamics)\n\n' +
      '• [[Services balance trends]] (services trade competitiveness)\n\n' +
      '• [[Primary income shifts]] (investment returns and compensation flows)\n\n' +
      '• [[Geographic patterns]] (especially with UK, China, and US)\n\n' +
      '• [[Energy price volatility]] affecting goods balance\n\n' +
      '[[Thresholds & Inflection Points]]\n\n' +
      'A move toward [[deficit (negative current account)]] would signal deterioration and likely pressure EUR. A return to [[above 2.5% of GDP]] would signal improvement and support EUR. The 2.0% level appears to be a near-term equilibrium, with significant deviations likely to shift market narratives.\n\n' +
      '[[Signals That Could Change the Narrative]]\n\n' +
      'Unexpected shifts in the goods or services balance, especially if driven by trade tensions or competitiveness changes, could alter EUR dynamics. Continued deterioration in primary income, suggesting structural shifts in investment returns, would signal changing capital flow patterns. Changes in geographic patterns, especially with major partners like the UK, China, or the US, could affect trade flows and EUR positioning.\n\n' +
      '[[FXSentinel Usage]]\n\n' +
      'Within FXSentinel, the Euro Area Current Account Balance functions best as:\n\n' +
      '• [[EUR structural support indicator]] (via capital flows)\n\n' +
      '• [[Competitiveness gauge]] (goods and services balances)\n\n' +
      '• [[External vulnerability signal]]\n\n' +
      '• [[Component analysis tool]] for understanding underlying dynamics',
  },
  // GBP Unemployment Rate
  'unemployment-GBP': {
    overview:
      'The [[United Kingdom Unemployment Rate]] measures the percentage of the labor force that is unemployed and actively seeking work. Published monthly by the [[Office for National Statistics (ONS)]], it is a key indicator of labor market health and economic slack, closely monitored by the Bank of England for monetary policy decisions.\n\n' +
      'The unemployment rate reflects [[labor market tightness]], influences [[wage dynamics]], and signals the [[output gap]]—the difference between actual and potential economic output. It feeds directly into the [[Bank of England\'s reaction function]], influencing expectations for interest rates, forward guidance, and policy stance.\n\n' +
      'For traders, the UK Unemployment Rate is a [[leading indicator of BoE policy shifts]] and GBP strength. Low unemployment supports wage growth and inflation persistence, potentially constraining BoE easing, while rising unemployment increases pressure for accommodative policy, typically weighing on GBP.\n\n' +
      'Markets react less to absolute unemployment levels and more to [[surprises versus expectations, trend momentum, and the interplay with wage growth and inflation data]].',
    measurement:
      'The [[Office for National Statistics (ONS)]] calculates the UK Unemployment Rate using the [[International Labour Organization (ILO) definition]]: unemployed persons are those aged 16 and over who are without work, available to start work within two weeks, and have actively sought employment in the previous four weeks.\n\n' +
      'Key methodological points:\n\n' +
      '• [[Three-month rolling average]]: Provides a smoother view of trends, reducing monthly volatility\n\n' +
      '• [[Harmonized methodology]]: Ensures comparability with international standards\n\n' +
      '• [[Labor force participation]]: Only includes those actively seeking work, excluding discouraged workers\n\n' +
      '• [[Age and regional breakdowns]]: Available for different age groups and regions, revealing structural divergences\n\n' +
      'Data is published monthly, typically around the [[middle of the following month]], with revisions possible in subsequent releases. Frequency: Monthly (three-month rolling average). Unit: Percentage (%).',
    impact:
      'Unemployment readings have [[profound implications]] for GBP markets through multiple transmission channels:\n\n' +
      '[[Low and Falling Unemployment]]\n\n' +
      '• [[Tightens labor market conditions]], supporting wage growth and inflation persistence\n\n' +
      '• [[Constrains BoE easing]], potentially supporting GBP via higher real rate expectations\n\n' +
      '• [[Signals economic resilience]], supporting risk-on positioning in GBP crosses\n\n' +
      '• [[Reduces output gap]], limiting scope for accommodative policy\n\n' +
      '[[Rising Unemployment]]\n\n' +
      '• [[Increases economic slack]], reducing wage pressures and inflation risks\n\n' +
      '• [[Strengthens case for BoE easing]], potentially weighing on GBP\n\n' +
      '• [[Signals economic deterioration]], increasing recession risk pricing\n\n' +
      '• [[Opens policy space]] for accommodative measures, supporting bond markets\n\n' +
      '[[Market Dynamics]]\n\n' +
      'GBP crosses remain sensitive to unemployment surprises, with [[above-expectation readings tending to weaken GBP]] via dovish repricing of BoE expectations, while [[below-expectation readings support GBP]] through reduced easing pressure. The interplay between unemployment, wage growth, and inflation is crucial for BoE policy anticipation. Markets focus on [[expectations versus outcomes]], with significant deviations from consensus driving immediate volatility.',
    context:
      '[[Current Reading & Trend (Late 2025)]]\n\n' +
      'As of the three months to October 2025, the UK unemployment rate stood at [[5.1%]], the highest since January 2021. This is up from 4.4% in the same period in 2024, indicating a [[cooling labor market]].\n\n' +
      'Recent trend: The unemployment rate has been rising from lower levels, with the three months to October 2025 at 5.1% (up from 4.4% a year earlier). The [[employment rate declined to 74.9%]] for individuals aged 16 to 64, a slight decrease from the previous quarter. The [[economic inactivity rate is 21.0%]] for those aged 16 to 64, showing a marginal decline over the year.\n\n' +
      'The trend shows a [[cooling labor market]], with rising unemployment, declining employment, and increased redundancies (156,000 in the three months to October 2025). [[Youth unemployment has risen to 16.0%]], with 735,000 individuals aged 16 to 24 unemployed, an increase of 113,000 from the previous quarter.\n\n' +
      '[[Institutional & Bank Commentary]]\n\n' +
      'Major financial institutions interpret the rise to 5.1% as a sign of [[labor market cooling]], reflecting economic slowdown and reduced hiring. The increase from 4.4% a year earlier indicates a shift from tight to balanced-to-soft conditions.\n\n' +
      'Consensus themes among institutions:\n\n' +
      '• [[The labor market is cooling]] but remains relatively tight by historical standards\n\n' +
      '• [[Youth unemployment is a particular concern]], rising to 16.0%\n\n' +
      '• [[Wage growth remains robust]] but is decelerating, especially in the private sector\n\n' +
      '• [[The rise in unemployment supports]] the case for continued rate cuts\n\n' +
      'Analysts expect unemployment to [[remain elevated but moderate]] relative to historical peaks, with the pace of increase depending on economic growth and business investment.\n\n' +
      '[[Central Bank & Policy Context]]\n\n' +
      'The Bank of England monitors unemployment as a key input for [[price stability and economic growth]]. It feeds into wage dynamics, inflation expectations, and the output gap. The BoE\'s reaction function links labor market tightness to wage pressures and, in turn, inflation persistence.\n\n' +
      'Current context: Unemployment at 5.1%, the highest since January 2021, with easing inflation suggests [[increased economic slack]], allowing the BoE to focus on growth support. The rise in unemployment and weak growth create a case for accommodative policy. The BoE cut the Bank Rate to 3.75% in December 2025, citing [[labor market cooling and easing inflation]].\n\n' +
      'The BoE\'s forward guidance and rate decisions depend on the [[unemployment-inflation-wage nexus]]. If unemployment rises while inflation remains low, the case for easing strengthens. If unemployment stays low but wage growth accelerates, the focus shifts to inflation risks. The current environment—rising unemployment, easing inflation, weak growth—supports continued easing.\n\n' +
      '[[Political & Structural Overlay]]\n\n' +
      'Political leaders acknowledge the importance of maintaining low unemployment, but [[fiscal constraints and economic challenges limit coordinated action]]. The rise in unemployment, particularly youth unemployment, has raised concerns about social and economic stability.\n\n' +
      'Fiscal policy: Government spending and tax policy affect labor market conditions through demand channels. [[Fiscal support can reduce unemployment]] but is constrained by fiscal rules. The Labour government has introduced measures aimed at stimulating long-term growth.\n\n' +
      'Structural factors: The UK\'s [[services-heavy economy]] affects labor market dynamics and rate transmission, while [[youth unemployment is a particular concern]], reflecting structural challenges. [[Regional divergences]] in unemployment can affect policy trade-offs. [[Economic inactivity remains elevated]], affecting labor supply.\n\n' +
      'The distinction between political narrative and policy reality is important: public statements emphasize employment support and growth, but [[actual policy responses are constrained by fiscal rules, trade agreements, and structural factors]]. The rise in unemployment reflects underlying economic shifts rather than policy choices.',
    traderImplications:
      '[[What Traders Should Monitor Next]]\n\n' +
      'High-impact drivers for unemployment and policy repricing:\n\n' +
      '• [[Monthly ONS unemployment releases]] (typically around the middle of the following month)\n\n' +
      '• [[Youth unemployment trends]] (particular concern, currently at 16.0%)\n\n' +
      '• [[Employment rate and economic inactivity]] (affects labor supply and economic activity)\n\n' +
      '• [[Redundancies data]] (early signals of labor market deterioration)\n\n' +
      '• [[Wage growth trends]] (unemployment-wage nexus is critical for BoE policy)\n\n' +
      '• [[BoE communications on labor market conditions]] and their implications for policy\n\n' +
      '[[Thresholds & Inflection Points]]\n\n' +
      'A move above [[5.5%]] would signal further deterioration and likely increase easing expectations. A move below [[4.5%]] would suggest stabilization and could support a less dovish BoE stance. The 5.1% level appears to be a near-term equilibrium, with significant deviations likely to shift market narratives.\n\n' +
      '[[Signals That Could Change the Narrative]]\n\n' +
      'Unexpected shifts in unemployment, especially if accompanied by changes in wage growth, inflation, or GDP, could alter BoE policy expectations. Changes in youth unemployment, affecting social and economic stability, could influence policy trade-offs. Changes in employment rate and economic inactivity, affecting labor supply and potential growth, could provide early signals of labor market shifts.\n\n' +
      '[[FXSentinel Usage]]\n\n' +
      'Within FXSentinel, the UK Unemployment Rate functions best as:\n\n' +
      '• [[BoE policy expectation driver]]\n\n' +
      '• [[GBP bias validator]] (via wage-inflation-policy nexus)\n\n' +
      '• [[Growth momentum signal]]\n\n' +
      '• [[Volatility trigger around data releases]]',
  },
  // JPY Unemployment Rate
  'unemployment-JPY': {
    overview:
      'The [[Japan Unemployment Rate]] measures the percentage of the labor force that is unemployed and actively seeking work. Published monthly by the [[Statistics Bureau of Japan]], it is a key indicator of labor market health and economic slack, closely monitored by the Bank of Japan for monetary policy decisions.\n\n' +
      'The unemployment rate reflects [[labor market tightness]], influences [[wage dynamics]], and signals the [[output gap]]—the difference between actual and potential economic output. It feeds directly into the [[Bank of Japan\'s reaction function]], influencing expectations for interest rates, forward guidance, and policy stance.\n\n' +
      'For traders, the Japan Unemployment Rate is a [[leading indicator of BoJ policy shifts]] and JPY strength. Low unemployment supports wage growth and inflation persistence, potentially constraining BoJ easing, while rising unemployment increases pressure for accommodative policy, typically weighing on JPY.\n\n' +
      'Markets react less to absolute unemployment levels and more to [[surprises versus expectations, trend momentum, and the interplay with wage growth and inflation data]].',
    measurement:
      'The [[Statistics Bureau of Japan]] calculates the Japan Unemployment Rate using the [[International Labour Organization (ILO) definition]]: unemployed persons are those aged 15 and over who are without work, available to start work within one week, and have actively sought employment in the previous four weeks.\n\n' +
      'Key methodological points:\n\n' +
      '• [[Harmonized methodology]]: Ensures comparability with international standards\n\n' +
      '• [[Labor force participation]]: Only includes those actively seeking work, excluding discouraged workers\n\n' +
      '• [[Age and gender breakdowns]]: Available for different age groups and genders, revealing structural patterns\n\n' +
      '• [[Jobs-to-applicants ratio]]: Provides additional context on labor market tightness\n\n' +
      'Data is published monthly, typically around the [[end of the following month]], with revisions possible in subsequent releases. Frequency: Monthly. Unit: Percentage (%).',
    impact:
      'Unemployment readings have [[profound implications]] for JPY markets through multiple transmission channels:\n\n' +
      '[[Low and Falling Unemployment]]\n\n' +
      '• [[Tightens labor market conditions]], supporting wage growth and inflation persistence\n\n' +
      '• [[Constrains BoJ easing]], potentially supporting JPY via higher real rate expectations\n\n' +
      '• [[Signals economic resilience]], supporting risk-on positioning in JPY crosses\n\n' +
      '• [[Reduces output gap]], limiting scope for accommodative policy\n\n' +
      '[[Rising Unemployment]]\n\n' +
      '• [[Increases economic slack]], reducing wage pressures and inflation risks\n\n' +
      '• [[Strengthens case for BoJ easing]], potentially weighing on JPY\n\n' +
      '• [[Signals economic deterioration]], increasing recession risk pricing\n\n' +
      '• [[Opens policy space]] for accommodative measures, supporting bond markets\n\n' +
      '[[Market Dynamics]]\n\n' +
      'JPY crosses remain sensitive to unemployment surprises, with [[above-expectation readings tending to weaken JPY]] via dovish repricing of BoJ expectations, while [[below-expectation readings support JPY]] through reduced easing pressure. The interplay between unemployment, wage growth, and inflation is crucial for BoJ policy anticipation. Markets focus on [[expectations versus outcomes]], with significant deviations from consensus driving immediate volatility.',
    context:
      '[[Current Reading & Trend (Late 2025)]]\n\n' +
      'As of November 2025, Japan\'s unemployment rate stood at [[2.6%]], unchanged from the previous three months and aligning with market expectations. This rate represents the [[highest level since July 2024]].\n\n' +
      'Recent trend: The unemployment rate has been stable at 2.6% for three consecutive months, with November 2025 at 2.6% (unchanged from previous three months), October 2025 at 2.6% (unchanged from same month previous year, highest in 15 months), and September 2025 at 2.6%.\n\n' +
      'The [[number of unemployed individuals decreased by 40,000 to 1.81 million]] in November 2025, while [[employment increased by 500,000 to a record high of 68.51 million]]. The labor force saw a modest rise of 20,000, reaching 70.32 million. The [[labor force participation rate was 64.1%]], slightly down from 64.2% in October but up from 63.5% a year earlier.\n\n' +
      'The [[jobs-to-applicants ratio remained steady at 1.18]], the lowest since January 2022, indicating 118 job openings for every 100 job seekers. The trend shows a [[stable labor market with record-high employment]], but the slight increase in unemployment from lower levels suggests some labor market softening.\n\n' +
      '[[Institutional & Bank Commentary]]\n\n' +
      'Major financial institutions view the 2.6% rate as [[low by international standards]], reflecting a resilient labor market despite economic challenges. The stability at 2.6% for three consecutive months, combined with record-high employment, suggests underlying labor market strength, but the slight increase from lower levels indicates some softening.\n\n' +
      'Consensus themes among institutions:\n\n' +
      '• [[Unemployment remains low by international standards]], among the lowest in the OECD\n\n' +
      '• [[Employment has reached record highs]], reflecting labor market resilience\n\n' +
      '• [[Labor force participation has increased]], particularly among women and seniors\n\n' +
      '• [[The jobs-to-applicants ratio remains above 1.0]], indicating labor market tightness\n\n' +
      'The unemployment rate is projected to [[remain around 2.6% in 2026]], according to econometric models, with the pace of change depending on economic growth and labor market dynamics.\n\n' +
      '[[Central Bank & Policy Context]]\n\n' +
      'The Bank of Japan monitors unemployment as a key input for [[price stability and economic growth]]. It feeds into wage dynamics, inflation expectations, and the output gap. The BoJ\'s reaction function links labor market tightness to wage pressures and, in turn, inflation persistence.\n\n' +
      'Current context: Unemployment at 2.6%, low by international standards, with persistent inflation suggests a [[tight labor market]], supporting wage growth and inflation persistence. The BoJ raised the Policy Rate to 0.75% in December 2025, citing persistent inflation above target, with low unemployment supporting the case for normalization.\n\n' +
      'The BoJ\'s forward guidance and rate decisions depend on the [[unemployment-inflation-wage nexus]]. If unemployment stays low while inflation remains above target, the case for normalization strengthens. If unemployment rises while inflation moderates, the focus shifts to growth support. The current environment—low unemployment, persistent inflation, modest growth—supports continued normalization.\n\n' +
      '[[Political & Structural Overlay]]\n\n' +
      'Political leaders acknowledge the importance of maintaining low unemployment, but [[demographic challenges and economic uncertainties limit policy options]]. The record-high employment, particularly among women and seniors, reflects structural shifts in labor supply.\n\n' +
      'Fiscal policy: Government spending and tax policy affect labor market conditions through demand channels. [[Fiscal support can reduce unemployment]] but is constrained by fiscal rules. The government has implemented measures aimed at supporting labor market participation.\n\n' +
      'Structural factors: Japan\'s [[aging population]] affects labor supply and demand dynamics, while [[increasing labor force participation among women and seniors]] affects labor supply. [[Sectoral shifts in employment]] (e.g., information and communications up, manufacturing down) affect labor market dynamics. [[Productivity challenges]] affect growth potential and labor market dynamics.\n\n' +
      'The distinction between political narrative and policy reality is important: public statements emphasize employment support and growth, but [[actual policy responses are constrained by fiscal rules, demographic challenges, and structural factors]]. The stability in unemployment reflects underlying economic shifts rather than policy choices.',
    traderImplications:
      '[[What Traders Should Monitor Next]]\n\n' +
      'High-impact drivers for unemployment and policy repricing:\n\n' +
      '• [[Monthly Statistics Bureau unemployment releases]] (typically around the end of the following month)\n\n' +
      '• [[Employment trends]] (affects labor supply and economic activity)\n\n' +
      '• [[Labor force participation]] (affects labor supply and potential growth)\n\n' +
      '• [[Jobs-to-applicants ratio]] (affects labor market tightness and wage pressures)\n\n' +
      '• [[Wage growth trends]] (unemployment-wage nexus is critical for BoJ policy)\n\n' +
      '• [[BoJ communications on labor market conditions]] and their implications for policy\n\n' +
      '[[Thresholds & Inflection Points]]\n\n' +
      'A move above [[3.0%]] would signal deterioration and likely increase easing expectations. A move below [[2.0%]] would suggest further tightening and could support more aggressive normalization. The 2.6% level appears to be a near-term equilibrium, with significant deviations likely to shift market narratives.\n\n' +
      '[[Signals That Could Change the Narrative]]\n\n' +
      'Unexpected shifts in unemployment, especially if accompanied by changes in wage growth, inflation, or GDP, could alter BoJ policy expectations. Changes in employment trends, affecting labor supply and demand, could influence policy trade-offs. Changes in labor force participation, affecting labor supply and potential growth, could provide early signals of labor market shifts.\n\n' +
      '[[FXSentinel Usage]]\n\n' +
      'Within FXSentinel, the Japan Unemployment Rate functions best as:\n\n' +
      '• [[BoJ policy expectation driver]]\n\n' +
      '• [[JPY bias validator]] (via wage-inflation-policy nexus)\n\n' +
      '• [[Growth momentum signal]]\n\n' +
      '• [[Volatility trigger around data releases]]',
  },
  // JPY Current Account
  'trade-balance-JPY': {
    overview:
      'The [[Japan Current Account Balance]] measures the net flow of goods, services, primary income (investment income, compensation of employees), and secondary income (transfers, remittances) between Japan and the rest of the world over a given period. Published monthly by the [[Ministry of Finance]] and compiled by the Bank of Japan, it reflects Japan\'s external economic position and competitiveness.\n\n' +
      'A surplus indicates Japan is a [[net lender to the rest of the world]], while a deficit suggests it is a [[net borrower]]. The current account is part of the balance of payments and reflects trade competitiveness, savings-investment dynamics, and capital flow drivers.\n\n' +
      'For traders, the current account influences JPY valuation through [[capital flows]], reflects [[export competitiveness]], signals [[structural imbalances]], and affects [[BoJ policy considerations]]. A sustained surplus supports JPY via capital inflows, while a narrowing surplus or deficit can pressure JPY and signal economic challenges.\n\n' +
      'Markets focus less on absolute current account levels and more on [[trend direction, component breakdowns, and the interplay with growth, inflation, and monetary policy expectations]].',
    measurement:
      'The [[Ministry of Finance]] compiles current account data using standardized balance of payments methodology aligned with [[International Monetary Fund (IMF) guidelines]].\n\n' +
      'The current account consists of four main components:\n\n' +
      '• [[Goods balance]]: Exports minus imports of physical goods\n\n' +
      '• [[Services balance]]: Exports minus imports of services (tourism, financial services, transportation)\n\n' +
      '• [[Primary income]]: Investment income (dividends, interest) and compensation of employees from cross-border activities\n\n' +
      '• [[Secondary income]]: Current transfers, remittances, and other unilateral transfers\n\n' +
      'Data is published monthly, typically with a [[lag of approximately six weeks]] after the reference month. Quarterly data provides more detailed breakdowns, including geographic patterns and component analysis. Frequency: Monthly (with quarterly detailed breakdowns). Unit: Billions of yen (¥), also expressed as percentage of GDP.',
    impact:
      'Current account readings have [[profound implications]] for JPY markets through multiple transmission channels:\n\n' +
      '[[Sustained Surplus]]\n\n' +
      '• [[Supports JPY strength]] via capital inflows and demand for Japanese assets\n\n' +
      '• [[Reflects export competitiveness]] and structural economic strength\n\n' +
      '• [[Signals net lending position]], supporting currency valuation\n\n' +
      '• [[Reduces external vulnerability]], supporting risk sentiment\n\n' +
      '[[Narrowing Surplus or Deficit]]\n\n' +
      '• [[Reduces JPY support]] via weaker capital flows\n\n' +
      '• [[Signals competitiveness challenges]] or structural shifts\n\n' +
      '• [[Increases external vulnerability]], potentially weighing on JPY\n\n' +
      '• [[May affect BoJ policy considerations]] if combined with growth concerns\n\n' +
      '[[Market Dynamics]]\n\n' +
      'JPY crosses remain sensitive to current account trends, with [[sustained surpluses supporting JPY]] through capital flow dynamics, while [[narrowing surpluses or deficits can pressure JPY]] via reduced capital inflows. Markets focus on [[trend direction and component breakdowns]], with shifts in goods, services, or primary income providing signals about competitiveness and structural position. The interplay between current account, growth, inflation, and BoJ policy is crucial for JPY valuation.',
    context:
      '[[Current Reading & Trend (Late 2025)]]\n\n' +
      'As of the latest available data, Japan recorded a current account surplus of [[¥4.06 trillion in February 2025]], a 48.4% increase from the previous year and the highest for a single month since 1985. This was largely due to a [[shift in the trade balance to a surplus]], with exports rising by 10.4% and imports decreasing by 1.9%.\n\n' +
      'Recent trend: The current account has shown volatility, with February 2025 at ¥4.06 trillion surplus (48.4% increase year-on-year, highest monthly surplus since 1985), January 2025 at ¥257.6 billion deficit (first deficit in two years, driven by weak yen and increased imports), and September 2025 at ¥4,483.3 billion surplus (record high, up from ¥1,537.4 billion a year earlier).\n\n' +
      'Fiscal Year 2024: Japan achieved a [[record-high current account surplus of ¥30.4 trillion]], the largest since comparable data became available in 1985. This was primarily driven by a substantial rise in [[primary income, which reached a surplus of ¥41.7 trillion]], an 11.7% increase from the previous year.\n\n' +
      'The trend shows a [[strong surplus driven by primary income]], but with volatility in monthly data reflecting trade balance fluctuations and currency dynamics.\n\n' +
      '[[Institutional & Bank Commentary]]\n\n' +
      'Major financial institutions view the record-high surplus as reflecting Japan\'s [[strong position in international investment income]], but note challenges in the goods and services balance. The primary income surplus of ¥41.7 trillion in fiscal 2024, driven by overseas investments and a weaker yen, underscores Japan\'s role as a net creditor nation.\n\n' +
      'Consensus themes among institutions:\n\n' +
      '• [[The current account surplus remains structurally positive]], driven by primary income\n\n' +
      '• [[The goods trade balance has been in deficit]] for multiple consecutive years\n\n' +
      '• [[The services balance shows mixed performance]], with travel surplus offsetting digital sector deficits\n\n' +
      '• [[The weaker yen has amplified returns]] from foreign investments\n\n' +
      'Projections indicate Japan\'s current account surplus will [[continue to grow, reaching approximately $7.643 trillion by 2030]], though the current account surplus as a percentage of GDP is expected to decrease from 4.7% in 2024 to around 3.3% by 2027.\n\n' +
      '[[Central Bank & Policy Context]]\n\n' +
      'The Bank of Japan monitors the current account as part of its [[assessment of external stability and competitiveness]]. While not a direct policy target, it informs policy considerations through its relationship with growth, inflation, and financial stability.\n\n' +
      'Current context: The record-high surplus of ¥30.4 trillion in fiscal 2024 reflects Japan\'s [[strong position in international investment income]], supporting JPY via capital flows. However, the persistent goods trade deficit and services balance challenges indicate structural shifts in Japan\'s external position.\n\n' +
      'The BoJ\'s reaction function considers the current account alongside inflation, growth, and financial conditions. A strong surplus alone is unlikely to drive policy, but [[combined with other factors]], it can influence the policy stance.\n\n' +
      '[[Political & Structural Overlay]]\n\n' +
      'Trade tensions, particularly with the United States, affect the current account through [[tariffs, supply chain shifts, and export competitiveness]]. The goods trade deficit reflects import dependency and trade structure, while the services balance shows mixed performance.\n\n' +
      'Energy dynamics: Energy import costs affect the goods balance, though recent normalization has reduced pressure. [[Energy security and diversification efforts]] may reshape trade patterns over time.\n\n' +
      'Structural factors: Japan\'s [[export-oriented model]] drives goods exports, but imports have also increased. [[Primary income from overseas investments]] drives the overall surplus. [[Services competitiveness shows mixed performance]], with travel surplus offsetting digital deficits.\n\n' +
      'The distinction between political narrative and policy reality is important: public statements emphasize trade competitiveness and external strength, but [[actual policy responses are constrained by fiscal rules, trade agreements, and structural factors]]. The record-high surplus reflects underlying economic shifts rather than policy choices.',
    traderImplications:
      '[[What Traders Should Monitor Next]]\n\n' +
      'High-impact drivers for current account and JPY repricing:\n\n' +
      '• [[Monthly Ministry of Finance balance of payments releases]] (typically around six weeks after reference month)\n\n' +
      '• [[Quarterly detailed breakdowns]] with component and geographic analysis\n\n' +
      '• [[Primary income trends]] (investment returns and compensation flows)\n\n' +
      '• [[Goods balance trends]] (export competitiveness and import dynamics)\n\n' +
      '• [[Services balance trends]] (services trade competitiveness, especially travel)\n\n' +
      '• [[Currency dynamics]] (especially yen strength or weakness affecting returns)\n\n' +
      '• [[Energy price volatility]] affecting goods balance\n\n' +
      '[[Thresholds & Inflection Points]]\n\n' +
      'A move toward [[deficit (negative current account)]] would signal deterioration and likely pressure JPY. A return to [[above ¥5 trillion monthly surplus]] would signal improvement and support JPY. The current level appears to be volatile, with significant deviations likely to shift market narratives.\n\n' +
      '[[Signals That Could Change the Narrative]]\n\n' +
      'Unexpected shifts in the goods or services balance, especially if driven by trade tensions or competitiveness changes, could alter JPY dynamics. Continued strength in primary income, suggesting structural shifts in investment returns, would signal changing capital flow patterns. Changes in currency dynamics, especially yen strength or weakness affecting returns, could affect current account trends. Changes in BoJ communication tone, especially around external stability, could affect market positioning.\n\n' +
      '[[FXSentinel Usage]]\n\n' +
      'Within FXSentinel, the Japan Current Account Balance functions best as:\n\n' +
      '• [[JPY structural support indicator]] (via capital flows)\n\n' +
      '• [[Competitiveness gauge]] (goods and services balances)\n\n' +
      '• [[External vulnerability signal]]\n\n' +
      '• [[Component analysis tool]] for understanding underlying dynamics',
  },
  // GBP Wage Growth
  'wage-growth-GBP': {
    overview:
      '[[United Kingdom Wage Growth]] measures the annual percentage change in average weekly earnings for employees. Published monthly by the [[Office for National Statistics (ONS)]], it reflects labor market tightness, inflation persistence, and purchasing power. The Bank of England monitors wage growth closely as a [[key indicator of inflationary pressures]] and a critical input for monetary policy decisions.\n\n' +
      'Wage growth reflects the [[balance between labor supply and demand]], affects [[inflation persistence]] (especially in services), and signals the [[output gap]]. It feeds directly into the [[Bank of England\'s reaction function]], influencing expectations for interest rates, forward guidance, and policy stance. In a services-heavy economy, wage growth is particularly important for understanding inflation dynamics.\n\n' +
      'For traders, UK Wage Growth is a [[leading indicator of BoE policy shifts]] and GBP strength. Strong wage growth supports inflation persistence, potentially constraining BoE easing, while moderating wage growth supports disinflation and accommodative policy, typically weighing on GBP.\n\n' +
      'Markets react less to absolute wage growth levels and more to [[surprises versus expectations, trend momentum, and the interplay with inflation and unemployment data]].',
    measurement:
      'The [[Office for National Statistics (ONS)]] calculates wage growth by tracking changes in average weekly earnings for employees across the UK economy. The [[year-over-year (YoY)]] measure compares current earnings to the same period in the previous year.\n\n' +
      'Key components:\n\n' +
      '• [[Regular pay (excluding bonuses)]]: Primary indicator of underlying wage growth\n\n' +
      '• [[Total pay (including bonuses)]]: More volatile but can drive overall trends\n\n' +
      '• [[Public sector vs. private sector]]: Reveals policy-driven vs. market-driven dynamics\n\n' +
      '• [[Real wage growth]]: Affects purchasing power and consumer spending\n\n' +
      '• [[Sectoral breakdowns]]: Reveals underlying inflation dynamics\n\n' +
      'Data is published monthly, typically around the [[middle of the following month]], with revisions possible in subsequent releases. Frequency: Monthly (three-month rolling average). Unit: Percent (%).',
    impact:
      'Wage growth readings have [[profound implications]] for GBP markets through multiple transmission channels:\n\n' +
      '[[Strong Wage Growth]]\n\n' +
      '• [[Supports inflation persistence]], constraining BoE easing\n\n' +
      '• [[Supports GBP strength]] via higher real rate expectations\n\n' +
      '• [[Pressures equities]] as markets price in tighter policy\n\n' +
      '• [[Increases cost pressures]], affecting profit margins\n\n' +
      '[[Moderating Wage Growth]]\n\n' +
      '• [[Supports disinflation]], allowing for more accommodative policy\n\n' +
      '• [[May weaken GBP]] via increased easing expectations\n\n' +
      '• [[Supports risk assets and bonds]] as policy pressure eases\n\n' +
      '• [[Reduces cost pressures]], supporting profit margins\n\n' +
      '[[Market Dynamics]]\n\n' +
      'GBP crosses remain sensitive to wage growth surprises, with [[above-expectation readings tending to support GBP]] via higher rate expectations, while [[below-expectation readings weaken GBP]] through dovish repricing. The interplay between wage growth, inflation, and unemployment is crucial for BoE policy anticipation. Markets focus on [[expectations versus outcomes]], with significant deviations from consensus driving immediate volatility.',
    context:
      '[[Current Wage Growth Trend (Late 2025)]]\n\n' +
      'As of the three months to October 2025, regular pay (excluding bonuses) increased by [[4.6% year-over-year]], down from 4.7% in the previous quarter. This marks the [[lowest growth rate in over three years]] and represents a continued deceleration from higher levels.\n\n' +
      'Recent trend: Wage growth has been moderating, with the three months to October 2025 at 4.6% (down from 4.7% in the previous quarter), the three months to March 2025 at 5.6% (down from 5.9% in December 2024), and December 2024 at 5.9% (driven by robust private sector performance).\n\n' +
      'Sectoral variations: [[Public sector wages grew by 7.6%]] in the three months to October 2025, while [[private sector wages grew by 3.9%]]. Manufacturing wages rose by 6% in the three months to October 2025, contributing to overall private sector wage growth of 5.4%.\n\n' +
      'Real wage growth: When adjusted for inflation, [[real regular pay increased by approximately 0.5%]] in the three months to October 2025, indicating that wage increases are slightly outpacing inflation. In April 2025, median weekly earnings for full-time employees increased by 1.1% in real terms compared to the previous year.\n\n' +
      'The trend shows [[moderating wage growth]], reflecting a cooling labor market and reduced hiring pressure, but wage growth remains above historical averages, supporting inflation persistence.\n\n' +
      '[[Institutional & Bank Commentary]]\n\n' +
      'Major financial institutions view the moderation to 4.6% as a sign of [[labor market cooling]], but note that wage growth remains elevated relative to historical standards and inflation targets. The deceleration from 5.9% in December 2024 to 4.6% in October 2025 reflects reduced hiring pressure and economic slowdown.\n\n' +
      'Consensus themes among institutions:\n\n' +
      '• [[Wage growth is moderating]] but remains elevated relative to historical standards\n\n' +
      '• [[Public sector wage growth is outpacing]] private sector growth\n\n' +
      '• [[Real wage growth is positive but modest]], with purchasing power improving slowly\n\n' +
      '• [[The moderation in wage growth supports]] the case for continued rate cuts\n\n' +
      'International comparison: The UK\'s [[real salary growth in 2025 has lagged behind many European counterparts]]. The ECA International\'s Salary Trends Report indicates a real salary increase of just 0.4% in the UK, placing it 21st out of 25 European countries.\n\n' +
      '[[Central Bank & Policy Context]]\n\n' +
      'The Bank of England monitors wage growth as a [[key indicator of inflationary pressures]] and a critical input for monetary policy decisions. The MPC sets the Bank Rate based on wage growth, inflation, growth momentum, and labor market conditions.\n\n' +
      'Current context: Wage growth at 4.6% in the three months to October 2025, down from 4.7% in the previous quarter, supports the BoE\'s shift toward easing, but wage growth remains [[elevated relative to the 2% inflation target]], limiting aggressive easing. The BoE cut the Bank Rate to 3.75% in December 2025, citing labor market cooling and easing inflation, but [[persistent wage growth remains a concern]] for inflation persistence.\n\n' +
      'The BoE\'s reaction function weighs [[wage growth persistence, inflation dynamics, growth momentum, and labor market conditions]]. Current levels support continued easing, but the pace depends on incoming data, especially wage growth and services inflation. The BoE emphasizes [[data dependence]], with no pre-committed rate path, and remains ready to adjust policy based on incoming information.\n\n' +
      '[[Political & Structural Overlay]]\n\n' +
      'Fiscal policy: Government spending and tax policy affect wage growth through demand channels and labor market conditions. The [[introduction of a £25 billion increase in employers\' national insurance contributions]] and a 6.7% rise in the minimum wage in April 2025 have influenced wage dynamics, with concerns about potential job cuts and increased unemployment rates.\n\n' +
      'Brexit and trade: Trade relationships and supply chain shifts affect labor market conditions and wage growth. [[Trade tensions and uncertainties]] can affect business investment and hiring, influencing wage dynamics.\n\n' +
      'Structural factors: The UK\'s [[services-heavy economy]] affects wage growth dynamics and rate transmission, while [[public sector wage growth is outpacing private sector growth]], reflecting policy-driven adjustments. [[Regional divergences]] in wage growth can affect policy trade-offs. [[Productivity challenges]] affect wage growth potential and inflation dynamics.\n\n' +
      'The distinction between political narrative and policy reality is important: public statements emphasize wage growth support and purchasing power, but [[actual policy responses are constrained by fiscal rules, trade agreements, and structural factors]]. The moderation in wage growth reflects underlying economic shifts rather than policy choices.',
    traderImplications:
      '[[What Traders Should Monitor Next]]\n\n' +
      'High-impact wage growth signals include:\n\n' +
      '• [[Monthly ONS wage growth releases]] (typically around the middle of the following month)\n\n' +
      '• [[Public sector vs. private sector wage growth]] (reveals policy-driven vs. market-driven dynamics)\n\n' +
      '• [[Real wage growth trends]] (affects purchasing power and consumer spending)\n\n' +
      '• [[Sectoral wage growth breakdowns]] (reveals underlying inflation dynamics)\n\n' +
      '• [[Regular pay vs. total pay]] (underlying vs. volatile components)\n\n' +
      '• [[BoE communications on wage growth]] and their implications for policy\n\n' +
      '[[Thresholds & Inflection Points]]\n\n' +
      'A move below [[4.0%]] would signal faster moderation and likely support GBP via reduced inflation expectations. A move above [[5.0%]] would signal persistent wage growth and likely pressure GBP via increased easing expectations. The 4.6% level appears to be a near-term equilibrium, with significant deviations likely to shift market narratives.\n\n' +
      '[[Signals That Could Change the Narrative]]\n\n' +
      'Unexpected shifts in wage growth, especially if driven by services or public sector, could alter Bank Rate expectations. Changes in public sector vs. private sector wage growth, affecting overall dynamics, could influence rate decisions. Changes in real wage growth, affecting purchasing power and consumer spending, could shift market expectations. Changes in BoE communication tone, especially around forward guidance, could affect market positioning.\n\n' +
      '[[FXSentinel Usage]]\n\n' +
      'Within FXSentinel, UK Wage Growth functions best as:\n\n' +
      '• [[BoE policy expectation driver]] (via inflation persistence signals)\n\n' +
      '• [[GBP bias validator]] (via policy constraint assessment)\n\n' +
      '• [[Real-yield and bond signal]]\n\n' +
      '• [[Volatility trigger around data releases]]',
  },
  // GBP Inflation
  'inflation-GBP': {
    overview:
      'The [[United Kingdom Consumer Price Index (CPI)]] measures the annual percentage change in prices for a basket of goods and services purchased by consumers. Published monthly by the [[Office for National Statistics (ONS)]], it is the [[Bank of England\'s primary inflation target]] (2%) and directly shapes monetary policy expectations, GBP valuation, and cross-asset risk sentiment.\n\n' +
      'The CPI reflects the [[cost of living and purchasing power]] of the pound, with components including food, energy, housing, and services. The Bank of England uses CPI to assess price stability and guide monetary policy decisions, making it a critical input for interest rate expectations.\n\n' +
      'For traders, CPI is a [[leading driver of BoE policy expectations]], GBP valuation, and cross-asset risk sentiment. Markets react less to absolute inflation levels and more to [[surprises versus expectations and trend momentum]], making CPI a high-signal indicator for policy repricing.\n\n' +
      'The CPI is published monthly, typically around the [[middle of the following month]], with detailed breakdowns by component and category. The data is subject to revisions, and traders should monitor both initial releases and revisions for policy signals.',
    measurement:
      'The [[Office for National Statistics (ONS)]] calculates CPI by tracking price changes for a representative basket of goods and services across UK consumers. The [[year-over-year (YoY)]] measure compares current prices to the same month in the previous year.\n\n' +
      'Key components:\n\n' +
      '• [[Headline CPI]]: Includes all items, including volatile food and energy components\n\n' +
      '• [[Core CPI]]: Excludes food, energy, alcohol, and tobacco to reveal underlying inflation trends\n\n' +
      '• [[Services inflation]]: Often sticky and affects core inflation persistence\n\n' +
      '• [[Goods inflation]]: More volatile but can drive headline inflation\n\n' +
      '• [[Energy and food prices]]: Affect headline inflation directly and indirectly\n\n' +
      'Data is released monthly, typically around the [[middle of the following month]], with revisions possible in subsequent releases. Frequency: Monthly. Unit: Percent (%).',
    impact:
      'CPI readings have [[profound implications]] for GBP markets through multiple transmission channels:\n\n' +
      '[[Above-Expectation Inflation]]\n\n' +
      '• [[Reinforces hawkish bias]] and supports GBP via higher rate expectations\n\n' +
      '• [[Pressures equities and bonds]] as markets price in tighter policy\n\n' +
      '• [[Increases inflation expectations]], potentially steepening yield curves\n\n' +
      '[[Below-Expectation Inflation]]\n\n' +
      '• [[Strengthens easing expectations]] and may weaken GBP\n\n' +
      '• [[Supports risk assets and bonds]] as policy pressure eases\n\n' +
      '• [[Relieves pressure on policymakers]], potentially supporting risk sentiment\n\n' +
      '[[Market Dynamics]]\n\n' +
      'CPI remains the [[primary constraint on BoE easing]]. Cooling inflation supports additional rate cuts, while sticky core components cap the pace and depth of easing. CPI surprises quickly [[reprice Bank Rate expectations and short-dated yields]]. For markets, CPI prints act as [[confirmation or invalidation events]] for existing rate expectations. The November 2025 decline to 3.2% led to a 0.2% dip in GBP/USD, reflecting dovish repricing.',
    context:
      '[[Current Inflation Trend (Late 2025)]]\n\n' +
      'As of November 2025, UK CPI inflation stood at [[3.2% year-over-year]], down from 3.6% in October 2025. This marks the [[second consecutive month of decline]] and the lowest in five months, indicating progress toward the Bank of England\'s 2% target.\n\n' +
      'The monthly CPI rate for November was [[-0.2%]], indicating a slight month-on-month decrease. The decline was driven by [[lower prices in food and non-alcoholic beverages, clothing and footwear, and alcohol and tobacco]], contributing to the overall disinflationary trend.\n\n' +
      'Recent trend: Inflation has been declining from higher levels, with October 2025 at 3.6% (down from 3.8% in September) and September 2025 at 3.8%. The trend shows [[disinflationary momentum]], moving toward the BoE\'s 2% target, but inflation remains above target, limiting aggressive policy easing.\n\n' +
      '[[Institutional & Bank Commentary]]\n\n' +
      'Major financial institutions view the decline as progress but note that the UK remains among the highest-inflation advanced economies. The [[International Monetary Fund (IMF) projects UK average inflation at 3.4% in 2025 and 2.5% in 2026]], the highest among advanced economies.\n\n' +
      'Consensus themes among institutions:\n\n' +
      '• [[Inflation is moderating]] but remains above target\n\n' +
      '• [[The UK faces persistent inflation pressures]] relative to peers\n\n' +
      '• [[Services and core components remain sticky]], affecting inflation persistence\n\n' +
      '• [[Wage growth continues to support]] inflation persistence\n\n' +
      'Forecasts vary, with the [[Office for Budget Responsibility (OBR) forecasting CPI inflation to average 4.3% in 2025 and 3.7% in 2026]], gradually declining to 2.3% by 2030. Markets expect inflation to [[approach the 2% target by late 2026 or early 2027]], aided by disinflationary measures introduced in the Autumn Budget.\n\n' +
      '[[Central Bank & Policy Context]]\n\n' +
      'The Bank of England targets [[2% CPI inflation]] as its primary monetary policy objective. The MPC sets the Bank Rate based on inflation, wage growth, growth momentum, and labor market conditions.\n\n' +
      'Current context: CPI at 3.2% in November 2025, down from 3.6% in October, supports the BoE\'s shift toward easing. The BoE cut the Bank Rate to 3.75% in December 2025, citing [[established disinflation trends]]. However, inflation above target limits aggressive easing.\n\n' +
      'The BoE\'s reaction function weighs [[inflation persistence, wage growth, growth momentum, and labor market conditions]]. Current levels support continued easing, but the pace depends on incoming data. The BoE emphasizes [[data dependence]], with no pre-committed rate path, and remains ready to adjust policy based on incoming information.\n\n' +
      '[[Political & Structural Overlay]]\n\n' +
      'Fiscal policy: Government spending and tax policy affect inflation through demand and supply channels. The [[Autumn Budget included disinflationary measures]] expected to help inflation approach the 2% target by late 2026 or early 2027.\n\n' +
      'Brexit and trade: Trade relationships and supply chain shifts affect import costs and inflation. [[Trade tensions and tariffs]] can affect prices and competitiveness, while trade deals can support growth but may affect inflation.\n\n' +
      'Structural factors: The UK\'s [[services-heavy economy]] affects inflation dynamics and rate transmission, while [[housing market sensitivity]] to rates affects consumption and growth. [[Productivity challenges]] affect growth potential and inflation dynamics.\n\n' +
      'The distinction between political narrative and policy reality is important: public statements emphasize inflation control and growth support, but [[actual policy is constrained by the inflation target and economic conditions]]. The BoE maintains operational independence, but political pressure can affect communication and expectations.',
    traderImplications:
      '[[What Traders Should Monitor Next]]\n\n' +
      'High-impact inflation signals include:\n\n' +
      '• [[Monthly CPI & Core CPI prints]] (typically around the middle of the following month)\n\n' +
      '• [[Services inflation trends]] (often sticky and affects core inflation persistence)\n\n' +
      '• [[Wage growth data]] (affects inflation persistence and policy trade-offs)\n\n' +
      '• [[Component breakdowns]] (food, energy, housing, services)\n\n' +
      '• [[Inflation expectations surveys]]\n\n' +
      '• [[BoE communications on inflation]] and their implications for policy\n\n' +
      '[[Thresholds & Inflection Points]]\n\n' +
      'A move below [[3.0%]] would signal faster disinflation and likely support GBP via reduced easing pressure. A move above [[3.5%]] would signal persistent inflation and likely pressure GBP via continued easing expectations. The 3.2% level appears to be a near-term equilibrium, with significant deviations likely to shift market narratives.\n\n' +
      '[[Signals That Could Change the Narrative]]\n\n' +
      'Unexpected shifts in inflation, especially if driven by services or core components, could alter Bank Rate expectations. Changes in wage growth, affecting inflation persistence and policy trade-offs, could influence rate decisions. Energy price volatility, affecting headline inflation and consumer sentiment, could drive inflation volatility. Changes in BoE communication tone, especially around forward guidance, could shift market expectations.\n\n' +
      '[[FXSentinel Usage]]\n\n' +
      'Within FXSentinel, UK CPI (YoY) functions best as:\n\n' +
      '• [[Rate-expectation driver]]\n\n' +
      '• [[GBP bias validator]]\n\n' +
      '• [[Real-yield and bond signal]]\n\n' +
      '• [[Volatility trigger around data releases]]',
  },
  // GBP Core Inflation
  'core-inflation-YoY-GBP': {
    overview:
      'The [[United Kingdom Core Consumer Price Index (CPI)]] measures the annual percentage change in consumer prices excluding volatile items such as energy, food, alcohol, and tobacco. Published monthly by the [[Office for National Statistics (ONS)]], Core CPI provides a [[clearer view of underlying inflation trends]] by filtering out short-term price fluctuations.\n\n' +
      'Core CPI is the [[Bank of England\'s preferred gauge]] for assessing inflation persistence and policy effectiveness, as it reflects domestic price pressures that monetary policy can influence. The BoE monitors Core CPI closely when setting the Bank Rate, making it a critical input for interest rate expectations.\n\n' +
      'For traders, Core CPI is a [[leading driver of BoE policy expectations]], GBP valuation, and cross-asset risk sentiment. Markets often react [[more strongly to core inflation surprises than headline CPI]], especially during policy transitions, as core inflation signals underlying inflation persistence.\n\n' +
      'The Core CPI is published monthly, typically around the [[middle of the following month]], with detailed breakdowns by component (goods, services) and category. The data is subject to revisions, and traders should monitor both initial releases and revisions for policy signals.',
    measurement:
      'The [[Office for National Statistics (ONS)]] calculates Core CPI by tracking price changes for a representative basket of goods and services, [[excluding energy, food, alcohol, and tobacco]]. The [[year-over-year (YoY)]] measure compares current prices to the same month in the previous year.\n\n' +
      'Key components:\n\n' +
      '• [[Services inflation]]: Often sticky and affects core inflation persistence (currently 4.4%)\n\n' +
      '• [[Goods inflation]]: More volatile but can drive core inflation trends (currently 2.1%)\n\n' +
      '• [[The gap between services and goods inflation]]: Signals underlying inflation dynamics\n\n' +
      '• [[Monthly momentum]]: Provides early signals of trend changes\n\n' +
      'Data is released monthly, typically around the [[middle of the following month]], with revisions possible in subsequent releases. Frequency: Monthly. Unit: Percent (%).',
    impact:
      'Core CPI readings have [[profound implications]] for GBP markets through multiple transmission channels:\n\n' +
      '[[Above-Expectation Core Inflation]]\n\n' +
      '• [[Reinforces hawkish bias]] and supports GBP via higher rate expectations\n\n' +
      '• [[Pressures equities and bonds]] as markets price in tighter policy\n\n' +
      '• [[Signals inflation persistence]], potentially limiting policy easing\n\n' +
      '[[Below-Expectation Core Inflation]]\n\n' +
      '• [[Strengthens easing expectations]] and may weaken GBP\n\n' +
      '• [[Supports risk assets and bonds]] as policy pressure eases\n\n' +
      '• [[Relieves pressure on policymakers]], potentially supporting risk sentiment\n\n' +
      '[[Market Dynamics]]\n\n' +
      'Core CPI remains a [[key constraint on BoE easing]]. Cooling core inflation supports additional rate cuts, while sticky core components, particularly services inflation, cap the pace and depth of easing. Core inflation surprises often have a [[larger impact than headline CPI surprises]], as they signal underlying inflation persistence. Markets focus on [[expectations versus outcomes]], with significant deviations from consensus driving immediate volatility.',
    context:
      '[[Current Core Inflation Trend (Late 2025)]]\n\n' +
      'As of November 2025, UK Core CPI inflation stood at [[3.2% year-over-year]], down from 3.4% in October 2025. This marks the [[lowest level since December 2024]] and represents a continued decline from higher levels.\n\n' +
      'Recent trend: Core inflation has been declining, with October 2025 at 3.4% (down from 3.5% in September) and September 2025 at 3.5%. The November decline was [[broad-based]], with goods inflation decreasing to 2.1% from 2.6% in October, while services inflation edged down to 4.4% from 4.5%.\n\n' +
      'On a monthly basis, core consumer prices fell by [[-0.2% in November]], reversing October\'s 0.3% rise and posting the first decline since January. The trend shows [[disinflationary momentum]], but core inflation remains above the BoE\'s 2% target, with services inflation particularly sticky, limiting aggressive policy easing.\n\n' +
      '[[Institutional & Bank Commentary]]\n\n' +
      'Major financial institutions view the decline as progress but note that UK core inflation remains [[among the highest in the G7]]. In November 2025, UK core inflation was 3.2%, compared to 2.4% in Canada, 1.4% in France, 2.6% in Germany, 1.7% in Italy, and 1.5% in Japan.\n\n' +
      'Consensus themes among institutions:\n\n' +
      '• [[Core inflation is moderating]] but remains elevated relative to peers\n\n' +
      '• [[Services inflation remains sticky]], affecting overall persistence\n\n' +
      '• [[Goods inflation has eased more quickly]] than services\n\n' +
      '• [[The UK faces persistent core inflation pressures]] relative to other advanced economies\n\n' +
      'Analysts anticipate the [[disinflationary trend will continue into 2026]], with core inflation expected to approach the BoE\'s 2% target by late 2026 or early 2027. The pace of decline depends on services inflation and wage growth dynamics.\n\n' +
      '[[Central Bank & Policy Context]]\n\n' +
      'The Bank of England monitors Core CPI as the [[primary gauge of underlying inflation persistence]]. The MPC sets the Bank Rate based on core inflation, wage growth, growth momentum, and labor market conditions.\n\n' +
      'Current context: Core CPI at 3.2% in November 2025, down from 3.4% in October, supports the BoE\'s shift toward easing. The BoE cut the Bank Rate to 3.75% in December 2025, citing [[established disinflation trends]]. However, core inflation above the 2% target, particularly [[sticky services inflation at 4.4%]], limits aggressive easing.\n\n' +
      'The BoE\'s reaction function weighs [[core inflation persistence, wage growth, growth momentum, and labor market conditions]]. Current levels support continued easing, but the pace depends on incoming data, especially services inflation and wage growth. The BoE emphasizes [[data dependence]], with no pre-committed rate path, and remains ready to adjust policy based on incoming information.\n\n' +
      '[[Political & Structural Overlay]]\n\n' +
      'Fiscal policy: Government spending and tax policy affect core inflation through demand and supply channels. The [[Autumn Budget included disinflationary measures]] expected to help inflation approach the 2% target by late 2026 or early 2027.\n\n' +
      'Brexit and trade: Trade relationships and supply chain shifts affect import costs and core inflation. [[Trade tensions and tariffs]] can affect prices and competitiveness, while trade deals can support growth but may affect inflation.\n\n' +
      'Structural factors: The UK\'s [[services-heavy economy]] affects core inflation dynamics and rate transmission, while [[housing market sensitivity]] to rates affects consumption and growth. [[Productivity challenges]] affect growth potential and inflation dynamics.\n\n' +
      'Wage dynamics: [[Wage growth affects core inflation persistence]], especially in services. Labor market conditions affect wage pressures and inflation dynamics. The [[interplay between wages and core inflation]] is crucial for policy.\n\n' +
      'The distinction between political narrative and policy reality is important: public statements emphasize inflation control and growth support, but [[actual policy is constrained by the inflation target and economic conditions]]. The BoE maintains operational independence, but political pressure can affect communication and expectations.',
    traderImplications:
      '[[What Traders Should Monitor Next]]\n\n' +
      'High-impact core inflation signals include:\n\n' +
      '• [[Monthly Core CPI prints]] (typically around the middle of the following month)\n\n' +
      '• [[Services inflation trends]] (often sticky and affects core inflation persistence)\n\n' +
      '• [[Goods inflation trends]] (more volatile but can drive core inflation)\n\n' +
      '• [[Wage growth data]] (affects core inflation persistence and policy trade-offs)\n\n' +
      '• [[The gap between services and goods inflation]] (signals underlying dynamics)\n\n' +
      '• [[BoE communications on core inflation]] and their implications for policy\n\n' +
      '[[Thresholds & Inflection Points]]\n\n' +
      'A move below [[3.0%]] would signal faster disinflation and likely support GBP via reduced easing pressure. A move above [[3.5%]] would signal persistent core inflation and likely pressure GBP via continued easing expectations. The 3.2% level appears to be a near-term equilibrium, with significant deviations likely to shift market narratives.\n\n' +
      '[[Signals That Could Change the Narrative]]\n\n' +
      'Unexpected shifts in core inflation, especially if driven by services or wage growth, could alter Bank Rate expectations. Changes in services inflation, affecting overall core inflation persistence, could influence rate decisions. Changes in wage growth, affecting core inflation dynamics and policy trade-offs, could shift market expectations. Changes in BoE communication tone, especially around forward guidance, could affect market positioning.\n\n' +
      '[[FXSentinel Usage]]\n\n' +
      'Within FXSentinel, UK Core CPI (YoY) functions best as:\n\n' +
      '• [[Rate-expectation driver]] (via inflation persistence signals)\n\n' +
      '• [[GBP bias validator]] (via policy constraint assessment)\n\n' +
      '• [[Real-yield and bond signal]]\n\n' +
      '• [[Volatility trigger around data releases]]',
  },
  // JPY Inflation
  'inflation-JPY': {
    overview:
      'The [[Japan Consumer Price Index (CPI)]] measures the annual percentage change in prices for a basket of goods and services purchased by consumers. Published monthly by the [[Statistics Bureau of Japan]], it is the [[Bank of Japan\'s primary inflation target]] (2%) and directly shapes monetary policy expectations, JPY valuation, and cross-asset risk sentiment.\n\n' +
      'The CPI reflects the [[cost of living and purchasing power]] of the yen, with components including food, energy, housing, and services. The Bank of Japan uses CPI to assess price stability and guide monetary policy decisions, making it a critical input for interest rate expectations.\n\n' +
      'For traders, CPI is a [[leading driver of BoJ policy expectations]], JPY valuation, and cross-asset risk sentiment. Markets react less to absolute inflation levels and more to [[surprises versus expectations and trend momentum]], making CPI a high-signal indicator for policy repricing.\n\n' +
      'The CPI is published monthly, typically around the [[end of the following month]], with detailed breakdowns by component and category. Tokyo Core CPI serves as a [[leading indicator for nationwide trends]], providing early signals of inflation dynamics.',
    measurement:
      'The [[Statistics Bureau of Japan]] calculates CPI by tracking price changes for a representative basket of goods and services across Japanese consumers. The [[year-over-year (YoY)]] measure compares current prices to the same month in the previous year.\n\n' +
      'Key components:\n\n' +
      '• [[Headline CPI]]: Includes all items, including volatile food and energy components\n\n' +
      '• [[Core CPI (excluding fresh food)]]: Primary indicator of underlying inflation trends\n\n' +
      '• [[Services inflation]]: Often sticky and affects core inflation persistence\n\n' +
      '• [[Goods inflation]]: More volatile but can drive headline inflation\n\n' +
      '• [[Energy and food prices]]: Affect headline inflation directly and indirectly\n\n' +
      '• [[Tokyo Core CPI]]: Leading indicator for nationwide trends\n\n' +
      'Data is released monthly, typically around the [[end of the following month]], with revisions possible in subsequent releases. Frequency: Monthly. Unit: Percent (%).',
    impact:
      'CPI readings have [[profound implications]] for JPY markets through multiple transmission channels:\n\n' +
      '[[Above-Expectation Inflation]]\n\n' +
      '• [[Reinforces hawkish bias]] and supports JPY via higher rate expectations\n\n' +
      '• [[Pressures equities and bonds]] as markets price in tighter policy\n\n' +
      '• [[Increases inflation expectations]], potentially steepening yield curves\n\n' +
      '[[Below-Expectation Inflation]]\n\n' +
      '• [[Strengthens easing expectations]] and may weaken JPY\n\n' +
      '• [[Supports risk assets and bonds]] as policy pressure eases\n\n' +
      '• [[Relieves pressure on policymakers]], potentially supporting risk sentiment\n\n' +
      '[[Market Dynamics]]\n\n' +
      'CPI remains a [[key driver of BoJ normalization]]. Higher inflation supports additional rate hikes, while moderating inflation may slow the pace of normalization. CPI surprises quickly [[reprice Policy Rate expectations and short-dated yields]]. For markets, CPI prints act as [[confirmation or invalidation events]] for existing rate expectations. The core CPI at 3.0% in November 2025, above the 2% target, supports the BoJ\'s shift toward normalization.',
    context:
      '[[Current Inflation Trend (Late 2025)]]\n\n' +
      'As of November 2025, Japan\'s CPI stood at [[113.20 points]], up from 112.80 in October. The [[core CPI (excluding fresh food) increased by 3.0% year-over-year]] in November, maintaining the same rate as in October and aligning with market expectations.\n\n' +
      'Recent trend: Inflation has been [[above the BoJ\'s 2% target for over two years]], with core CPI consistently exceeding 2%. The moderation in [[Tokyo Core CPI from 2.8% in November to 2.3% in December]] suggests potential easing of inflationary pressures, but nationwide inflation remains elevated.\n\n' +
      'The trend shows [[sustained inflation above the 2% target]], with core CPI at 3.0% in November 2025, above the 2% target. The moderation in Tokyo Core CPI suggests potential easing, but nationwide inflation remains elevated, supporting continued BoJ normalization.\n\n' +
      '[[Institutional & Bank Commentary]]\n\n' +
      'Major financial institutions view the sustained inflation above the 2% target as supporting continued BoJ normalization, but note risks from global uncertainties and the need for a gradual approach. The core CPI at 3.0% in November 2025, above the 2% target, supports the BoJ\'s shift toward normalization, but the moderation in Tokyo Core CPI suggests potential easing.\n\n' +
      'Consensus themes among institutions:\n\n' +
      '• [[Inflation remains above target]], supporting continued normalization\n\n' +
      '• [[The moderation in Tokyo Core CPI suggests]] potential easing of inflationary pressures\n\n' +
      '• [[Energy price fluctuations affect]] headline inflation dynamics\n\n' +
      '• [[Domestic demand will influence]] the inflation trajectory\n\n' +
      'The BoJ projects that [[inflation will stabilize around its 2% target by early 2026]], with factors such as energy price fluctuations and domestic demand influencing the inflation trajectory.\n\n' +
      '[[Central Bank & Policy Context]]\n\n' +
      'The Bank of Japan targets [[2% CPI inflation]] as its primary monetary policy objective. The Policy Board sets the Policy Rate based on inflation, wage growth, growth momentum, and financial stability.\n\n' +
      'Current context: CPI at 3.0% in November 2025, above the 2% target, supports the BoJ\'s shift toward normalization. The BoJ raised the Policy Rate to 0.75% in December 2025, citing [[persistent inflation above target]]. However, the moderation in Tokyo Core CPI suggests potential easing, which may affect the pace of normalization.\n\n' +
      'The BoJ\'s reaction function weighs [[inflation persistence, wage growth, growth momentum, and financial stability]]. Current levels support continued normalization, but the pace depends on incoming data, especially inflation and wage growth. The BoJ emphasizes [[data dependence]], with no pre-committed rate path, and remains ready to adjust policy based on incoming information.\n\n' +
      '[[Political & Structural Overlay]]\n\n' +
      'Fiscal policy: Government spending and tax policy affect inflation through demand and supply channels. [[Fiscal support can reduce the need]] for monetary accommodation, while fiscal tightening can increase pressure for monetary support.\n\n' +
      'Structural factors: Japan\'s [[aging population]] affects growth potential and inflation dynamics, while the [[export-oriented economy]] affects rate transmission and currency dynamics. [[Productivity challenges]] affect growth potential and inflation dynamics. [[Energy import dependency]] affects headline inflation and consumer sentiment.\n\n' +
      'The distinction between political narrative and policy reality is important: public statements emphasize inflation control and growth support, but [[actual policy is constrained by the inflation target and economic conditions]]. The BoJ maintains operational independence, but political pressure can affect communication and expectations.',
    traderImplications:
      '[[What Traders Should Monitor Next]]\n\n' +
      'High-impact inflation signals include:\n\n' +
      '• [[Monthly CPI & Core CPI prints]] (typically around the end of the following month)\n\n' +
      '• [[Tokyo Core CPI]] (leading indicator for nationwide trends)\n\n' +
      '• [[Services inflation trends]] (often sticky and affects core inflation persistence)\n\n' +
      '• [[Wage growth data]] (affects inflation persistence and policy trade-offs)\n\n' +
      '• [[Component breakdowns]] (food, energy, housing, services)\n\n' +
      '• [[BoJ communications on inflation]] and their implications for policy\n\n' +
      '[[Thresholds & Inflection Points]]\n\n' +
      'A move below [[2.5%]] would signal faster disinflation and likely weigh on JPY via reduced normalization pressure. A move above [[3.5%]] would signal persistent inflation and likely support JPY via increased normalization expectations. The 3.0% level appears to be a near-term equilibrium, with significant deviations likely to shift market narratives.\n\n' +
      '[[Signals That Could Change the Narrative]]\n\n' +
      'Unexpected shifts in inflation, especially if driven by services or core components, could alter Policy Rate expectations. Changes in Tokyo Core CPI, affecting nationwide inflation expectations, could influence rate decisions. Energy price volatility, affecting headline inflation and consumer sentiment, could drive inflation volatility. Changes in BoJ communication tone, especially around forward guidance, could shift market expectations.\n\n' +
      '[[FXSentinel Usage]]\n\n' +
      'Within FXSentinel, Japan CPI (YoY) functions best as:\n\n' +
      '• [[Rate-expectation driver]]\n\n' +
      '• [[JPY bias validator]]\n\n' +
      '• [[Real-yield and bond signal]]\n\n' +
      '• [[Volatility trigger around data releases]]',
  },
  // JPY Core Inflation
  'core-inflation-YoY-JPY': {
    overview:
      'The [[Japan Core Consumer Price Index (CPI)]] measures the annual percentage change in consumer prices excluding volatile fresh food. Published monthly by the [[Statistics Bureau of Japan]], Core CPI provides a [[clearer view of underlying inflation trends]] by filtering out temporary food price shocks.\n\n' +
      'Core CPI is the [[Bank of Japan\'s preferred gauge]] for assessing inflation persistence and policy effectiveness, as it reflects domestic price pressures that monetary policy can influence. The BoJ monitors Core CPI closely when setting the Policy Rate, making it a critical input for interest rate expectations.\n\n' +
      'For traders, Core CPI is a [[leading driver of BoJ policy expectations]], JPY valuation, and cross-asset risk sentiment. Markets often react [[more strongly to core inflation surprises than headline CPI]], especially during policy transitions, as core inflation signals underlying inflation persistence.\n\n' +
      'The Core CPI is published monthly, typically around the [[end of the following month]], with detailed breakdowns by component (goods, services) and category. Tokyo Core CPI serves as a [[leading indicator for nationwide trends]], providing early signals of inflation dynamics.',
    measurement:
      'The [[Statistics Bureau of Japan]] calculates Core CPI by tracking price changes for a representative basket of goods and services, [[excluding fresh food prices]]. The [[year-over-year (YoY)]] measure compares current prices to the same month in the previous year.\n\n' +
      'Key components:\n\n' +
      '• [[Core-core inflation (excluding fresh food and energy)]]: Reveals underlying inflation trends\n\n' +
      '• [[Services inflation]]: Often sticky and affects core inflation persistence\n\n' +
      '• [[Goods inflation]]: More volatile but can drive core inflation trends\n\n' +
      '• [[The gap between core and core-core inflation]]: Signals energy price effects\n\n' +
      '• [[Tokyo Core CPI]]: Leading indicator for nationwide trends\n\n' +
      'Data is released monthly, typically around the [[end of the following month]], with revisions possible in subsequent releases. Frequency: Monthly. Unit: Percent (%).',
    impact:
      'Core CPI readings have [[profound implications]] for JPY markets through multiple transmission channels:\n\n' +
      '[[Above-Expectation Core Inflation]]\n\n' +
      '• [[Reinforces hawkish bias]] and supports JPY via higher rate expectations\n\n' +
      '• [[Pressures equities and bonds]] as markets price in tighter policy\n\n' +
      '• [[Signals inflation persistence]], potentially limiting policy easing\n\n' +
      '[[Below-Expectation Core Inflation]]\n\n' +
      '• [[Strengthens easing expectations]] and may weaken JPY\n\n' +
      '• [[Supports risk assets and bonds]] as policy pressure eases\n\n' +
      '• [[Relieves pressure on policymakers]], potentially supporting risk sentiment\n\n' +
      '[[Market Dynamics]]\n\n' +
      'Core CPI remains a [[key driver of BoJ normalization]]. Higher core inflation supports additional rate hikes, while moderating core inflation may slow the pace of normalization. Core inflation surprises often have a [[larger impact than headline CPI surprises]], as they signal underlying inflation persistence. Markets focus on [[expectations versus outcomes]], with significant deviations from consensus driving immediate volatility.',
    context:
      '[[Current Core Inflation Trend (Late 2025)]]\n\n' +
      'As of November 2025, Japan\'s Core CPI (excluding fresh food) increased by [[3.0% year-over-year]], maintaining the same rate as in October 2025 and aligning with market expectations. The core CPI reached 112.50 points in November, up from 112.10 in October.\n\n' +
      'Recent trend: Core inflation has been [[above the BoJ\'s 2% target for over two years]], with fluctuations. The trend shows moderation from peaks earlier in 2025 (3.5% in April 2025, highest since January 2023) to current levels (3.0% in November 2025). [[Tokyo Core CPI, a leading indicator, decreased to 2.3% in December 2025]], down from 2.8% in November, marking the lowest figure since February but remaining above the BoJ\'s 2% target.\n\n' +
      'The trend shows [[sustained inflation above the 2% target]], with recent moderation from peaks earlier in 2025. The decline in Tokyo Core CPI suggests potential easing, but nationwide core inflation remains elevated, supporting continued BoJ normalization.\n\n' +
      '[[Institutional & Bank Commentary]]\n\n' +
      'Major financial institutions view the sustained core inflation above the 2% target as supporting continued BoJ normalization, but note the recent moderation suggests potential easing. The core CPI at 3.0% in November 2025, above the 2% target, supports the BoJ\'s shift toward normalization, but the moderation in Tokyo Core CPI suggests potential easing.\n\n' +
      'Consensus themes among institutions:\n\n' +
      '• [[Core inflation remains above target]], supporting continued normalization\n\n' +
      '• [[The moderation in Tokyo Core CPI suggests]] potential easing of inflationary pressures\n\n' +
      '• [[Services and core-core inflation remain concerns]] for persistence\n\n' +
      '• [[Energy price fluctuations affect]] headline inflation but are excluded from core\n\n' +
      'The BoJ projects that [[inflation will stabilize around its 2% target by early 2026]], with factors such as energy price fluctuations and domestic demand influencing the inflation trajectory.\n\n' +
      '[[Central Bank & Policy Context]]\n\n' +
      'The Bank of Japan monitors Core CPI as the [[primary gauge of underlying inflation persistence]]. The Policy Board sets the Policy Rate based on core inflation, wage growth, growth momentum, and financial stability.\n\n' +
      'Current context: Core CPI at 3.0% in November 2025, above the 2% target, supports the BoJ\'s shift toward normalization. The BoJ raised the Policy Rate to 0.75% in December 2025, citing [[persistent inflation above target]]. However, the moderation in Tokyo Core CPI suggests potential easing, which may affect the pace of normalization.\n\n' +
      'The BoJ\'s reaction function weighs [[core inflation persistence, wage growth, growth momentum, and financial stability]]. Current levels support continued normalization, but the pace depends on incoming data, especially core inflation and wage growth. The BoJ emphasizes [[data dependence]], with no pre-committed rate path, and remains ready to adjust policy based on incoming information.\n\n' +
      '[[Political & Structural Overlay]]\n\n' +
      'Fiscal policy: Government spending and tax policy affect core inflation through demand and supply channels. [[Fiscal support can reduce the need]] for monetary accommodation, while fiscal tightening can increase pressure for monetary support.\n\n' +
      'Structural factors: Japan\'s [[aging population]] affects growth potential and inflation dynamics, while the [[export-oriented economy]] affects rate transmission and currency dynamics. [[Productivity challenges]] affect growth potential and inflation dynamics. [[Energy import dependency]] affects headline inflation but is excluded from core.\n\n' +
      'The distinction between political narrative and policy reality is important: public statements emphasize inflation control and growth support, but [[actual policy is constrained by the inflation target and economic conditions]]. The BoJ maintains operational independence, but political pressure can affect communication and expectations.',
    traderImplications:
      '[[What Traders Should Monitor Next]]\n\n' +
      'High-impact core inflation signals include:\n\n' +
      '• [[Monthly Core CPI prints]] (typically around the end of the following month)\n\n' +
      '• [[Tokyo Core CPI]] (leading indicator for nationwide trends)\n\n' +
      '• [[Core-core inflation (excluding fresh food and energy)]] (reveals underlying trends)\n\n' +
      '• [[Services inflation trends]] (often sticky and affects core inflation persistence)\n\n' +
      '• [[Wage growth data]] (affects core inflation persistence and policy trade-offs)\n\n' +
      '• [[BoJ communications on core inflation]] and their implications for policy\n\n' +
      '[[Thresholds & Inflection Points]]\n\n' +
      'A move below [[2.5%]] would signal faster disinflation and likely weigh on JPY via reduced normalization pressure. A move above [[3.5%]] would signal persistent core inflation and likely support JPY via increased normalization expectations. The 3.0% level appears to be a near-term equilibrium, with significant deviations likely to shift market narratives.\n\n' +
      '[[Signals That Could Change the Narrative]]\n\n' +
      'Unexpected shifts in core inflation, especially if driven by services or wage growth, could alter Policy Rate expectations. Changes in Tokyo Core CPI, affecting nationwide inflation expectations, could influence rate decisions. Changes in core-core inflation, affecting underlying dynamics, could shift market expectations. Changes in BoJ communication tone, especially around forward guidance, could affect market positioning.\n\n' +
      '[[FXSentinel Usage]]\n\n' +
      'Within FXSentinel, Japan Core CPI (YoY) functions best as:\n\n' +
      '• [[Rate-expectation driver]] (via inflation persistence signals)\n\n' +
      '• [[JPY bias validator]] (via policy constraint assessment)\n\n' +
      '• [[Real-yield and bond signal]]\n\n' +
      '• [[Volatility trigger around data releases]]',
  },
  'core-inflation-YoY': {
    overview:
      'U.S. Core Inflation measures the underlying trend in consumer prices, excluding [[volatile food and energy components]]. It is one of the [[most closely watched inflation gauges by the Federal Reserve]] and plays a central role in monetary policy decisions, interest rate expectations, and USD pricing.\n\n' +
      'For traders, core inflation is a [[cleaner signal of persistent price pressure]] than headline inflation.\n\n' +
      'Why Core Inflation Matters to Traders:\n\n' +
      '• [[Federal Reserve policy decisions]]\n\n' +
      '• [[Interest rate and yield expectations]]\n\n' +
      '• [[Real yields]], impacting USD and gold\n\n' +
      '• [[Market confidence in sustained disinflation]]\n\n' +
      'Markets often react more strongly to [[core inflation surprises than headline CPI]], especially during late-cycle or easing environments.',
    measurement:
      'The [[Bureau of Labor Statistics (BLS)]] calculates Core CPI by taking the Consumer Price Index and [[excluding food and energy components]]. The year-over-year change is calculated by comparing the current month\'s Core CPI to the same month in the previous year.\n\n' +
      'Key components:\n\n' +
      '• [[Core CPI]]: All items except food and energy, representing approximately 78% of the CPI basket.\n\n' +
      '• [[Food excluded]]: Fresh fruits, vegetables, meat, dairy, and processed foods.\n\n' +
      '• [[Energy excluded]]: Gasoline, electricity, natural gas, and fuel oil.\n\n' +
      '• [[Included items]]: Housing, medical care, transportation services, apparel, education, and other services.\n\n' +
      '[[Core CPI vs Core PCE]]\n\n' +
      'While Core CPI is widely traded, the Federal Reserve places greater emphasis on [[Core PCE inflation]].\n\n' +
      '• [[Core PCE]]: Running closer to 2.8–2.9% YoY\n\n' +
      '• [[Broader coverage and adaptive weighting]] make PCE a more stable policy gauge\n\n' +
      '• [[Persistent elevation in core PCE]] reinforces the Fed\'s data-dependent and cautious stance\n\n' +
      'Data is released monthly, typically around the [[10th-15th of each month]] for the previous month, alongside headline CPI.',
    impact:
      'Core Inflation has [[significant implications]] for currency markets through Fed policy channels:\n\n' +
      '[[Hawkish Core Inflation]]\n\n' +
      '• [[Core CPI/PCE remains elevated]]\n\n' +
      '• [[Services inflation stays firm]]\n\n' +
      '• [[Wage growth remains strong]]\n\n' +
      '→ [[USD support, higher real yields, pressure on risk assets]]\n\n' +
      '[[Dovish Core Inflation]]\n\n' +
      '• [[Sustained downward trend]]\n\n' +
      '• [[Broad-based easing across services]]\n\n' +
      '• [[Wage pressures cool]]\n\n' +
      '→ [[USD weakness, yield compression, support for equities and gold]]\n\n' +
      '[[Market dynamics]]: Core inflation remains the [[key constraint on aggressive Fed easing]]. Sustained declines strengthen the case for rate cuts, while sticky core readings delay or reduce expected easing. Short-dated yields and USD pricing [[react rapidly to core surprises]]. Core inflation acts as a [[confirmation indicator for broader disinflation trends]].',
    context:
      '[[Current Core Inflation Trend (Late 2025)]]\n\n' +
      'Core CPI is running at approximately [[2.6% YoY]], down from levels near 3.0% earlier in 2025. This marks the [[slowest pace of core inflation since early 2021]], suggesting a gradual easing in underlying price pressures.\n\n' +
      'However, core inflation remains [[above the Fed\'s 2% target]], reinforcing a cautious approach to rate cuts rather than aggressive easing.\n\n' +
      'Key takeaway: Disinflation is progressing, but persistence in core components keeps policy restrictive.\n\n' +
      '[[Key Drivers of Core Inflation]]\n\n' +
      'Services & Shelter:\n\n' +
      '• [[Shelter and services inflation remain the stickiest components]], slowing the pace of overall disinflation\n\n' +
      '• These categories are [[heavily influenced by wage growth and labor market conditions]]\n\n' +
      'Wages & Labor Costs:\n\n' +
      '• [[Elevated wage growth has sustained service-sector inflation]]\n\n' +
      '• A [[cooling labor market is required]] for a durable decline in core prices\n\n' +
      'Structural & Policy Factors:\n\n' +
      '• [[Tariffs and supply-side frictions]] continue to apply upward pressure to core goods prices\n\n' +
      '• These effects [[limit how quickly core inflation can revert to target]]\n\n' +
      '[[Institutional & Bank Perspective]]\n\n' +
      'Major institutions broadly agree on three themes:\n\n' +
      '• [[Core inflation is cooling, but remains structurally sticky]]\n\n' +
      '• [[Services inflation is the primary obstacle]] to reaching 2%\n\n' +
      '• [[Full normalization may extend into 2026]], not 2025\n\n' +
      'Several banks describe the environment as [["disinflation with persistence"]], rather than a clean return to target.\n\n' +
      '[[Political & Structural Context]]\n\n' +
      'Trade and tariff policies continue to contribute to [[upward core price pressure]].\n\n' +
      'Data collection disruptions during 2025 introduced [[short-term noise into CPI readings]].\n\n' +
      'Political pressure for easier policy contrasts with core inflation still running above target.\n\n' +
      'Trader implication: Core inflation data may trigger [[outsized repricing as markets debate signal vs distortion]].',
    traderImplications:
      '[[Market & Fed Implications]]\n\n' +
      'Core inflation remains the [[key constraint on aggressive Fed easing]]. Sustained declines strengthen the case for rate cuts, while sticky core readings delay or reduce expected easing. Short-dated yields and USD pricing [[react rapidly to core surprises]]. Core inflation acts as a [[confirmation indicator for broader disinflation trends]].\n\n' +
      '[[What Traders Should Monitor Next]]\n\n' +
      'High-impact core inflation signals include:\n\n' +
      '• [[Monthly Core CPI momentum]]\n\n' +
      '• [[Core PCE releases]] (Fed-preferred)\n\n' +
      '• [[Services & shelter inflation breakdowns]]\n\n' +
      '• [[Wage growth and labor cost indicators]]\n\n' +
      '• [[Inflation expectations surveys]]\n\n' +
      'The [[strongest macro trades]] emerge when core inflation trends align with Fed guidance and market expectations.\n\n' +
      '[[FXSentinel Usage]]\n\n' +
      'Within FXSentinel, Core Inflation functions best as:\n\n' +
      '• [[Policy constraint indicator]]\n\n' +
      '• [[Rate-cut timing signal]]\n\n' +
      '• [[Real-yield and USD bias filter]]\n\n' +
      '• [[Volatility catalyst around CPI & PCE releases]]',
  },
};

function Economies() {
  const [selectedEconomy, setSelectedEconomy] = useState('US');
  const [apiIndicatorsData, setApiIndicatorsData] = useState({});
  const [apiDataLoading, setApiDataLoading] = useState(false);
  const [useApiData, setUseApiData] = useState({}); // Track which countries successfully loaded from API
  const [error, setError] = useState(null);
  const analysisRef = React.useRef(null);
  const fetchedCountriesRef = React.useRef(new Set()); // Track which countries we've already attempted to fetch

  // Error boundary for component
  React.useEffect(() => {
    const errorHandler = (event) => {
      console.error('Economies component error:', event.error);
      setError(event.error?.message || 'An error occurred');
    };
    window.addEventListener('error', errorHandler);
    return () => window.removeEventListener('error', errorHandler);
  }, []);

  // Fetch indicators from Google Sheets API when economy changes
  useEffect(() => {
    const fetchIndicators = async () => {
      try {
        // Check if we should force refresh (add ?refresh=true to URL or use Shift+Click)
        const urlParams = new URLSearchParams(window.location.search);
        const forceRefresh = urlParams.get('refresh') === 'true';
        
        // Check if we recently fetched this economy (within last 30 seconds)
        const lastFetchTime = fetchedCountriesRef.current.get(selectedEconomy);
        const now = Date.now();
        const timeSinceLastFetch = lastFetchTime ? now - lastFetchTime : Infinity;
        const REFETCH_INTERVAL = 30000; // 30 seconds - allow refetch after this time
        
        // Skip if we recently fetched this economy (unless forcing refresh)
        if (!forceRefresh && lastFetchTime && timeSinceLastFetch < REFETCH_INTERVAL) {
          console.log(`⏭️ Skipping API call for ${selectedEconomy} - fetched ${Math.round(timeSinceLastFetch / 1000)}s ago (cache valid)`);
          return;
        }
        
        console.log(`🔄 Fetching ${selectedEconomy} indicators from API...`);

        // Mark as fetched with timestamp (unless forcing refresh)
        if (!forceRefresh) {
          fetchedCountriesRef.current.set(selectedEconomy, now);
        }

        // Check if config is available
        if (!config || !config.endpoints || !config.endpoints.economyIndicators) {
          console.warn('⚠️ Config not available, using fallback JSON');
          setUseApiData(prev => ({
            ...prev,
            [selectedEconomy]: false
          }));
          return;
        }

        // Don't block UI - show cards immediately with placeholder data
        // API data will update cards when it arrives
        setApiDataLoading(true);
        
        // Reduced timeout for faster fallback (2 seconds instead of 5)
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 2000);
        
        // Add cache-busting parameter if forcing refresh
        let apiUrl = config.endpoints.economyIndicators(selectedEconomy);
        if (forceRefresh) {
          apiUrl += `?refresh=true&_t=${Date.now()}`;
        }
        
        console.log(`📡 API URL: ${apiUrl}`);
        const response = await fetch(apiUrl, {
          signal: controller.signal
        });
        console.log(`📥 API Response status: ${response.status}`);
        
        clearTimeout(timeoutId);
        
        if (response.ok) {
          const data = await response.json();
          console.log(`📦 API Response for ${selectedEconomy}:`, {
            status: data.status,
            indicatorCount: data.indicators ? Object.keys(data.indicators).length : 0,
            cached: data.cached,
            source: data.source
          });
          
          if (data.status === 'success' && data.indicators) {
            // Store API data for this country
            setApiIndicatorsData(prev => ({
              ...prev,
              [selectedEconomy]: { indicators: data.indicators }
            }));
            setUseApiData(prev => ({
              ...prev,
              [selectedEconomy]: true
            }));
            console.log(`✅ Loaded ${selectedEconomy} indicators from Google Sheets (${Object.keys(data.indicators).length} indicators, cached: ${data.cached})`);
          } else {
            // API returned error, use fallback
            setUseApiData(prev => ({
              ...prev,
              [selectedEconomy]: false
            }));
            console.log(`⚠️ API returned error for ${selectedEconomy}, using fallback JSON`);
          }
        } else {
          // API request failed, use fallback
          setUseApiData(prev => ({
            ...prev,
            [selectedEconomy]: false
          }));
          console.log(`⚠️ API request failed for ${selectedEconomy} (${response.status}), using fallback JSON`);
        }
      } catch (error) {
        // Network error or timeout, use fallback
        setUseApiData(prev => ({
          ...prev,
          [selectedEconomy]: false
        }));
        if (error.name !== 'AbortError') {
          console.log(`⚠️ Failed to fetch ${selectedEconomy} indicators from API, using fallback JSON:`, error.message);
        }
      } finally {
        setApiDataLoading(false);
      }
    };

    fetchIndicators();
  }, [selectedEconomy]); // Only depend on selectedEconomy

  // Central bank rates data (will move to backend later)
  const centralBankRates = [
    {
      flag: '🇺🇸',
      country: 'USA',
      rate: 3.75,
      bankName: 'Fed',
      trend: 'down',
      nextMeeting: 'null'
    },
    {
      flag: '🇬🇧',
      country: 'UK',
      rate: 3.75,
      bankName: 'BOE',
      trend: 'stable',
      nextMeeting: 'null'
    },
    {
      flag: '🇪🇺',
      country: 'EU',
      rate: 2.15,
      bankName: 'ECB',
      trend: 'stable',
      nextMeeting: 'null'
    },
    {
      flag: '🇯🇵',
      country: 'Japan',
      rate: 0.75,
      bankName: 'BOJ',
      trend: 'stable',
      nextMeeting: 'null'
    }
  ];

  const getTrendArrow = (trend) => {
    if (trend === 'up') return '↑';
    if (trend === 'down') return '↓';
    return '→';
  };

  const formatLastUpdated = () => {
    // Hardcoded for now - will be dynamic later
    return '2 days ago';
  };

  const handleScrollToAnalysis = () => {
    if (analysisRef.current) {
      analysisRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  return (
    <div className="economies-tab">
      <div className="economies-content">
        {/* Header with Central Bank Rates */}
        <div className="economies-header">
          <h1 className="economies-title">ECONOMIC INDICATORS</h1>
          
          <div className="central-bank-rates">
            <span className="rates-label" title="Central Bank Rates"><b>CBR:</b></span>
            {/* Ticker wrap: on mobile, inner scrolls right-to-left with duplicated content for seamless loop */}
            <div className="rates-ticker-wrap">
              <div className="rates-ticker-inner">
                <div className="rates-grid">
                  {centralBankRates.map((item, index) => (
                    <React.Fragment key={`${item.country}-1`}>
                      <div className="rate-item">
                        <span className="flag">{item.flag}</span>
                        <span className="rate-value">{item.rate.toFixed(2)}%</span>
                        <span className="bank-name">{item.bankName}</span>
                        <span className={`rate-trend ${item.trend}`}>
                          {getTrendArrow(item.trend)}
                        </span>
                      </div>
                      {index < centralBankRates.length - 1 && (
                        <span className="rate-divider">│</span>
                      )}
                    </React.Fragment>
                  ))}
                </div>
                <div className="rates-grid rates-grid-duplicate">
                  {centralBankRates.map((item, index) => (
                    <React.Fragment key={`${item.country}-2`}>
                      <div className="rate-item">
                        <span className="flag">{item.flag}</span>
                        <span className="rate-value">{item.rate.toFixed(2)}%</span>
                        <span className="bank-name">{item.bankName}</span>
                        <span className={`rate-trend ${item.trend}`}>
                          {getTrendArrow(item.trend)}
                        </span>
                      </div>
                      {index < centralBankRates.length - 1 && (
                        <span className="rate-divider">│</span>
                      )}
                    </React.Fragment>
                  ))}
                </div>
              </div>
            </div>
          </div>
          
          <span className="economies-last-updated">Updated: {formatLastUpdated()}</span>
        </div>

        {/* Economy Cards will go here */}
        <div className="economies-main-card">
          {/* Card Header */}
          <div className="card-header">
            <div className="card-header-main">
            <span className="card-header-text">Choose Economy:</span>
            <select className="economy-selector" value={selectedEconomy} onChange={(e) => setSelectedEconomy(e.target.value)}>
              <option value="US">🇺🇸 United States</option>
              <option value="EUR">🇪🇺 European Union</option>
              <option value="GBP">🇬🇧 United Kingdom</option>
              <option value="JPY">🇯🇵 Japan</option>
            </select>
            </div>
            <button type="button" className="holistic-scan-button" onClick={handleScrollToAnalysis}>
              Hollistic Scan
            </button>
          </div>
          
          {/* Card Body */}
          <div className="card-body">
              <EconomyDetails 
                selectedEconomy={selectedEconomy} 
                analysisRef={analysisRef}
                apiIndicatorsData={apiIndicatorsData}
                useApiData={useApiData}
              />
          </div>
        </div>
      </div>
    </div>
  );
}

export default Economies;


function EconomyDetails({ selectedEconomy, analysisRef, apiIndicatorsData, useApiData }) {
  const [isLoading, setIsLoading] = useState(false);
  const [expandedIndicatorId, setExpandedIndicatorId] = useState(null);
  const [loadingIndicatorId, setLoadingIndicatorId] = useState(null);
  const [chartHover, setChartHover] = useState(null);
  const [error, setError] = useState(null);
  const [activeYieldSymbol, setActiveYieldSymbol] = useState('OANDA:USB10YUSD');

  useEffect(() => {
    const defaultByEconomy = {
      US: 'OANDA:USB10YUSD',
      EUR: 'OANDA:DE10YBEUR',
      GBP: 'OANDA:UK10YBGBP',
      JPY: 'OANDA:USB10YUSD'
    };
    const symbol = defaultByEconomy[selectedEconomy] || 'OANDA:USB10YUSD';
    setActiveYieldSymbol(symbol);
  }, [selectedEconomy]);

  const activeYieldIndex = useMemo(
    () => Math.max(0, YIELD_MARKETS.findIndex((market) => market.symbol === activeYieldSymbol)),
    [activeYieldSymbol]
  );

  const activeYield = YIELD_MARKETS[activeYieldIndex] || YIELD_MARKETS[0];

  const handleYieldWheel = (event) => {
    event.preventDefault();
    const direction = event.deltaY > 0 ? 1 : -1;
    const nextIndex = (activeYieldIndex + direction + YIELD_MARKETS.length) % YIELD_MARKETS.length;
    setActiveYieldSymbol(YIELD_MARKETS[nextIndex].symbol);
  };

  // Log for debugging
  React.useEffect(() => {
    console.log('EconomyDetails rendered with selectedEconomy:', selectedEconomy);
  }, [selectedEconomy]);

  // Normalize chart data from actual values to 0-100 range for SVG display
  const normalizeChartData = (values) => {
    if (!values || values.length === 0) return [];
    const min = Math.min(...values);
    const max = Math.max(...values);
    const range = max - min;
    if (range === 0) return values.map(() => 50); // If all values are same, center at 50
    return values.map((val) => ((val - min) / range) * 80 + 10); // Scale to 10-90 range for better visibility
  };

  // Format date for display
  const formatDate = (dateString) => {
    if (!dateString) return '';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', { 
        month: 'long', 
        day: 'numeric', 
        year: 'numeric' 
      });
    } catch {
      return dateString;
    }
  };

  // Format date for chart label (compact format)
  const formatChartLabelDate = (dateString) => {
    if (!dateString) return '';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', { 
        month: 'short', 
        year: 'numeric' 
      });
    } catch {
      return dateString;
    }
  };

  // Merge real data from JSON with placeholder data
  const mergeIndicatorData = (placeholderIndicator, realData) => {
    if (!realData) return placeholderIndicator;
    
    // Generate chart label based on available data (compact format)
    let chartLabel = placeholderIndicator.chartLabel;
    if (realData.chartDates && realData.chartDates.length > 0) {
      const startDate = formatChartLabelDate(realData.chartDates[0]);
      const endDate = formatChartLabelDate(realData.chartDates[realData.chartDates.length - 1]);
      chartLabel = `${startDate} - ${endDate}`;
    }
    
    // Store ALL original data points
    const allOriginalData = realData.chartData || null;
    const allDates = realData.chartDates || [];
    
    // For collapsed view: use last 8 points (or all if less than 8)
    const collapsedData = allOriginalData 
      ? (allOriginalData.length > 8 ? allOriginalData.slice(-8) : allOriginalData)
      : null;
    const collapsedDates = allDates.length > 8 ? allDates.slice(-8) : allDates;
    
    // Normalize both datasets
    const normalizedCollapsed = collapsedData 
      ? normalizeChartData(collapsedData) 
      : placeholderIndicator.chartData;
    const normalizedAll = allOriginalData 
      ? normalizeChartData(allOriginalData) 
      : normalizedCollapsed;
    
    return {
      ...placeholderIndicator,
      currentValue: realData.currentValue || placeholderIndicator.currentValue,
      // Always use placeholder description for card display (professional briefs)
      // Real data descriptions are kept for reference but not displayed in cards
      description: placeholderIndicator.description,
      chartData: normalizedCollapsed, // Default to collapsed (8 points)
      chartDataExpanded: normalizedAll, // All points for expanded view
      chartDataOriginal: collapsedData, // Original values for collapsed tooltips
      chartDataOriginalAll: allOriginalData, // All original values for expanded tooltips
      chartDates: collapsedDates, // Dates for collapsed view
      chartDatesAll: allDates, // All dates for expanded view
      chartLabel: chartLabel,
      source: realData.source || placeholderIndicator.source,
      sourceUrl: realData.sourceUrl || null,
      notes: realData.notes || placeholderIndicator.notes,
      asOf: realData.asOf ? formatDate(realData.asOf) : null,
      unit: realData.unit || null,
      frequency: realData.frequency || null
    };
  };

  const economyData = useMemo(() => {
    const baseData = {
    US: {
      flag: '🇺🇸',
      name: 'United States',
      description:
        'Data sources: Federal Reserve (FRED), Bureau of Labor Statistics, BEA. The US economy is a diversified, consumer-driven economy with significant services output, deep financial markets, and the USD as the world\'s reserve currency. Key drivers: labor market strength, consumer spending, credit conditions, and Fed policy.',
      indicators: [
        {
          id: 'interest-rate',
            title: 'Federal Funds Rate',
          currentValue: '4.25%',
            description: 'Federal Funds Rate - The primary monetary policy tool set by the Federal Open Market Committee (FOMC). Represents the target range for overnight interbank lending rates.',
          chartData: [85, 78, 82, 88, 92, 89, 87, 90],
            chartLabel: 'Federal Funds Rate (Upper Bound)'
        },
        {
          id: 'inflation-YoY',
          title: 'Inflation YoY (CPI)',
          currentValue: '3.2%',
          description: 'Consumer Price Index Year-over-Year - Measures the annual percentage change in prices for a basket of consumer goods and services. The primary inflation gauge used by the Federal Reserve to assess price stability and guide monetary policy decisions.',
          chartData: [45, 52, 48, 41, 38, 42, 39, 35],
          chartLabel: 'YoY trend'
        },
        {
          id: 'core-inflation-YoY',
          title: 'Core Inflation YoY',
          currentValue: '3.0%',
          description: 'Core Inflation Year-over-Year - Measures the annual change in consumer prices excluding volatile food and energy components. The Federal Reserve\'s preferred inflation gauge for monetary policy decisions, providing a clearer view of underlying inflation trends.',
          chartData: [60, 65, 58, 62, 68, 64, 67, 70],
          chartLabel: 'YoY trend'
        },
        {
          id: 'gdp-growth',
          title: 'GDP Growth',
          currentValue: '+2.1%',
          description: 'Gross Domestic Product Growth Rate - Measures the quarterly percentage change in real GDP (adjusted for inflation), indicating economic expansion or contraction. A key indicator of overall economic health and growth momentum.',
          chartData: [60, 65, 58, 62, 68, 64, 67, 70],
          chartLabel: 'Q/Q growth'
        },
        {
          id: 'unemployment',
          title: 'Unemployment',
          currentValue: '3.8%',
          description: 'Unemployment Rate - Measures the percentage of the labor force that is jobless but actively seeking work. A key indicator of labor market health and economic slack, closely watched by the Federal Reserve for monetary policy decisions.',
          chartData: [25, 28, 26, 24, 22, 23, 21, 20],
          chartLabel: 'Rate trend'
        },
        {
          id: 'nonfarm-payrolls',
          title: 'Non-Farm Payrolls',
          currentValue: '119K',
          description: 'Non-Farm Payrolls (NFP) - Measures the monthly change in employment, excluding farm workers, government employees, and non-profit organization employees. One of the most closely watched economic indicators, released on the first Friday of each month.',
          chartData: [70, 75, 72, 78, 82, 79, 85, 88],
          chartLabel: 'Monthly change'
        }
      ],
    },
    EUR: {
      flag: '🇪🇺',
      name: 'European Union',
      description:
        'Data sources: ECB, Eurostat. The euro area is export-oriented with manufacturing hubs and a shared monetary policy under the ECB. Key drivers: energy costs, industrial output, services PMIs, and ECB stance.',
      indicators: [
        {
          id: 'interest-rate',
          title: 'Main Refinancing Rate',
          currentValue: '2.15%',
          description: 'Main Refinancing Rate - The primary monetary policy tool set by the European Central Bank (ECB). Represents the interest rate at which banks can borrow from the ECB for one week. This rate influences borrowing costs across the eurozone and is a key driver of EUR strength.',
          chartData: [45, 48, 52, 55, 58, 56, 54, 52],
          chartLabel: 'Last 8 months'
        },
        {
          id: 'inflation',
          title: 'Inflation (HICP)',
          currentValue: '2.4%',
          description: 'Harmonized Index of Consumer Prices (HICP) - The official measure of inflation for the eurozone, calculated by Eurostat. HICP provides a comparable measure of inflation across all EU member states and is the primary inflation target for the European Central Bank (ECB).',
          chartData: [65, 68, 72, 75, 78, 76, 74, 72],
          chartLabel: 'YoY trend'
        },
        {
          id: 'core-inflation-YoY',
          title: 'Core Inflation YoY',
          currentValue: '2.4%',
          description: 'Core HICP (Harmonized Index of Consumer Prices) Year-over-Year - Measures the annual change in consumer prices excluding volatile food, energy, alcohol, and tobacco. This is the European Central Bank\'s preferred inflation gauge for monetary policy decisions, providing a clearer view of underlying inflation trends without short-term commodity price fluctuations.',
          chartData: [70, 72, 75, 78, 82, 80, 85, 88],
          chartLabel: 'Core YoY trend'
        },
        {
          id: 'gdp-growth',
          title: 'GDP Growth',
          currentValue: '+0.8%',
          description: 'GDP Annual Growth Rate - Measures the year-over-year percentage change in Gross Domestic Product for the eurozone. GDP growth reflects the overall health and expansion of the economy, influencing ECB monetary policy decisions and EUR strength.',
          chartData: [40, 42, 38, 35, 32, 34, 36, 38],
          chartLabel: 'Q/Q growth'
        },
        {
          id: 'unemployment',
          title: 'Unemployment',
          currentValue: '6.4%',
          description: 'Unemployment Rate - Measures the percentage of the labor force that is jobless but actively seeking work in the eurozone. Published monthly by Eurostat, this seasonally adjusted indicator is a key gauge of labor market health and economic slack, closely monitored by the European Central Bank for monetary policy decisions. The unemployment rate influences wage dynamics, inflation expectations, and ECB policy expectations, making it critical for EUR valuation and cross-asset positioning.',
          chartData: [55, 58, 56, 54, 52, 53, 51, 50],
          chartLabel: 'Rate trend'
        },
        {
          id: 'current-account',
          title: 'Current Account',
          currentValue: '+€12.8B',
          description: 'Current Account Balance - Measures the net flow of goods, services, primary income, and secondary income between the eurozone and the rest of the world. Published monthly by the European Central Bank, a positive current account indicates the eurozone is a net lender, supporting EUR strength through capital inflows. The current account reflects export competitiveness, savings-investment dynamics, and structural economic position, making it critical for EUR valuation and cross-asset positioning.',
          chartData: [70, 72, 75, 78, 82, 80, 85, 88],
          chartLabel: 'Monthly balance'
        }
      ],
    },
    GBP: {
      flag: '🇬🇧',
      name: 'United Kingdom',
      description:
        'Data sources: Bank of England, ONS. The UK economy is services-heavy (financial services core), sensitive to rates and housing. Key drivers: wage growth, services PMIs, BoE policy, and Sterling risk sentiment.',
      indicators: [
        {
          id: 'interest-rate',
          title: 'Bank Rate',
          currentValue: '3.75%',
          description: 'Bank Rate - The primary monetary policy tool set by the Bank of England\'s Monetary Policy Committee (MPC). Represents the interest rate at which the BoE lends to commercial banks overnight, anchoring the UK yield curve and influencing borrowing costs across the economy. The Bank Rate is set to meet the 2% CPI inflation target while supporting growth and employment. Changes in the Bank Rate directly impact GBP valuation, UK asset pricing, and cross-asset capital flows, making it critical for FX, rates, and equity traders.',
          chartData: [75, 78, 82, 85, 88, 86, 84, 82],
          chartLabel: 'Last 8 months'
        },
        {
          id: 'inflation',
          title: 'Inflation (CPI)',
          currentValue: '3.2%',
          description: 'Consumer Price Index (CPI) Year-over-Year - Measures the annual percentage change in prices for a basket of consumer goods and services in the United Kingdom. Published monthly by the Office for National Statistics (ONS), CPI is the Bank of England\'s primary inflation target (2%) and directly shapes monetary policy expectations, GBP valuation, and cross-asset risk sentiment. The CPI reflects the cost of living and purchasing power, with components including food, energy, housing, and services. Markets react to surprises versus expectations and trend momentum, making CPI a critical input for FX, rates, and equity traders.',
          chartData: [80, 85, 88, 92, 95, 93, 90, 88],
          chartLabel: 'YoY trend'
        },
        {
          id: 'core-inflation-YoY',
          title: 'Core Inflation YoY',
          currentValue: '3.2%',
          description: 'Core CPI (Consumer Price Index) Year-over-Year - Measures the annual change in consumer prices excluding volatile food, energy, alcohol, and tobacco components in the United Kingdom. Published monthly by the Office for National Statistics (ONS), Core CPI provides a clearer view of underlying inflation trends and is the Bank of England\'s preferred gauge for assessing inflation persistence and policy effectiveness. Core CPI reflects domestic price pressures that monetary policy can influence, making it critical for BoE policy expectations, GBP valuation, and cross-asset risk sentiment. Markets often react more strongly to core inflation surprises than headline CPI, especially during policy transitions.',
          chartData: [70, 72, 75, 78, 82, 80, 85, 88],
          chartLabel: 'Core YoY trend'
        },
        {
          id: 'gdp-growth',
          title: 'GDP Growth',
          currentValue: '+1.5%',
          description: 'GDP Annual Growth Rate - Measures the year-over-year percentage change in Gross Domestic Product for the United Kingdom. GDP growth reflects the overall health and expansion of the economy, influencing Bank of England monetary policy decisions and GBP strength. Strong growth supports GBP via real yield support and capital inflows, while weak growth increases rate-cut probability and supports defensive FX and bonds. GDP growth provides context on demand strength, recession risk, and policy durability, making it critical for FX, rates, and equity traders.',
          chartData: [50, 52, 48, 45, 42, 44, 46, 48],
          chartLabel: 'Q/Q growth'
        },
        {
          id: 'unemployment',
          title: 'Unemployment',
          currentValue: '4.2%',
          description: 'Unemployment Rate - Measures the percentage of the labor force that is jobless but actively seeking work in the United Kingdom. Published monthly by the Office for National Statistics (ONS), this indicator is a key gauge of labor market health and economic slack, closely monitored by the Bank of England for monetary policy decisions. The unemployment rate influences wage dynamics, inflation expectations, and BoE policy expectations, making it critical for GBP valuation and cross-asset positioning. Lower unemployment typically supports GBP strength through improved economic outlook, while rising unemployment increases pressure for accommodative policy, typically weighing on GBP.',
          chartData: [35, 38, 36, 34, 32, 33, 31, 30],
          chartLabel: 'Rate trend'
        },
        {
          id: 'wage-growth',
          title: 'Wage Growth',
          currentValue: '4.7%',
          description: 'Wage Growth (Average Weekly Earnings) - Measures the year-over-year percentage change in average weekly earnings for employees in the United Kingdom. Published monthly by the Office for National Statistics (ONS), wage growth reflects labor market tightness, inflation persistence, and purchasing power. The Bank of England monitors wage growth closely as a key indicator of inflationary pressures and a critical input for monetary policy decisions. Strong wage growth supports inflation persistence, potentially constraining BoE easing, while moderating wage growth supports disinflation and accommodative policy, making it critical for GBP valuation and cross-asset positioning.',
          chartData: [60, 62, 65, 68, 72, 70, 75, 78],
          chartLabel: 'YoY growth'
        }
      ],
    },
    JPY: {
      flag: '🇯🇵',
      name: 'Japan',
      description:
        'Data sources: BoJ, Statistics Bureau of Japan. Japan is an export-led economy with historically low rates and a focus on yield-curve control. Key drivers: JPY carry trades, energy import costs, and BoJ policy normalization path.',
      indicators: [
        {
          id: 'interest-rate',
          title: 'Interest Rate',
          currentValue: '0.75%',
          description: 'Bank of Japan Policy Rate - The primary monetary policy tool set by the Bank of Japan\'s Policy Board. Represents the interest rate at which the BoJ lends to financial institutions overnight, anchoring the Japanese yield curve and influencing borrowing costs across the economy. The Policy Rate is set to achieve the 2% inflation target while supporting economic growth. Changes in the Policy Rate directly impact JPY valuation, Japanese asset pricing, and cross-asset capital flows, making it critical for FX, rates, and equity traders.',
          chartData: [15, 18, 22, 25, 28, 26, 24, 22],
          chartLabel: 'Last 8 months'
        },
        {
          id: 'inflation',
          title: 'Inflation (CPI)',
          currentValue: '3.0%',
          description: 'Consumer Price Index (CPI) Year-over-Year - Measures the annual percentage change in prices for a basket of consumer goods and services in Japan. Published monthly by the Statistics Bureau of Japan, CPI is the Bank of Japan\'s primary inflation target (2%) and directly shapes monetary policy expectations, JPY valuation, and cross-asset risk sentiment. The CPI reflects the cost of living and purchasing power of the yen, with components including food, energy, housing, and services. Markets react to surprises versus expectations and trend momentum, making CPI a critical input for FX, rates, and equity traders.',
          chartData: [35, 38, 42, 45, 48, 46, 44, 42],
          chartLabel: 'YoY trend'
        },
        {
          id: 'core-inflation-YoY',
          title: 'Core Inflation YoY',
          currentValue: '3.0%',
          description: 'Core CPI (Consumer Price Index) Year-over-Year - Measures the annual change in consumer prices excluding volatile fresh food components in Japan. Published monthly by the Statistics Bureau of Japan, Core CPI provides a clearer view of underlying inflation trends and is the Bank of Japan\'s preferred gauge for assessing inflation persistence and policy effectiveness. Core CPI reflects domestic price pressures that monetary policy can influence, making it critical for BoJ policy expectations, JPY valuation, and cross-asset risk sentiment. Markets often react more strongly to core inflation surprises than headline CPI, especially during policy transitions.',
          chartData: [50, 55, 52, 48, 52, 54, 56, 58, 52, 50, 56, 62, 60, 62, 66, 66, 70, 64, 62, 56, 60, 62],
          chartLabel: 'YoY trend'
        },
        {
          id: 'gdp-growth',
          title: 'GDP Growth',
          currentValue: '+1.2%',
          description: 'GDP Annual Growth Rate - Measures the year-over-year percentage change in Gross Domestic Product for Japan. GDP growth reflects the overall health and expansion of the economy, influencing Bank of Japan monetary policy decisions and JPY strength. Strong growth supports JPY via real yield support and capital inflows, while weak growth increases rate-cut probability and supports defensive FX and bonds. GDP growth provides context on demand strength, recession risk, and policy durability, making it critical for FX, rates, and equity traders.',
          chartData: [30, 32, 28, 25, 22, 24, 26, 28],
          chartLabel: 'Q/Q growth'
        },
        {
          id: 'unemployment',
          title: 'Unemployment',
          currentValue: '2.6%',
          description: 'Unemployment Rate - Measures the percentage of the labor force that is jobless but actively seeking work in Japan. Published monthly by the Statistics Bureau of Japan, this indicator is a key gauge of labor market health and economic slack, closely monitored by the Bank of Japan for monetary policy decisions. The unemployment rate influences wage dynamics, inflation expectations, and BoJ policy expectations, making it critical for JPY valuation and cross-asset positioning. Lower unemployment typically supports JPY strength through improved economic outlook and reduced easing pressure, while rising unemployment increases pressure for accommodative policy, typically weighing on JPY.',
          chartData: [20, 22, 20, 18, 16, 17, 15, 14],
          chartLabel: 'Rate trend'
        },
        {
          id: 'trade-balance',
          title: 'Current Account',
          currentValue: '+¥1.2T',
          description: 'Current Account Balance - Measures the net flow of goods, services, primary income, and secondary income between Japan and the rest of the world. Published monthly by the Ministry of Finance and compiled by the Bank of Japan, a positive current account indicates Japan is a net lender to the rest of the world, supporting JPY strength through capital flows. The current account reflects export competitiveness, savings-investment dynamics, and structural economic position, making it critical for JPY valuation and cross-asset positioning.',
          chartData: [60, 62, 65, 68, 72, 70, 75, 78],
          chartLabel: 'Monthly balance'
        }
      ],
    },
    };

    // Merge real data from API (Google Sheets) or JSON file (fallback) with placeholder data
    const mergedData = { ...baseData };
    
    // Determine which data source to use for each country
    const indicatorsSource = {};
    Object.keys(baseData).forEach((countryCode) => {
      // Use API data if available and successful, otherwise use JSON fallback
      if (useApiData[countryCode] && apiIndicatorsData[countryCode]?.indicators) {
        indicatorsSource[countryCode] = apiIndicatorsData[countryCode];
      } else if (economyIndicatorsData[countryCode]?.indicators) {
        indicatorsSource[countryCode] = economyIndicatorsData[countryCode];
      }
    });
    
    // Merge indicators from the selected source (API or JSON)
    Object.keys(indicatorsSource).forEach((countryCode) => {
      if (mergedData[countryCode] && indicatorsSource[countryCode]?.indicators) {
        const realIndicators = indicatorsSource[countryCode].indicators;
        
        mergedData[countryCode].indicators = mergedData[countryCode].indicators.map((indicator) => {
          const realData = realIndicators[indicator.id];
          return realData ? mergeIndicatorData(indicator, realData) : indicator;
        });
      }
    });

    return mergedData;
  }, [apiIndicatorsData, useApiData]);

  // Log economyData for debugging
  React.useEffect(() => {
    console.log('EconomyDetails - economyData keys:', Object.keys(economyData));
    console.log('EconomyDetails - selectedEconomy:', selectedEconomy);
    console.log('EconomyDetails - economyData[selectedEconomy]:', economyData[selectedEconomy]);
  }, [economyData, selectedEconomy]);

  // Safely get data with fallback - always return data immediately (no blocking)
  let data;
  try {
    data = economyData[selectedEconomy] || economyData.US || economyData['US'];
    if (!data) {
      console.error('No data found for economy:', selectedEconomy);
      // Return placeholder data instead of error to keep UI responsive
      data = economyData.US || Object.values(economyData)[0];
    }
    if (data) {
      console.log('EconomyDetails - data loaded successfully:', data.name);
    }
  } catch (err) {
    console.error('Error accessing economyData:', err);
    // Fallback to US data to keep UI working
    data = economyData.US || Object.values(economyData)[0];
  }
  
  // If still no data, show error
  if (!data) {
    return (
      <div style={{ padding: '20px', color: 'red' }}>
        <h3>Error: No data available</h3>
        <p>Please refresh the page.</p>
      </div>
    );
  }

  const toggleIndicatorCard = (indicatorId) => {
    const isCurrentlyExpanded = expandedIndicatorId === indicatorId;
    
    if (!isCurrentlyExpanded) {
      // Opening modal - show loading
      setLoadingIndicatorId(indicatorId);
      setExpandedIndicatorId(indicatorId);
      
      // Clear loading after modal opens
      setTimeout(() => {
        setLoadingIndicatorId(null);
      }, 600);
    } else {
      // Closing modal
      setExpandedIndicatorId(null);
      setLoadingIndicatorId(null);
    }
  };

  const closeExpandedCard = () => {
    setExpandedIndicatorId(null);
    setLoadingIndicatorId(null);
  };

  const handleIndicatorKeyDown = (event, indicatorId) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      toggleIndicatorCard(indicatorId);
    }
  };

  const getIndicatorInsights = (indicator, selectedEconomy) => {
    if (Array.isArray(indicator.insights) && indicator.insights.length > 0) {
      return indicator.insights;
    }

    // Special handling for interest-rate with country-specific professional content
    if (indicator.id === 'interest-rate') {
      // EUR Interest Rate
      if (selectedEconomy === 'EUR') {
      return [
          'The European Central Bank has paused its easing cycle after delivering substantial rate cuts through 2024–2025. Policy rates are now held at broadly neutral levels (Main Refinancing Rate: 2.15%), reflecting inflation that has converged toward target and a euro area economy showing modest but improving resilience.',
          'The ECB has emphasized that future decisions will be strictly data-dependent, with no pre-committed rate path. Markets currently price high probability of rate stability through 2026, with low probability of near-term cuts or hikes absent a macro shock.',
          'A steady ECB while other central banks ease may support the euro, though weak growth differentials versus the U.S. remain a structural EUR headwind. EUR crosses remain sensitive to inflation surprises and ECB communication tone.',
          'Future rate direction will depend primarily on core inflation persistence, wage growth dynamics, eurozone growth momentum, and external shocks (energy prices, geopolitics, global trade).',
        ];
      }
      
      // GBP Bank Rate
      if (selectedEconomy === 'GBP') {
        return [
          'Bank of England Bank Rate stands at 3.75% as of December 18, 2025, following a 25 basis point cut from 4.00%. This marks the lowest level since February 2023 and reflects a shift from restrictive policy toward easing, driven by moderating inflation, weak growth, and a softening labor market.',
          'The BoE has cut rates multiple times since August 2024, with the most recent cuts including December 18, 2025 (3.75%), August 7, 2025 (4.00%), and May 8, 2025 (4.25%). The 5-4 voting split in recent decisions indicates internal division on the pace of easing, with some members favoring faster cuts and others cautioning on inflation risks.',
          'CPI inflation stood at 3.2% in November 2025, down from 3.6% in October, but still above the 2% target. The UK economy has shown minimal growth, with GDP expanding by only 0.1% in Q2 2025, while unemployment has risen to 5.1%, the highest since January 2021. Governor Andrew Bailey noted that the UK has "passed the recent peak in inflation and it has continued to fall," allowing for rate reductions.',
          'GBP crosses remain sensitive to Bank Rate expectations and decisions, with above-expectation cuts tending to weaken GBP via dovish repricing, while below-expectation cuts or pauses support GBP through reduced easing pressure. Markets price additional cuts into 2026, with timing sensitive to inflation, wage growth, and labor market data.',
        ];
      }
      
      // JPY Interest Rate
      if (selectedEconomy === 'JPY') {
        return [
          'Bank of Japan Policy Rate stands at 0.75% as of December 19, 2025, following a 25 basis point hike from 0.50%. This marks the highest level since September 1995 and reflects a shift from ultra-loose policy toward normalization, driven by sustained inflation above the 2% target, stronger wage growth, and confidence in achieving stable inflation.',
          'The BoJ has raised rates multiple times since ending negative rates, with the most recent hikes including December 19, 2025 (0.75%), January 24, 2025 (0.50%), and March 19, 2024 (0% to 0.1%). The December 2025 hike to 0.75% aims to curb inflation, which stood at 3% in November, exceeding the BoJ\'s 2% target. This marks the first rate hike cycle in 17 years, signaling a significant shift from ultra-loose monetary policies.',
          'CPI inflation stood at 3% in November 2025, above the 2% target. Wage growth has strengthened, supporting sustainable inflation and confidence in achieving the 2% target. Major financial institutions interpret the normalization as appropriate given sustained inflation and wage growth, but note risks from global uncertainties and the need for a gradual approach. Markets price additional normalization into 2026, with timing sensitive to inflation, wage growth, and economic growth data.',
          'JPY crosses remain sensitive to Policy Rate expectations and decisions, with above-expectation hikes tending to support JPY via hawkish repricing, while below-expectation hikes or pauses weaken JPY through reduced normalization pressure. The interplay between Policy Rate, inflation, wage growth, and growth data is crucial for BoJ policy anticipation. Markets focus on expectations versus outcomes, with significant deviations from consensus driving immediate volatility.',
        ];
      }
      
      // US Interest Rate (default)
      return [
        'The Federal Funds Rate has shifted from restrictive policy toward cautious easing, cutting rates to 3.50%–3.75% amid moderating inflation and signs of labor market softening.',
        'Major global banks broadly expect further rate cuts into 2026, but emphasize a measured and data-dependent pace. Markets currently price 1–3 additional 25bp cuts, with timing sensitive to incoming data.',
        'The highest-conviction trades emerge when data, expectations, and policy guidance align. Monitor core inflation trends, labor market data, Fed communication tone, and yield curve dynamics for rate repricing signals.',
        'Political pressure from President Trump for lower rates adds headline-driven volatility and can influence market narratives around Fed independence and policy credibility.',
      ];
    }

    // Special handling for inflation-YoY with professional content (US only)
    if (indicator.id === 'inflation-YoY' && selectedEconomy === 'US') {
      return [
        'Headline U.S. CPI is running at approximately 2.7% YoY, down from earlier 2025 highs near 3.0%. This moderation reflects easing shelter inflation, base effects, and slower goods price growth.',
        'Core inflation has also cooled but remains above the Federal Reserve\'s 2% target, reinforcing a cautious policy stance rather than aggressive easing. Inflation is easing, but not fully neutralized — keeping policy expectations finely balanced.',
        'Major financial institutions broadly agree that inflation is cooling but warn against declaring victory. Several banks describe current inflation as a "low-grade persistence" environment rather than a clean disinflation cycle.',
        'Inflation remains the primary constraint on Fed easing. Inflation surprises quickly reprice Fed Funds Futures and short-dated yields. For markets, inflation prints act as confirmation or invalidation events for existing rate expectations.',
      ];
    }

    // Special handling for inflation (EUR, GBP, JPY use 'inflation' not 'inflation-YoY')
    // EUR HICP Inflation
    if (indicator.id === 'inflation' && selectedEconomy === 'EUR') {
      return [
        'Eurozone HICP inflation stands at approximately 2.1% year-over-year, placing it very close to the ECB\'s 2% medium-term target. Inflation has stabilized after declining sharply from post-pandemic and energy-shock peaks, reflecting normalized price pressures following easing energy and supply-chain costs.',
        'The ECB operates under a symmetric 2% inflation target over the medium term, and current inflation levels support a more balanced policy stance rather than aggressive tightening or easing. Headline inflation is largely anchored near target, with inflation persistence increasingly driven by domestic components rather than external shocks.',
        'Markets react most strongly to surprises versus consensus expectations, not absolute inflation levels. HICP remains a primary constraint on ECB easing—cooling inflation supports additional rate cuts, while sticky core components, particularly services inflation, cap the pace and depth of easing.',
        'EUR crosses remain sensitive to HICP surprises and ECB communication tone. Key drivers to monitor include core and services inflation trends, wage growth dynamics, energy price volatility, and persistent divergence between headline HICP and underlying components, which often precedes shifts in ECB communication.',
      ];
    }

    // GBP CPI Inflation
    if (indicator.id === 'inflation' && selectedEconomy === 'GBP') {
      return [
        'UK CPI inflation stood at 3.2% year-over-year in November 2025, down from 3.6% in October, marking the second consecutive month of decline and the lowest in five months. The monthly CPI rate for November was -0.2%, with the decline driven by lower prices in food and non-alcoholic beverages, clothing and footwear, and alcohol and tobacco.',
        'The International Monetary Fund projects UK average inflation at 3.4% in 2025 and 2.5% in 2026, the highest among advanced economies. The Office for Budget Responsibility forecasts CPI inflation to average 4.3% in 2025 and 3.7% in 2026, gradually declining to 2.3% by 2030. Markets expect inflation to approach the 2% target by late 2026 or early 2027.',
        'The Bank of England cut the Bank Rate to 3.75% in December 2025, citing established disinflation trends. However, inflation above the 2% target limits aggressive easing. The BoE\'s reaction function weighs inflation persistence, wage growth, growth momentum, and labor market conditions, with current levels supporting continued easing but the pace depending on incoming data.',
        'GBP crosses remain sensitive to CPI surprises, with above-expectation readings tending to support GBP via higher rate expectations, while below-expectation readings weaken GBP through dovish repricing. The November 2025 decline led to a 0.2% dip in GBP/USD, reflecting dovish repricing. CPI remains the primary constraint on BoE easing, with surprises quickly repricing Bank Rate expectations and short-dated yields.',
      ];
    }

    // JPY CPI Inflation
    if (indicator.id === 'inflation' && selectedEconomy === 'JPY') {
      return [
        'Japan\'s CPI stood at 113.20 points in November 2025, up from 112.80 in October. The core CPI (excluding fresh food) increased by 3.0% year-over-year in November, maintaining the same rate as in October and aligning with market expectations. Inflation has been above the BoJ\'s 2% target for over two years, with core CPI consistently exceeding 2%.',
        'Tokyo Core CPI, a leading indicator for nationwide trends, increased by 2.3% year-over-year in December 2025, down from 2.8% in November, suggesting potential easing of inflationary pressures. The Bank of Japan raised the Policy Rate to 0.75% in December 2025, citing persistent inflation above target. The BoJ projects that inflation will stabilize around its 2% target by early 2026, with factors such as energy price fluctuations and domestic demand influencing the inflation trajectory.',
        'Major financial institutions view the sustained inflation above the 2% target as supporting continued BoJ normalization, but note risks from global uncertainties and the need for a gradual approach. The core CPI at 3.0% in November 2025, above the 2% target, supports the BoJ\'s shift toward normalization, but the moderation in Tokyo Core CPI suggests potential easing, which may affect the pace of normalization.',
        'JPY crosses remain sensitive to CPI surprises, with above-expectation readings tending to support JPY via higher rate expectations, while below-expectation readings weaken JPY through dovish repricing. CPI remains a key driver of BoJ normalization, with surprises quickly repricing Policy Rate expectations and short-dated yields. Markets focus on expectations versus outcomes, with significant deviations from consensus driving immediate volatility.',
      ];
    }

    // Special handling for core-inflation-YoY with professional content
    // EUR Core Inflation
    if (indicator.id === 'core-inflation-YoY' && selectedEconomy === 'EUR') {
      return [
        'Eurozone core inflation is running at approximately 2.4% year-over-year, remaining above headline HICP (~2.1%) and slightly above the ECB\'s 2% medium-term target. Core inflation has stabilized rather than fallen sharply in recent months, reflecting sticky domestic price pressures with services inflation continuing to be the dominant contributor.',
        'Core inflation has hovered around the 2.3%–2.5% range, indicating resilience despite easing energy and goods prices. Monthly momentum remains positive, implying that inflationary pressure is cooling gradually rather than collapsing. The gap between headline and core inflation underscores the role of wages, rents, and services costs.',
        'The ECB\'s symmetric 2% target framework places core inflation at the center of persistence assessment. Current levels support a measured and data-dependent approach to rate cuts, reducing urgency for aggressive easing despite headline inflation nearing target. ECB officials frequently cite services and core inflation as key constraints on faster policy normalization.',
        'EUR crosses remain sensitive to core inflation surprises, with above-expectation readings tending to support EUR via higher real rate assumptions, while downside surprises often weaken EUR through dovish repricing of ECB expectations. A decisive downward break in core inflation would materially alter ECB policy pricing and EUR dynamics.',
      ];
    }

    // GBP Core CPI Inflation
    if (indicator.id === 'core-inflation-YoY' && selectedEconomy === 'GBP') {
      return [
        'UK Core CPI inflation stood at 3.2% year-over-year in November 2025, down from 3.4% in October, marking the lowest level since December 2024. The decline was broad-based, with goods inflation decreasing to 2.1% from 2.6% in October, while services inflation edged down to 4.4% from 4.5%. On a monthly basis, core consumer prices fell by 0.2%, reversing October\'s 0.3% rise and posting the first decline since January.',
        'UK core inflation remains among the highest in the G7, with November 2025 at 3.2% compared to 2.4% in Canada, 1.4% in France, 2.6% in Germany, 1.7% in Italy, and 1.5% in Japan. Analysts anticipate the disinflationary trend will continue into 2026, with core inflation expected to approach the BoE\'s 2% target by late 2026 or early 2027. The pace of decline depends on services inflation and wage growth dynamics.',
        'The Bank of England cut the Bank Rate to 3.75% in December 2025, citing established disinflation trends. However, core inflation above the 2% target, particularly sticky services inflation at 4.4%, limits aggressive easing. The BoE\'s reaction function weighs core inflation persistence, wage growth, growth momentum, and labor market conditions, with current levels supporting continued easing but the pace depending on incoming data.',
        'GBP crosses remain sensitive to core inflation surprises, with above-expectation readings tending to support GBP via higher rate expectations, while below-expectation readings weaken GBP through dovish repricing. Markets often react more strongly to core inflation surprises than headline CPI, especially during policy transitions, as core inflation signals underlying inflation persistence. Core CPI remains a key constraint on BoE easing, with surprises quickly repricing Bank Rate expectations.',
      ];
    }

    // JPY Core CPI Inflation
    if (indicator.id === 'core-inflation-YoY' && selectedEconomy === 'JPY') {
      return [
        'Japan\'s Core CPI (excluding fresh food) increased by 3.0% year-over-year in November 2025, maintaining the same rate as in October and aligning with market expectations. Core inflation has been above the BoJ\'s 2% target for over two years, with fluctuations from peaks earlier in 2025 (3.5% in April 2025, highest since January 2023) to current levels. Tokyo Core CPI, a leading indicator, decreased to 2.3% in December 2025, down from 2.8% in November, marking the lowest figure since February but remaining above the BoJ\'s 2% target.',
        'The trend shows sustained inflation above the 2% target, with recent moderation from peaks earlier in 2025. The decline in Tokyo Core CPI suggests potential easing, but nationwide core inflation remains elevated, supporting continued BoJ normalization. Major financial institutions view the sustained core inflation above the 2% target as supporting continued BoJ normalization, but note the recent moderation suggests potential easing. The BoJ projects that inflation will stabilize around its 2% target by early 2026, with factors such as energy price fluctuations and domestic demand influencing the inflation trajectory.',
        'The Bank of Japan raised the Policy Rate to 0.75% in December 2025, citing persistent inflation above target. However, the moderation in Tokyo Core CPI suggests potential easing, which may affect the pace of normalization. The BoJ\'s reaction function weighs core inflation persistence, wage growth, growth momentum, and financial stability, with current levels supporting continued normalization but the pace depending on incoming data, especially core inflation and wage growth.',
        'JPY crosses remain sensitive to core inflation surprises, with above-expectation readings tending to support JPY via higher rate expectations, while below-expectation readings weaken JPY through dovish repricing. Core inflation surprises often have a larger impact than headline CPI surprises, as they signal underlying inflation persistence. Markets focus on expectations versus outcomes, with significant deviations from consensus driving immediate volatility. Core CPI remains a key driver of BoJ normalization, with surprises quickly repricing Policy Rate expectations.',
      ];
    }

    // Special handling for gdp-growth with professional content
    if (indicator.id === 'gdp-growth' && selectedEconomy === 'US') {
      return [
        'Q3 2025 Real GDP registered +4.3% (annualized), the strongest quarterly expansion in over two years. Growth exceeded consensus expectations, driven by resilient consumer spending, a rebound in exports, and continued government and fiscal support.',
        'Earlier in 2025, GDP briefly contracted before rebounding sharply in Q2 and accelerating further in Q3, highlighting uneven but resilient economic momentum. Q4 2025 GDP (GDPNow estimate) is projected at ~3.0%, with full-year 2025 growth near ~1.8–2.0% on an annual basis.',
        'Stronger-than-expected GDP complicates the Federal Reserve\'s easing path. Robust growth reduces urgency for aggressive rate cuts, while persistent expansion alongside sticky inflation increases data-dependence.',
        'Economists note Q3 growth was broad-based, not purely statistical. Consensus expects slower but positive growth into 2026, with risks including cooling consumer demand, softer job creation, and fiscal uncertainty.',
      ];
    }

    // EUR GDP Growth
    if (indicator.id === 'gdp-growth' && selectedEconomy === 'EUR') {
      return [
        'Q3 2025 Eurozone GDP registered +0.3% quarter-on-quarter and ~1.4% year-over-year, reflecting positive but moderate expansion. Growth is driven by consumption, government spending, and export activity, with investment stabilizing after prior weakness.',
        'The euro area economy remains in positive but non-recessionary territory, supporting the ECB\'s strategy of holding interest rates steady. Growth is not strong enough to justify tightening, but positive enough to reduce pressure for aggressive easing.',
        'Growth expansion is uneven across member states, with Spain and France outpacing core economies like Germany, which has exhibited softer growth. ECB projections place full-year 2025 growth near ~1.3%–1.4%, with a modest slowdown expected in 2026 before moderate recovery.',
        'EUR crosses remain sensitive to GDP surprises, with stronger-than-expected prints tending to support EUR (especially if accompanied by resilient inflation), while growth moderation or downside surprises can pressure EUR via dovish repricing of ECB expectations. The interplay between growth and inflation data is crucial for ECB policy anticipation.',
      ];
    }

    // GBP GDP Growth
    if (indicator.id === 'gdp-growth' && selectedEconomy === 'GBP') {
      return [
        'UK GDP expanded by 0.7% quarter-on-quarter in Q1 2025, the fastest growth in a year and surpassing expectations of 0.6%. Q2 2025 growth moderated to 0.3% quarter-on-quarter, still above forecasts of 0.1%. Annual growth for 2024 was 1.1%, revised up from the initial estimate of 0.9%, and an improvement from 0.4% growth in 2023.',
        'Q1 2025 growth was primarily driven by the services sector, with a 0.7% increase driven by retail, wholesale, and computer programming. The production sector rose 1.1% in Q1 2025 but declined 0.7% in March 2025, while construction showed no growth in Q1 2025. The Bank of England revised its 2025 growth forecast down to 0.75% from 1.5%, citing global uncertainties and domestic challenges.',
        'The International Monetary Fund projects 1.3% growth for 2025, positioning the UK as the second-fastest-growing major economy after the U.S. The Confederation of British Industry projects 1.4% growth for 2025 (upgraded from earlier forecasts) and 1.3% for 2026. Business investment remains subdued due to weak demand, high costs, and uncertainties, while consumer spending is modest due to slower real income growth.',
        'GBP crosses remain sensitive to GDP surprises, with above-expectation growth supporting GBP via reduced easing pressure, while below-expectation growth pressuring GBP via increased easing expectations. GDP surprises tend to reprice rate expectations first, with FX and equity volatility following. Markets react not just to the headline number but to components and revisions, with consumption and investment data particularly scrutinized for forward-looking signals.',
      ];
    }

    // JPY GDP Growth
    if (indicator.id === 'gdp-growth' && selectedEconomy === 'JPY') {
      return [
        'Japan\'s GDP contracted by 2.3% on an annualized basis in Q3 2025, marking the first contraction in six quarters and the steepest in two years. This decline was influenced by a 1.2% drop in exports, partly due to U.S. tariffs impacting the auto industry, and reduced capital expenditure. Q2 2025 GDP grew at an annualized rate of 2.2%, driven by resilient exports and business investment, while Q1 2025 contracted by 0.2% quarter-on-quarter, the first negative growth in four quarters.',
        'The Japanese government revised its FY2026 real GDP growth projection to 1.3%, up from 0.9%, reflecting expectations of eased inflation supporting private consumption and business investment. The OECD projects 0.7% growth in 2025 and 0.4% in 2026, driven primarily by domestic demand, while the IMF projects 1.2% growth for 2025 and 0.8% for 2026. Domestic demand, bolstered by strong wage growth, is expected to drive growth, but external factors, particularly U.S. tariffs, pose challenges to export-driven growth.',
        'The Bank of Japan raised the Policy Rate to 0.75% in December 2025, citing persistent inflation above target, but the Q3 2025 contraction may affect the pace of normalization. The BoJ\'s reaction function weighs growth momentum, inflation persistence, wage growth, and financial stability, with current levels supporting continued normalization but the pace depending on incoming data, especially growth and inflation dynamics.',
        'JPY crosses remain sensitive to GDP surprises, with above-expectation growth supporting JPY via increased normalization expectations, while below-expectation growth pressuring JPY via reduced normalization expectations. GDP surprises tend to reprice rate expectations first, with FX and equity volatility following. Markets react not just to the headline number but to components and revisions, with consumption and investment data particularly scrutinized for forward-looking signals.',
      ];
    }

    // Special handling for unemployment with professional content
    if (indicator.id === 'unemployment' && selectedEconomy === 'US') {
      return [
        'Unemployment Rate is at ~4.6%, gradually rising through late 2025, marking the highest level since 2021 and signaling a cooling labor market. Recent employment gains have been concentrated in healthcare, construction, and social assistance, while federal workforce reductions and slower hiring across cyclical sectors have weighed on overall labor conditions.',
        'The labor market has shifted from tight to balanced-to-soft, marked by slowing monthly payroll growth, reduced labor mobility, fewer job openings, and stable but flattening labor force participation. While unemployment remains historically moderate, the direction of travel suggests increasing economic slack.',
        'The recent rise in unemployment strengthens the case for continued, cautious rate cuts, especially if paired with easing inflation. The Fed balances labor market cooling against inflation persistence, with rising unemployment reducing urgency to maintain restrictive rates.',
        'Labor data often leads policy shifts, making it a high-signal indicator for traders. Markets react strongly to unemployment trends, with rising unemployment tending to weigh on USD via lower rate expectations, particularly in USD/JPY, EUR/USD, and GBP/USD pairs.',
      ];
    }

    // EUR Unemployment Rate
    if (indicator.id === 'unemployment' && selectedEconomy === 'EUR') {
      return [
        'Euro Area Unemployment Rate stands at 6.4% as of October 2025, stable month-on-month but up from 6.3% a year earlier. The trend shows near-term stability but a slight year-on-year increase, suggesting the labor market is holding up despite sluggish economic growth.',
        'The European Commission revised its 2025 euro area growth forecast down to 0.9% (from 1.3%), citing trade tensions, a stronger euro, and declining energy prices. Analysts highlight that while unemployment remains low, the slight year-on-year increase serves as a warning sign, with divergence between low unemployment and weak GDP growth creating uncertainty.',
        'The ECB monitors unemployment as a key input for price stability and economic growth. Current context: Unemployment near 6.4% with low inflation suggests limited wage-driven inflation pressure, allowing the ECB to focus on growth support. However, the slight year-on-year increase and weak growth create a trade-off between supporting activity and maintaining price stability.',
        'EUR crosses remain sensitive to unemployment surprises, with above-expectation readings tending to weaken EUR via dovish repricing of ECB expectations, while below-expectation readings support EUR through reduced easing pressure. The interplay between unemployment, wage growth, and inflation is crucial for ECB policy anticipation.',
      ];
    }

    // EUR Current Account
    if (indicator.id === 'current-account' && selectedEconomy === 'EUR') {
      return [
        'Euro Area Current Account recorded a surplus of €26 billion in October 2025, with the 12-month cumulative surplus at €313 billion (2.0% of GDP), down from €419 billion (2.8% of GDP) in the preceding period. The narrowing reflects a shift from surplus to deficit in primary income and a larger secondary income deficit, despite continued goods and services surpluses.',
        'The October 2025 surplus was driven by goods (€31 billion) and services (€13 billion), partially offset by deficits in secondary income (€16 billion) and primary income (€3 billion). The goods surplus remains robust, indicating export competitiveness, while the primary income shift suggests changing investment return dynamics.',
        'Major financial institutions interpret the narrowing surplus as a sign of structural shifts in the eurozone\'s external position. The euro area maintains significant bilateral surpluses with the United Kingdom (€198 billion) and Switzerland (€73 billion), while recording the largest deficit with China (€134 billion), reflecting import dependency and trade structure.',
        'EUR crosses remain sensitive to current account trends, with sustained surpluses supporting EUR through capital flow dynamics, while narrowing surpluses can pressure EUR via reduced capital inflows. Markets focus on trend direction and component breakdowns, with shifts in goods, services, or primary income providing signals about competitiveness and structural position.',
      ];
    }

    // GBP Unemployment Rate
    if (indicator.id === 'unemployment' && selectedEconomy === 'GBP') {
      return [
        'UK unemployment rate stood at 5.1% for the three months to October 2025, the highest since January 2021, up from 4.4% in the same period in 2024. The trend shows a cooling labor market, with rising unemployment, declining employment (74.9% for individuals aged 16 to 64), and increased redundancies (156,000 in the three months to October 2025).',
        'Youth unemployment has risen to 16.0%, with 735,000 individuals aged 16 to 24 unemployed, an increase of 113,000 from the previous quarter. Major financial institutions interpret the rise to 5.1% as a sign of labor market cooling, reflecting economic slowdown and reduced hiring. The increase from 4.4% a year earlier indicates a shift from tight to balanced-to-soft conditions.',
        'The Bank of England monitors unemployment as a key input for price stability and economic growth. Current context: Unemployment at 5.1%, the highest since January 2021, with easing inflation suggests increased economic slack, allowing the BoE to focus on growth support. The BoE cut the Bank Rate to 3.75% in December 2025, citing labor market cooling and easing inflation.',
        'GBP crosses remain sensitive to unemployment surprises, with above-expectation readings tending to weaken GBP via dovish repricing of BoE expectations, while below-expectation readings support GBP through reduced easing pressure. The interplay between unemployment, wage growth, and inflation is crucial for BoE policy anticipation. Markets focus on expectations versus outcomes, with significant deviations from consensus driving immediate volatility.',
      ];
    }

    // JPY Unemployment Rate
    if (indicator.id === 'unemployment' && selectedEconomy === 'JPY') {
      return [
        'Japan\'s unemployment rate stood at 2.6% in November 2025, unchanged from the previous three months and aligning with market expectations. This rate represents the highest level since July 2024. The number of unemployed individuals decreased by 40,000 to 1.81 million, while employment increased by 500,000 to a record high of 68.51 million. The labor force participation rate was 64.1%, slightly down from 64.2% in October but up from 63.5% a year earlier.',
        'The jobs-to-applicants ratio remained steady at 1.18, the lowest since January 2022, indicating 118 job openings for every 100 job seekers. Major financial institutions view the 2.6% rate as low by international standards, reflecting a resilient labor market despite economic challenges. The stability at 2.6% for three consecutive months, combined with record-high employment, suggests underlying labor market strength, but the slight increase from lower levels indicates some softening.',
        'The Bank of Japan raised the Policy Rate to 0.75% in December 2025, citing persistent inflation above target, with low unemployment supporting the case for normalization. Unemployment at 2.6%, low by international standards, with persistent inflation suggests a tight labor market, supporting wage growth and inflation persistence. The BoJ\'s forward guidance and rate decisions depend on the unemployment-inflation-wage nexus, with the current environment supporting continued normalization.',
        'JPY crosses remain sensitive to unemployment surprises, with above-expectation readings tending to weaken JPY via dovish repricing of BoJ expectations, while below-expectation readings support JPY through reduced easing pressure. The interplay between unemployment, wage growth, and inflation is crucial for BoJ policy anticipation. Markets focus on expectations versus outcomes, with significant deviations from consensus driving immediate volatility.',
      ];
    }

    // JPY Current Account
    if (indicator.id === 'trade-balance' && selectedEconomy === 'JPY') {
      return [
        'Japan recorded a current account surplus of ¥4.06 trillion in February 2025, a 48.4% increase from the previous year and the highest for a single month since 1985. This was largely due to a shift in the trade balance to a surplus, with exports rising by 10.4% and imports decreasing by 1.9%. However, January 2025 saw a current account deficit of ¥257.6 billion, the first in two years, driven by weak yen and increased imports.',
        'Fiscal Year 2024: Japan achieved a record-high current account surplus of ¥30.4 trillion, the largest since comparable data became available in 1985. This was primarily driven by a substantial rise in primary income, which reached a surplus of ¥41.7 trillion, an 11.7% increase from the previous year. However, the goods trade balance recorded a deficit of ¥4 trillion, marking the fourth consecutive annual deficit, while the services balance recorded a deficit of ¥2.6 trillion, though the travel industry posted a record surplus of ¥6.7 trillion.',
        'Major financial institutions view the record-high surplus as reflecting Japan\'s strong position in international investment income, but note challenges in the goods and services balance. The primary income surplus of ¥41.7 trillion in fiscal 2024, driven by overseas investments and a weaker yen, underscores Japan\'s role as a net creditor nation. Projections indicate Japan\'s current account surplus will continue to grow, reaching approximately $7.643 trillion by 2030, though the current account surplus as a percentage of GDP is expected to decrease from 4.7% in 2024 to around 3.3% by 2027.',
        'JPY crosses remain sensitive to current account trends, with sustained surpluses supporting JPY through capital flow dynamics, while narrowing surpluses or deficits can pressure JPY via reduced capital inflows. Markets focus on trend direction and component breakdowns, with shifts in goods, services, or primary income providing signals about competitiveness and structural position. The interplay between current account, growth, inflation, and BoJ policy is crucial for JPY valuation.',
      ];
    }

    // GBP Wage Growth
    if (indicator.id === 'wage-growth' && selectedEconomy === 'GBP') {
      return [
        'UK wage growth stood at 4.6% year-over-year in the three months to October 2025, down from 4.7% in the previous quarter, marking the lowest growth rate in over three years. Public sector wages grew by 7.6% in the three months to October 2025, while private sector wages grew by 3.9%. Manufacturing wages rose by 6% in the three months to October 2025, contributing to overall private sector wage growth of 5.4%.',
        'When adjusted for inflation, real regular pay increased by approximately 0.5% in the three months to October 2025, indicating that wage increases are slightly outpacing inflation. The UK\'s real salary growth in 2025 has lagged behind many European counterparts, with a real salary increase of just 0.4%, placing it 21st out of 25 European countries. The moderation in wage growth reflects a cooling labor market and reduced hiring pressure, but wage growth remains above historical averages.',
        'The Bank of England cut the Bank Rate to 3.75% in December 2025, citing labor market cooling and easing inflation. However, wage growth at 4.6% remains elevated relative to the 2% inflation target, limiting aggressive easing. The BoE\'s reaction function weighs wage growth persistence, inflation dynamics, growth momentum, and labor market conditions, with current levels supporting continued easing but the pace depending on incoming data, especially wage growth and services inflation.',
        'GBP crosses remain sensitive to wage growth surprises, with above-expectation readings tending to support GBP via higher rate expectations, while below-expectation readings weaken GBP through dovish repricing. The interplay between wage growth, inflation, and unemployment is crucial for BoE policy anticipation. Markets focus on expectations versus outcomes, with significant deviations from consensus driving immediate volatility. The introduction of a £25 billion increase in employers\' national insurance contributions and a 6.7% rise in the minimum wage in April 2025 have influenced wage dynamics.',
      ];
    }

    // Special handling for nonfarm-payrolls with professional content (US only)
    if (indicator.id === 'nonfarm-payrolls' && selectedEconomy === 'US') {
      return [
        'Non-farm Payrolls registered +64,000 jobs added in November 2025, slightly above the consensus forecast of ~51,000, following October\'s sharp contraction of -105,000 jobs due to federal workforce reductions and shutdown effects.',
        'Total nonfarm employment has shown very little net change since April 2025, suggesting labor market activity has broadly flattened. November\'s gains were concentrated in healthcare, construction, and social assistance, while ADP data reported a decline in private jobs, highlighting underlying weakness outside public sector support.',
        'Even with small gains in November, the overall trend suggests sluggish labor demand and a softening job market, which supports a dovish tilt in monetary policy pricing. Combined with rising unemployment and slowing wage pressures, this environment keeps markets sensitive to labor data surprises.',
        'NFP is known as the "king of economic indicators" due to its market impact. The release often causes immediate and significant volatility in USD pairs, with markets reacting not just to the headline number but to revisions, wage data, and unemployment rate released simultaneously.',
      ];
    }

    // Special handling for core-inflation-YoY with professional content (US only)
    if (indicator.id === 'core-inflation-YoY' && selectedEconomy === 'US') {
      return [
        'Core CPI is running at approximately 2.6% YoY, down from levels near 3.0% earlier in 2025. This marks the slowest pace of core inflation since early 2021, suggesting a gradual easing in underlying price pressures.',
        'However, core inflation remains above the Fed\'s 2% target, reinforcing a cautious approach to rate cuts rather than aggressive easing. Disinflation is progressing, but persistence in core components keeps policy restrictive.',
        'Major institutions broadly agree that core inflation is cooling but remains structurally sticky. Services inflation is the primary obstacle to reaching 2%, and full normalization may extend into 2026.',
        'Core inflation remains the key constraint on aggressive Fed easing. Markets often react more strongly to core inflation surprises than headline CPI, especially during late-cycle or easing environments.',
      ];
    }

    const label = typeof indicator.chartLabel === 'string' ? indicator.chartLabel : 'recent trend';

    return [
      `${indicator.title} is under review relative to its ${label.toLowerCase()} trajectory.`,
      'Change-rate, percentile, and consensus comparisons will appear here once live data integrates.',
      'Holistic Scan will merge this indicator with broader macro drivers in the upcoming release.',
    ];
  };

  // Helper function to render text with highlights
  const renderHighlightedText = (text) => {
    if (!text) return null;
    
    // Split text by highlight markers [[highlight]] and render accordingly
    const parts = text.split(/(\[\[.*?\]\])/g);
    
    return parts.map((part, index) => {
      if (part.startsWith('[[') && part.endsWith(']]')) {
        const highlightText = part.slice(2, -2);
        return (
          <span key={index} className="indicator-highlight">
            {highlightText}
          </span>
        );
      }
      return <span key={index}>{part}</span>;
    });
  };

  // Helper function to render paragraphs
  const renderParagraphs = (text) => {
    if (!text) return null;
    const paragraphs = text.split('\n\n').filter(p => p.trim());
    return paragraphs.map((para, index) => {
      const trimmedPara = para.trim();
      // Check if paragraph is a subheading (starts and ends with [[highlight]])
      const isSubheading = trimmedPara.startsWith('[[') && trimmedPara.endsWith(']]') && 
                          trimmedPara.split(' ').length <= 8; // Likely a subheading if short
      
      if (isSubheading) {
        return (
          <p key={index} className="indicator-subheading">
            {renderHighlightedText(trimmedPara)}
          </p>
        );
      }
      return (
        <p key={index}>{renderHighlightedText(trimmedPara)}</p>
      );
    });
  };

  const getIndicatorDetails = (indicator, selectedEconomy) => {
    // First try country-specific key (e.g., 'interest-rate-EUR', 'inflation-GBP')
    const countrySpecificKey = `${indicator.id}-${selectedEconomy}`;
    const countryDefaults = indicatorDetails[countrySpecificKey] || {};
    
    // Fall back to generic key (e.g., 'interest-rate', 'inflation-YoY')
    const genericDefaults = indicatorDetails[indicator.id] || {};
    
    // Use country-specific if available, otherwise use generic
    const defaults = Object.keys(countryDefaults).length > 0 ? countryDefaults : genericDefaults;
    
    return {
      overview: defaults.overview || indicator.description,
      measurement:
        defaults.measurement ||
        `${indicator.title} measurement methodology will be detailed once official data feeds connect.`,
      impact:
        defaults.impact ||
        `${indicator.title} influence on the currency will be summarised alongside live data releases.`,
      context: defaults.context || null,
      traderImplications: defaults.traderImplications || null,
    };
  };

  const handleChartHover = (indicatorId, event, chartData, originalData = null) => {
    if (!Array.isArray(chartData) || chartData.length === 0) {
      return;
    }

    const rect = event.currentTarget.getBoundingClientRect();
    const relativeX = Math.min(Math.max((event.clientX - rect.left) / rect.width, 0), 1);
    const lastIndex = chartData.length - 1;
    const index = Math.round(relativeX * lastIndex);
    
    // Use original value if available, otherwise use normalized value
    const displayValue = originalData && originalData[index] !== undefined 
      ? originalData[index] 
      : chartData[index];

    // Calculate trend indicator (compare with previous value)
    let trend = null;
    let changePercent = null;
    if (index > 0 && originalData && originalData[index] !== undefined && originalData[index - 1] !== undefined) {
      const currentValue = originalData[index];
      const previousValue = originalData[index - 1];
      const change = currentValue - previousValue;
      changePercent = ((change / previousValue) * 100).toFixed(2);
      trend = change > 0 ? 'up' : change < 0 ? 'down' : 'neutral';
    }

    let xPercent = lastIndex === 0 ? 0 : (index / lastIndex) * 100;
    let yPercent = 100 - chartData[index]; // Use normalized for positioning

    // Smart tooltip positioning to avoid edge clipping
    // Estimate tooltip dimensions (approximate: ~100px width, ~70px height)
    const tooltipWidth = 100;
    const tooltipHeight = 70;
    const margin = 10; // Minimum margin from edges
    
    // Calculate tooltip position in pixels relative to chart container
    const tooltipX = (xPercent / 100) * rect.width;
    const tooltipY = (yPercent / 100) * rect.height;
    
    // Adjust horizontal position if tooltip would clip
    const tooltipLeftEdge = tooltipX - tooltipWidth / 2;
    const tooltipRightEdge = tooltipX + tooltipWidth / 2;
    
    if (tooltipLeftEdge < margin) {
      // Too close to left edge, shift right
      xPercent = ((margin + tooltipWidth / 2) / rect.width) * 100;
    } else if (tooltipRightEdge > rect.width - margin) {
      // Too close to right edge, shift left
      xPercent = ((rect.width - margin - tooltipWidth / 2) / rect.width) * 100;
    }
    
    // Adjust vertical position if tooltip would clip
    const tooltipTopEdge = tooltipY - tooltipHeight - 20; // 20px offset above point
    const tooltipBottomEdge = tooltipY + 20; // 20px offset below point
    
    let tooltipPosition = 'top';
    if (tooltipTopEdge < margin) {
      // Not enough space above, position below
      tooltipPosition = 'bottom';
      yPercent = yPercent + 8; // Position below the point
    } else {
      // Default: position above
      tooltipPosition = 'top';
      yPercent = yPercent - 8; // Position above the point
    }

    setChartHover({
      indicatorId,
      index,
      value: displayValue,
      xPercent,
      yPercent,
      trend,
      changePercent,
      position: tooltipPosition,
    });
  };

  const clearChartHover = () => {
    setChartHover(null);
  };

  // Generate SVG path using Monotone Cubic Interpolation (Method 2)
  // This creates smooth, professional curves that preserve monotonicity
  const generateLinePath = (data) => {
    if (data.length === 0) return '';
    if (data.length === 1) {
      const x = 0;
      const y = 100 - data[0];
      return `M ${x},${y}`;
    }
    
    const points = data.map((value, index) => {
      const x = (index / (data.length - 1)) * 100;
      const y = 100 - value;
      return { x, y };
    });
    
    // Monotone cubic interpolation
    // Calculate slopes (tangents) for each segment
    const slopes = [];
    for (let i = 0; i < points.length - 1; i++) {
      const dx = points[i + 1].x - points[i].x;
      const dy = points[i + 1].y - points[i].y;
      slopes.push(dx !== 0 ? dy / dx : 0);
    }
    
    // Calculate monotone tangents at each point
    const tangents = [];
    for (let i = 0; i < points.length; i++) {
      if (i === 0) {
        tangents.push(slopes[0]);
      } else if (i === points.length - 1) {
        tangents.push(slopes[slopes.length - 1]);
      } else {
        // Average of adjacent slopes, ensuring monotonicity
        const s1 = slopes[i - 1];
        const s2 = slopes[i];
        if (s1 * s2 <= 0) {
          tangents.push(0); // Preserve monotonicity
        } else {
          tangents.push((s1 + s2) / 2);
        }
      }
    }
    
    // Generate cubic bezier path with monotone interpolation
    let path = `M ${points[0].x},${points[0].y}`;
    
    for (let i = 0; i < points.length - 1; i++) {
      const p0 = points[i];
      const p1 = points[i + 1];
      const m0 = tangents[i];
      const m1 = tangents[i + 1];
      
      const dx = p1.x - p0.x;
      const delta = dx / 3; // One-third of the distance
      
      // Control points for cubic bezier
      const cp1x = p0.x + delta;
      const cp1y = p0.y + m0 * delta;
      const cp2x = p1.x - delta;
      const cp2y = p1.y - m1 * delta;
      
      path += ` C ${cp1x},${cp1y} ${cp2x},${cp2y} ${p1.x},${p1.y}`;
    }
    
    return path;
  };

  // Generate area path (line + bottom closure) for gradient fill
  const generateAreaPath = (data) => {
    if (data.length === 0) return '';
    if (data.length === 1) {
      const x = 0;
      const y = 100 - data[0];
      const bottomY = 100;
      return `M ${x},${y} L ${x},${bottomY} L 100,${bottomY} L 100,${y} Z`;
    }
    
    const linePath = generateLinePath(data);
    if (!linePath) return '';
    
    // Close the path to create filled area: line -> bottom right -> bottom left -> Z closes to start
    return `${linePath} L 100,100 L 0,100 Z`;
  };

  // Generate dot positions (matching SVG coordinates)
  const generateDotPositions = (data) => {
    return data.map((value, index) => ({
      x: (index / (data.length - 1)) * 100,
      y: 100 - value
    }));
  };

  // Show cards immediately with placeholder data, update when API data arrives
  // Removed artificial loading delay for better UX

  return (
    <div className="economy-details">
      <div className="economic-indicators-grid">
        {data.indicators.map((indicator) => {
          return (
            <div
              key={indicator.id}
              className="indicator-card"
              role="button"
              tabIndex={0}
              onClick={() => toggleIndicatorCard(indicator.id)}
              onKeyDown={(event) => handleIndicatorKeyDown(event, indicator.id)}
            >
            <div className="indicator-header">
              <div className="indicator-title">{indicator.title}</div>
              <div className="indicator-value">{indicator.currentValue}</div>
            </div>
            <div className="indicator-description">{indicator.description || 'Description not available'}</div>
            <div className="indicator-chart">
                {(() => {
                  // Always use collapsed data in default card view
                  const chartDataToUse = indicator.chartData;
                  const originalDataToUse = indicator.chartDataOriginal;
                  const datesToUse = indicator.chartDates;
                  
                  // Generate x-axis labels showing years
                  const generateXAxisLabels = () => {
                    if (!datesToUse || datesToUse.length === 0) {
                      // Fallback to index-based labels
                      const numPoints = chartDataToUse.length;
                      return [
                        { position: 50, label: Math.floor(numPoints / 2).toString() },
                        { position: 100, label: (numPoints - 1).toString() }
                      ];
                    }
                    
                    // Extract unique years from dates
                    const years = [...new Set(datesToUse.map(date => new Date(date).getFullYear()))].sort();
                    const labels = [];
                    
                    if (years.length === 0) return labels;
                    
                    // Find positions for each year, skipping the first one
                    years.slice(1).forEach((year, yearIdx) => {
                      // Find first occurrence of this year
                      const firstIndex = datesToUse.findIndex(date => new Date(date).getFullYear() === year);
                      if (firstIndex !== -1) {
                        const position = (firstIndex / (datesToUse.length - 1)) * 100;
                        labels.push({
                          position: position,
                          label: year.toString()
                        });
                      }
                    });
                    
                    return labels;
                  };
                  
                  // Generate y-axis labels with 5 clean intervals
                  const generateYAxisLabels = () => {
                    if (!originalDataToUse || originalDataToUse.length === 0) {
                      // Fallback to normalized values
                      return [
                        { position: 0, label: '100' },
                        { position: 25, label: '75' },
                        { position: 50, label: '50' },
                        { position: 75, label: '25' },
                        { position: 100, label: '0' }
                      ];
                    }
                    
                    const rawMin = Math.min(...originalDataToUse);
                    const rawMax = Math.max(...originalDataToUse);
                    const rawRange = rawMax - rawMin;
                    
                    // Round min down and max up to nice numbers for display labels
                    // Determine rounding step based on range
                    let roundingStep;
                    if (rawRange <= 1) {
                      roundingStep = 0.1; // Round to 0.1 for very small ranges
                    } else if (rawRange <= 5) {
                      roundingStep = 0.5; // Round to 0.5 for small ranges
                    } else {
                      roundingStep = 1; // Round to whole numbers for larger ranges
                    }
                    
                    // Round min down and max up for clean label values
                    const displayMin = Math.floor(rawMin / roundingStep) * roundingStep;
                    const displayMax = Math.ceil(rawMax / roundingStep) * roundingStep;
                    const displayRange = displayMax - displayMin;
                    
                    // Calculate 5 evenly spaced values for labels
                    const step = displayRange / 4; // 4 steps between 5 labels
                    const labels = [];
                    
                    // IMPORTANT: Data normalization uses rawMin/rawMax, not displayMin/displayMax
                    // Formula: ((val - rawMin) / rawRange) * 80 + 10
                    // So Y-axis label positions must use rawMin/rawRange to match data points
                    for (let i = 0; i < 5; i++) {
                      const value = displayMax - (step * i);
                      
                      // Round to clean number
                      let cleanValue;
                      if (roundingStep >= 1) {
                        cleanValue = Math.round(value);
                      } else if (roundingStep === 0.5) {
                        cleanValue = Math.round(value * 2) / 2;
                      } else {
                        cleanValue = Math.round(value * 10) / 10;
                      }
                      
                      // Calculate position using rawMin/rawRange to match data normalization
                      // Formula: position = 10 + ((cleanValue - rawMin) / rawRange) * 80
                      // But SVG Y-axis is inverted (0 at top, 100 at bottom), so: 100 - position
                      const normalizedPosition = rawRange === 0 ? 50 : 10 + ((cleanValue - rawMin) / rawRange) * 80;
                      const position = 100 - normalizedPosition; // Invert for SVG coordinates
                      
                      // Format based on rounding step and indicator type
                      let formattedLabel;
                      const isNFP = indicator.id === 'nonfarm-payrolls';
                      
                      if (isNFP) {
                        // Format as thousands (K) for NFP
                        formattedLabel = cleanValue.toFixed(0) + 'K';
                      } else {
                        // Format as percentage for other indicators
                        if (roundingStep >= 1) {
                          formattedLabel = cleanValue.toFixed(0) + '%';
                        } else if (roundingStep === 0.5) {
                          formattedLabel = cleanValue.toFixed(1) + '%';
                        } else {
                          formattedLabel = cleanValue.toFixed(1) + '%';
                        }
                      }
                      
                      labels.push({
                        position: position,
                        label: formattedLabel,
                        value: cleanValue
                      });
                    }
                    
                    // Add zero label if data crosses zero and zero is not already in the labels
                    if (rawMin < 0 && rawMax > 0) {
                      // Calculate zero position using rawMin/rawRange to match data normalization
                      const zeroNormalizedPosition = rawRange === 0 ? 50 : 10 + ((0 - rawMin) / rawRange) * 80;
                      const zeroPosition = 100 - zeroNormalizedPosition; // Invert for SVG
                      
                      // Check if zero is already close to one of the existing labels (within 2% position)
                      const hasZeroLabel = labels.some(label => Math.abs(label.position - zeroPosition) < 2);
                      
                      if (!hasZeroLabel) {
                        // Format zero label
                        const isNFP = indicator.id === 'nonfarm-payrolls';
                        const zeroLabel = isNFP ? '0K' : '0%';
                        
                        labels.push({
                          position: zeroPosition,
                          label: zeroLabel,
                          value: 0
                        });
                        
                        // Sort labels by position to maintain order
                        labels.sort((a, b) => a.position - b.position);
                      }
                    }
                    
                    return labels;
                  };
                  
                  const xAxisLabels = generateXAxisLabels();
                  const yAxisLabels = generateYAxisLabels();
                  
                  // Calculate 2% reference line position for inflation (not shown in default card view)
                  const getTargetLinePosition = () => {
                    return null; // Not shown in default card view
                  };

                  const getZeroLinePosition = () => {
                    if (!originalDataToUse || originalDataToUse.length === 0) {
                      return null;
                    }
                    
                    const rawMin = Math.min(...originalDataToUse);
                    const rawMax = Math.max(...originalDataToUse);
                    
                    // Only show zero line if data crosses zero (has both positive and negative values)
                    // or if zero is within a reasonable range of the data
                    if (rawMin > 0 && rawMax > 0) {
                      return null; // All values are positive, zero is below the chart
                    }
                    if (rawMin < 0 && rawMax < 0) {
                      return null; // All values are negative, zero is above the chart
                    }
                    
                    // Calculate Y position for 0 using rawMin/rawRange to match data normalization
                    // Data normalization uses: ((val - rawMin) / rawRange) * 80 + 10
                    const rawRange = rawMax - rawMin;
                    const zeroValue = 0;
                    
                    if (zeroValue < rawMin || zeroValue > rawMax) {
                      return null; // 0 is outside the visible range
                    }
                    
                    // Calculate normalized position in 10-90 range using rawMin/rawRange, then invert for SVG coordinates
                    const zeroNormalizedPosition = rawRange === 0 ? 50 : 10 + ((zeroValue - rawMin) / rawRange) * 80;
                    const yPosition = 100 - zeroNormalizedPosition; // Invert for SVG (0 at top, 100 at bottom)
                    return yPosition;
                  };
                  
                  const targetLineY = getTargetLinePosition();
                  const zeroLineY = getZeroLinePosition();
                  
                  return (
                    <div
                      className={`mini-chart${chartHover && chartHover.indicatorId === indicator.id ? ' chart-hover' : ''}`}
                      onMouseMove={(event) => handleChartHover(indicator.id, event, chartDataToUse, originalDataToUse)}
                      onMouseLeave={clearChartHover}
                    >
                <svg className="chart-line" viewBox="0 0 100 100" preserveAspectRatio="none">
                  <defs>
                    <linearGradient id={`chart-gradient-${indicator.id}`} x1="0%" y1="0%" x2="0%" y2="100%">
                      <stop offset="0%" stopColor="rgba(255, 59, 48, 0.4)" />
                      <stop offset="100%" stopColor="rgba(255, 59, 48, 0)" />
                    </linearGradient>
                  </defs>
                  {/* Grid lines - horizontal lines aligned with Y-axis labels */}
                  {yAxisLabels.map((label, idx) => (
                    <line 
                      key={`grid-h-${idx}`}
                      x1="0" 
                      y1={label.position} 
                      x2="100" 
                      y2={label.position} 
                      className="chart-grid-line"
                    />
                  ))}
                  {/* Grid lines - vertical lines (fixed positions for X-axis) */}
                  <line x1="0" y1="0" x2="0" y2="100" className="chart-grid-line" />
                  <line x1="25" y1="0" x2="25" y2="100" className="chart-grid-line" />
                  <line x1="50" y1="0" x2="50" y2="100" className="chart-grid-line" />
                  <line x1="75" y1="0" x2="75" y2="100" className="chart-grid-line" />
                  <line x1="100" y1="0" x2="100" y2="100" className="chart-grid-line" />
                  {/* Area fill */}
                  <path 
                    className="chart-area"
                    d={generateAreaPath(chartDataToUse)}
                    fill={`url(#chart-gradient-${indicator.id})`}
                  />
                  {/* Zero Line (all charts, when data crosses zero) */}
                  {zeroLineY !== null && (
                    <line 
                      x1="0" 
                      y1={zeroLineY} 
                      x2="100" 
                      y2={zeroLineY} 
                      className="chart-zero-line"
                    />
                  )}
                  {/* 2% Fed Target Line (inflation only, expanded only) */}
                  {targetLineY !== null && (
                    <line 
                      x1="0" 
                      y1={targetLineY} 
                      x2="100" 
                      y2={targetLineY} 
                      className="chart-target-line"
                    />
                  )}
                  {/* Multi-layer rendering: Glow/shadow layer (Method 5) */}
                  <path 
                    className="chart-path-glow"
                    d={generateLinePath(chartDataToUse)}
                  />
                  {/* Main line path */}
                  <path 
                    className="chart-path"
                    d={generateLinePath(chartDataToUse)}
                  />
                </svg>
                <div className="chart-dots">
                        {generateDotPositions(chartDataToUse).map((position, index) => (
                    <div 
                      key={index}
                            className={`chart-dot${
                              chartHover &&
                              chartHover.indicatorId === indicator.id &&
                              chartHover.index === index
                                ? ' active'
                                : ''
                            }`}
                      style={{
                        left: `${position.x}%`,
                        top: `${position.y}%`
                      }}
                    />
                  ))}
                </div>
                <div className="chart-axes">
                  <div className="chart-axis chart-axis-x"></div>
                  <div className="chart-axis chart-axis-y"></div>
                </div>
                <div className="chart-labels">
                        {xAxisLabels.map((label, idx) => (
                          <div 
                            key={idx}
                            className="chart-label-x" 
                            style={{ left: `${label.position}%` }}
                          >
                            {label.label}
                </div>
                        ))}
                        {yAxisLabels.map((label, idx) => (
                          <div 
                            key={`y-${idx}`}
                            className="chart-label-y" 
                            style={{ top: `${label.position}%` }}
                          >
                            {label.label}
              </div>
                        ))}
                      </div>
                      {/* 2% Target Label (Fed for US, BoJ for Japan, ECB for EUR) */}
                      {targetLineY !== null && (
                        <div 
                          className="chart-target-label"
                          style={{
                            top: `${targetLineY}%`,
                            right: '12px'
                          }}
                        >
                          {selectedEconomy === 'US' ? 'Fed 2% Target' : selectedEconomy === 'JPY' ? 'BoJ 2% Target' : selectedEconomy === 'EUR' ? 'ECB 2% Target' : selectedEconomy === 'GBP' ? 'BoE 2% Target' : '2% Target'}
                        </div>
                      )}
                      {chartHover && chartHover.indicatorId === indicator.id && (
                        <div
                          className={`chart-tooltip chart-tooltip-${chartHover.position || 'top'}`}
                          style={{
                            left: `${chartHover.xPercent}%`,
                            top: `${chartHover.yPercent}%`,
                          }}
                        >
                          <div className="chart-tooltip-value">
                            {typeof chartHover.value === 'number'
                              ? (indicator.id === 'nonfarm-payrolls' 
                                  ? chartHover.value.toFixed(0) + 'K'
                                  : chartHover.value.toFixed(2) + '%')
                              : chartHover.value}
                            {chartHover.trend && (
                              <span className={`chart-tooltip-trend chart-tooltip-trend-${chartHover.trend}`}>
                                {chartHover.trend === 'up' ? '↑' : chartHover.trend === 'down' ? '↓' : '→'}
                              </span>
                            )}
                          </div>
                          {chartHover.changePercent && chartHover.trend && (
                            <div className="chart-tooltip-change">
                              {chartHover.trend === 'up' ? '+' : ''}{chartHover.changePercent}%
                            </div>
                          )}
                          {datesToUse && datesToUse[chartHover.index] ? (
                            <div className="chart-tooltip-date">
                              {new Date(datesToUse[chartHover.index]).toLocaleDateString('en-US', { 
                                month: 'short', 
                                day: 'numeric', 
                                year: 'numeric' 
                              })}
                            </div>
                          ) : (
                            <div className="chart-tooltip-index">Point {chartHover.index + 1}</div>
                          )}
                        </div>
                      )}
                </div>
                  );
                })()}
              <div className="chart-label">{indicator.chartLabel}</div>
            </div>
          </div>
          );
        })}
      </div>

      {/* Modal Overlay for Expanded Card */}
      {expandedIndicatorId && (() => {
        const expandedIndicator = data.indicators.find(ind => ind.id === expandedIndicatorId);
        if (!expandedIndicator) return null;
        
        const isLoading = loadingIndicatorId === expandedIndicatorId;
        const insightItems = getIndicatorInsights(expandedIndicator, selectedEconomy) || [];
        const { overview, measurement, impact, context, traderImplications } = getIndicatorDetails(expandedIndicator, selectedEconomy);
        
        // Get accurate quick reference data based on indicator
        const getQuickReferenceData = (indicator) => {
          const baseData = {
            currentValue: indicator.currentValue,
            indicator: indicator.title,
            lastUpdated: indicator.asOf || null,
            frequency: indicator.frequency || null,
            unit: indicator.unit || null,
          };
          
          // Add indicator-specific data for US economy
          if (selectedEconomy === 'US') {
          if (indicator.id === 'interest-rate') {
            return {
              ...baseData,
              // Use actual currentValue from indicator data, not hardcoded
              lastChange: '25 bps cut',
              policyStance: 'Cautious easing',
              meetingFrequency: '8 times per year',
              nextAction: 'Markets price 1–3 additional cuts',
              keyDate: 'FOMC meetings',
            };
          }
          
          if (indicator.id === 'inflation-YoY') {
            return {
              ...baseData,
              target: 'Fed 2% target',
              trend: 'Moderating',
              lastReading: '3.0% (Sept 2025)',
              releaseDate: '10th-15th of each month',
            };
          }
          
          if (indicator.id === 'core-inflation-YoY') {
            return {
              ...baseData,
              target: 'Fed 2% target',
              trend: 'Moderating',
              lastReading: '3.0% (Sept 2025)',
              releaseDate: '10th-15th of each month',
              note: 'Fed\'s preferred gauge',
            };
          }
          
          if (indicator.id === 'gdp-growth') {
            return {
              ...baseData,
              lastReading: '3.8% (Q2 2025)',
              previousReading: '-0.6% (Q1 2025)',
              trend: 'Rebounding',
              releaseDate: 'End of month (quarterly)',
            };
          }
          
          if (indicator.id === 'unemployment') {
            return {
              ...baseData,
              lastReading: '4.4% (Sept 2025)',
              trend: 'Gradually increasing',
              releaseDate: 'First Friday of month',
              keyDate: 'NFP release day',
            };
          }
          
          if (indicator.id === 'nonfarm-payrolls') {
            return {
              ...baseData,
              lastReading: '119K (Sept 2025)',
              previousReading: '-4K (Aug 2025)',
              releaseDate: 'First Friday of month',
              releaseTime: '8:30 AM ET',
              impact: 'Highest-impact release',
            };
            }
          }
          
          // Add indicator-specific data for EUR economy
          if (selectedEconomy === 'EUR') {
            if (indicator.id === 'interest-rate') {
              return {
                ...baseData,
                lastChange: 'Paused after cuts',
                policyStance: 'Broadly neutral',
                meetingFrequency: '≈8 times per year',
                nextAction: 'Markets price stability through 2026',
                keyDate: 'ECB Governing Council meetings',
                note: 'Main Refinancing Rate: 2.15%',
              };
            }
            
            if (indicator.id === 'inflation') {
              return {
                ...baseData,
                target: 'ECB 2% target',
                trend: 'Stabilized near target',
                lastReading: '2.1% YoY (latest)',
                previousReading: 'Declining from peaks',
                releaseDate: 'Middle of each month',
                note: 'HICP - ECB\'s primary gauge',
              };
            }
            
            if (indicator.id === 'core-inflation-YoY') {
              return {
                ...baseData,
                target: 'ECB 2% target',
                trend: 'Stabilized',
                lastReading: '2.4% (Nov 2025)',
                releaseDate: 'Middle of each month',
                note: 'ECB\'s preferred gauge',
              };
            }
            
            if (indicator.id === 'gdp-growth') {
              return {
                ...baseData,
                lastReading: '+0.3% QoQ, ~1.4% YoY (Q3 2025)',
                previousReading: 'Q2 2025',
                trend: 'Moderate expansion',
                releaseDate: 'End of month (quarterly)',
                note: 'Eurostat / ECB projections',
              };
            }
            
            if (indicator.id === 'unemployment') {
              return {
                ...baseData,
                lastReading: '6.4% (Oct 2025)',
                previousReading: '6.4% (Sept 2025)',
                trend: 'Stable, slight YoY increase',
                releaseDate: 'Around 2nd of each month',
                note: 'Eurostat, seasonally adjusted',
              };
            }
            
            if (indicator.id === 'current-account') {
              return {
                ...baseData,
                lastReading: '€26B (Oct 2025)',
                previousReading: '€24B (Sept 2025)',
                trend: 'Narrowing surplus',
                releaseDate: '~6 weeks after reference month',
                note: '12-month: €313B (2.0% of GDP)',
              };
            }
          }
          
          // Add indicator-specific data for GBP economy
          if (selectedEconomy === 'GBP') {
            if (indicator.id === 'interest-rate') {
              return {
                ...baseData,
                lastChange: '25 bps cut (Dec 18, 2025)',
                policyStance: 'Shift toward easing',
                meetingFrequency: '≈Every 6 weeks',
                nextAction: 'Markets price additional cuts into 2026',
                keyDate: 'MPC meetings',
                note: 'Bank Rate - Lowest since Feb 2023',
              };
            }
            
            if (indicator.id === 'inflation') {
              return {
                ...baseData,
                target: 'BoE 2% target',
                trend: 'Declining',
                lastReading: '3.2% (Nov 2025)',
                previousReading: '3.6% (Oct 2025)',
                releaseDate: 'Middle of following month',
                note: 'CPI - BoE\'s primary target',
              };
            }
            
            if (indicator.id === 'core-inflation-YoY') {
              return {
                ...baseData,
                target: 'BoE 2% target',
                trend: 'Declining',
                lastReading: '3.2% (Nov 2025)',
                previousReading: '3.4% (Oct 2025)',
                releaseDate: 'Middle of following month',
                note: 'BoE\'s preferred gauge',
              };
            }
            
            if (indicator.id === 'gdp-growth') {
              return {
                ...baseData,
                lastReading: '+0.3% QoQ (Q2 2025)',
                previousReading: '+0.7% QoQ (Q1 2025)',
                trend: 'Moderating from Q1 strength',
                releaseDate: 'End of month following quarter',
                note: '2024: +1.1% (revised up from 0.9%)',
              };
            }
            
            if (indicator.id === 'unemployment') {
              return {
                ...baseData,
                lastReading: '5.1% (3m to Oct 2025)',
                previousReading: '4.4% (3m to Oct 2024)',
                trend: 'Rising, cooling labor market',
                releaseDate: 'Middle of following month',
                note: 'Highest since Jan 2021',
              };
            }
            
            if (indicator.id === 'wage-growth') {
              return {
                ...baseData,
                lastReading: '4.6% (3m to Oct 2025)',
                previousReading: '4.7% (previous quarter)',
                trend: 'Moderating, lowest in 3+ years',
                releaseDate: 'Middle of following month',
                note: 'Public: 7.6%, Private: 3.9%',
              };
            }
          }
          
          // Add indicator-specific data for JPY economy
          if (selectedEconomy === 'JPY') {
            if (indicator.id === 'interest-rate') {
              return {
                ...baseData,
                lastChange: '25 bps hike (Dec 19, 2025)',
                policyStance: 'Normalization',
                meetingFrequency: '≈Every 6 weeks',
                nextAction: 'Markets price additional normalization into 2026',
                keyDate: 'Policy Board meetings',
                note: 'Highest since Sept 1995',
              };
            }
            
            if (indicator.id === 'inflation') {
              return {
                ...baseData,
                target: 'BoJ 2% target',
                trend: 'Above target, sustained',
                lastReading: '3.0% (Nov 2025)',
                previousReading: '3.0% (Oct 2025)',
                releaseDate: 'End of following month',
                note: 'Tokyo Core: 2.3% (Dec 2025)',
              };
            }
            
            if (indicator.id === 'core-inflation-YoY') {
              return {
                ...baseData,
                target: 'BoJ 2% target',
                trend: 'Above target, moderating',
                lastReading: '3.0% (Nov 2025)',
                previousReading: '3.0% (Oct 2025)',
                releaseDate: 'End of following month',
                note: 'Tokyo Core: 2.3% (Dec 2025)',
              };
            }
            
            if (indicator.id === 'gdp-growth') {
              return {
                ...baseData,
                lastReading: '-2.3% annualized (Q3 2025)',
                previousReading: '+2.2% annualized (Q2 2025)',
                trend: 'Volatile, first contraction in 6 quarters',
                releaseDate: 'End of month following quarter',
                note: '2024: +0.1%',
              };
            }
            
            if (indicator.id === 'unemployment') {
              return {
                ...baseData,
                lastReading: '2.6% (Nov 2025)',
                previousReading: '2.6% (Oct 2025)',
                trend: 'Stable, highest since July 2024',
                releaseDate: 'End of following month',
                note: 'Jobs-to-applicants: 1.18',
              };
            }
            
            if (indicator.id === 'trade-balance') {
              return {
                ...baseData,
                lastReading: '¥4.06T (Feb 2025)',
                previousReading: '¥257.6B deficit (Jan 2025)',
                trend: 'Volatile, record FY2024 surplus',
                releaseDate: '~6 weeks after reference month',
                note: 'FY2024: ¥30.4T (record high)',
              };
            }
          }
          
          // Return base data for all other cases
          return baseData;
        };
        
        const quickRefData = getQuickReferenceData(expandedIndicator);
        
        return (
          <div 
            className="indicator-modal-overlay"
            onClick={closeExpandedCard}
          >
            <div 
              className="indicator-modal-content"
              onClick={(e) => e.stopPropagation()}
            >
              <button 
                className="indicator-modal-close"
                onClick={closeExpandedCard}
                aria-label="Close"
              >
                ×
              </button>
              
              <div className="indicator-modal-header">
                <div className="indicator-modal-title">{expandedIndicator.title}</div>
                <div className="indicator-modal-value">{expandedIndicator.currentValue}</div>
              </div>
              
              <div className="indicator-modal-description">{expandedIndicator.description || 'Description not available'}</div>
              
              <div className="indicator-modal-chart">
                {(() => {
                  const originalDataToUse = expandedIndicator.chartDataOriginalAll || expandedIndicator.chartDataOriginal;
                  const datesToUse = expandedIndicator.chartDatesAll || expandedIndicator.chartDates;
                  
                  // Check if we need to show 2% target line and if 2% is outside data range
                  const isInflationIndicator = expandedIndicator.id === 'inflation-YoY' || 
                                              expandedIndicator.id === 'inflation' || 
                                              expandedIndicator.id === 'core-inflation-YoY';
                  const needsTargetLine = isInflationIndicator && originalDataToUse && originalDataToUse.length > 0;
                  
                  // Re-normalize data to include 2% in range if target line is needed and 2% is outside range
                  let chartDataToUse;
                  if (needsTargetLine && originalDataToUse) {
                    const rawMin = Math.min(...originalDataToUse);
                    const rawMax = Math.max(...originalDataToUse);
                    const targetValue = 2.0;
                    
                    // If 2% is outside the data range, extend the normalization range to include it
                    if (targetValue < rawMin || targetValue > rawMax) {
                      const extendedMin = Math.min(rawMin, targetValue);
                      const extendedMax = Math.max(rawMax, targetValue);
                      const extendedRange = extendedMax - extendedMin;
                      
                      // Re-normalize using extended range
                      chartDataToUse = originalDataToUse.map((val) => 
                        extendedRange === 0 ? 50 : ((val - extendedMin) / extendedRange) * 80 + 10
                      );
                    } else {
                      // Use already normalized data
                      chartDataToUse = expandedIndicator.chartDataExpanded || expandedIndicator.chartData;
                    }
                  } else {
                    // Use already normalized data
                    chartDataToUse = expandedIndicator.chartDataExpanded || expandedIndicator.chartData;
                  }
                  
                  // Generate x-axis labels showing more dates in expanded modal
                  const generateXAxisLabels = () => {
                    if (!datesToUse || datesToUse.length === 0) {
                      const numPoints = chartDataToUse.length;
                      return [
                        { position: 50, label: Math.floor(numPoints / 2).toString() },
                        { position: 100, label: (numPoints - 1).toString() }
                      ];
                    }
                    
                    const labels = [];
                    const totalPoints = datesToUse.length;
                    
                    // Show more labels in expanded state - every 3-4 data points or key dates
                    // First, get all unique year-month combinations
                    const dateMap = new Map();
                    datesToUse.forEach((dateStr, index) => {
                      const date = new Date(dateStr);
                      const year = date.getFullYear();
                      const month = date.getMonth();
                      const key = `${year}-${month}`;
                      
                      if (!dateMap.has(key)) {
                        dateMap.set(key, { index, year, month, date });
                      }
                    });
                    
                    // Determine interval based on data length
                    let interval;
                    if (totalPoints <= 12) {
                      interval = 2; // Show every 2nd point for small datasets
                    } else if (totalPoints <= 24) {
                      interval = 3; // Show every 3rd point
                    } else {
                      interval = 4; // Show every 4th point for larger datasets
                    }
                    
                    // Add labels at regular intervals
                    for (let i = 0; i < totalPoints; i += interval) {
                      if (i < totalPoints) {
                        const date = new Date(datesToUse[i]);
                        const year = date.getFullYear();
                        const month = date.getMonth();
                        const monthName = date.toLocaleDateString('en-US', { month: 'short' });
                        
                        // Format: "Jan 2024" or just year if it's the first occurrence of that year
                        const isFirstOfYear = i === 0 || new Date(datesToUse[i - 1]).getFullYear() !== year;
                        const label = isFirstOfYear ? `${monthName} ${year}` : monthName;
                        
                        const position = (i / (totalPoints - 1)) * 100;
                        labels.push({ position, label });
                      }
                    }
                    
                    // Always include the last data point
                    if (totalPoints > 0) {
                      const lastIndex = totalPoints - 1;
                      const lastDate = new Date(datesToUse[lastIndex]);
                      const lastYear = lastDate.getFullYear();
                      const lastMonth = lastDate.toLocaleDateString('en-US', { month: 'short' });
                      
                      // Check if last point is already included
                      const lastIncluded = labels.some(l => Math.abs(l.position - 100) < 1);
                      if (!lastIncluded) {
                        labels.push({ position: 100, label: `${lastMonth} ${lastYear}` });
                      }
                    }
                    
                    return labels;
                  };
                  
                  // Generate y-axis labels with 5 clean intervals
                  const generateYAxisLabels = () => {
                    if (!originalDataToUse || originalDataToUse.length === 0) {
                      return [
                        { position: 0, label: '100' },
                        { position: 25, label: '75' },
                        { position: 50, label: '50' },
                        { position: 75, label: '25' },
                        { position: 100, label: '0' }
                      ];
                    }
                    
                    const rawMin = Math.min(...originalDataToUse);
                    const rawMax = Math.max(...originalDataToUse);
                    const rawRange = rawMax - rawMin;
                    
                    let roundingStep;
                    if (rawRange <= 1) {
                      roundingStep = 0.1;
                    } else if (rawRange <= 5) {
                      roundingStep = 0.5;
                    } else {
                      roundingStep = 1;
                    }
                    
                    // Round min down and max up for clean label values
                    const displayMin = Math.floor(rawMin / roundingStep) * roundingStep;
                    const displayMax = Math.ceil(rawMax / roundingStep) * roundingStep;
                    const displayRange = displayMax - displayMin;
                    const step = displayRange / 4;
                    const labels = [];
                    
                    // IMPORTANT: Data normalization uses rawMin/rawMax, not displayMin/displayMax
                    // Formula: ((val - rawMin) / rawRange) * 80 + 10
                    // So Y-axis label positions must use rawMin/rawRange to match data points
                    for (let i = 0; i < 5; i++) {
                      const value = displayMax - (step * i);
                      
                      let cleanValue;
                      if (roundingStep >= 1) {
                        cleanValue = Math.round(value);
                      } else if (roundingStep === 0.5) {
                        cleanValue = Math.round(value * 2) / 2;
                      } else {
                        cleanValue = Math.round(value * 10) / 10;
                      }
                      
                      // Calculate position using rawMin/rawRange to match data normalization
                      // Formula: position = 10 + ((cleanValue - rawMin) / rawRange) * 80
                      // But SVG Y-axis is inverted (0 at top, 100 at bottom), so: 100 - position
                      const normalizedPosition = rawRange === 0 ? 50 : 10 + ((cleanValue - rawMin) / rawRange) * 80;
                      const position = 100 - normalizedPosition; // Invert for SVG coordinates
                      
                      let formattedLabel;
                      const isNFP = expandedIndicator.id === 'nonfarm-payrolls';
                      
                      if (isNFP) {
                        formattedLabel = cleanValue.toFixed(0) + 'K';
                      } else {
                        if (roundingStep >= 1) {
                          formattedLabel = cleanValue.toFixed(0) + '%';
                        } else if (roundingStep === 0.5) {
                          formattedLabel = cleanValue.toFixed(1) + '%';
                        } else {
                          formattedLabel = cleanValue.toFixed(1) + '%';
                        }
                      }
                      
                      labels.push({ position, label: formattedLabel, value: cleanValue });
                    }
                    
                    // Add zero label if data crosses zero
                    if (rawMin < 0 && rawMax > 0) {
                      // Calculate zero position using rawMin/rawRange to match data normalization
                      const zeroNormalizedPosition = rawRange === 0 ? 50 : 10 + ((0 - rawMin) / rawRange) * 80;
                      const zeroPosition = 100 - zeroNormalizedPosition; // Invert for SVG
                      const hasZeroLabel = labels.some(label => Math.abs(label.position - zeroPosition) < 2);
                      
                      if (!hasZeroLabel) {
                        const isNFP = expandedIndicator.id === 'nonfarm-payrolls';
                        const zeroLabel = isNFP ? '0K' : '0%';
                        labels.push({ position: zeroPosition, label: zeroLabel, value: 0 });
                        labels.sort((a, b) => a.position - b.position);
                      }
                    }
                    
                    return labels;
                  };
                  
                  const getTargetLinePosition = () => {
                    // Show 2% target line for inflation indicators (both US Fed and Japan BoJ target 2%)
                    // US uses 'inflation-YoY' and 'core-inflation-YoY', Japan uses 'inflation' and 'core-inflation-YoY'
                    const isInflationIndicator = expandedIndicator.id === 'inflation-YoY' || 
                                                  expandedIndicator.id === 'inflation' || 
                                                  expandedIndicator.id === 'core-inflation-YoY';
                    if (!isInflationIndicator || !originalDataToUse || originalDataToUse.length === 0) {
                      return null;
                    }
                    
                    // Use the SAME normalization as the actual data points
                    // Data normalization uses: ((val - rawMin) / rawRange) * 80 + 10
                    const rawMin = Math.min(...originalDataToUse);
                    const rawMax = Math.max(...originalDataToUse);
                    const rawRange = rawMax - rawMin;
                    const targetValue = 2.0;
                    
                    // If 2% is outside the data range, we need to extend the range for accurate positioning
                    // But we must use the same formula as data normalization
                    if (targetValue < rawMin || targetValue > rawMax) {
                      // Extend range to include 2% for positioning calculation
                    const extendedMin = Math.min(rawMin, targetValue);
                    const extendedMax = Math.max(rawMax, targetValue);
                    const extendedRange = extendedMax - extendedMin;
                    
                      // Calculate position using extended range, matching the normalization formula
                    const targetNormalizedPosition = extendedRange === 0 ? 50 : 10 + ((targetValue - extendedMin) / extendedRange) * 80;
                      return 100 - targetNormalizedPosition; // Invert for SVG (0 at top, 100 at bottom)
                    }
                    
                    // If 2% is within the data range, use the same rawMin/rawRange as data normalization
                    const targetNormalizedPosition = rawRange === 0 ? 50 : 10 + ((targetValue - rawMin) / rawRange) * 80;
                    
                    return 100 - targetNormalizedPosition; // Invert for SVG (0 at top, 100 at bottom)
                  };

                  const getZeroLinePosition = () => {
                    if (!originalDataToUse || originalDataToUse.length === 0) {
                      return null;
                    }
                    
                    const rawMin = Math.min(...originalDataToUse);
                    const rawMax = Math.max(...originalDataToUse);
                    const rawRange = rawMax - rawMin;
                    
                    if (rawMin > 0 && rawMax > 0) return null;
                    if (rawMin < 0 && rawMax < 0) return null;
                    
                    const zeroValue = 0;
                    
                    if (zeroValue < rawMin || zeroValue > rawMax) {
                      return null;
                    }
                    
                    // Calculate normalized position using rawMin/rawRange to match data normalization
                    // Data normalization uses: ((val - rawMin) / rawRange) * 80 + 10
                    const zeroNormalizedPosition = rawRange === 0 ? 50 : 10 + ((zeroValue - rawMin) / rawRange) * 80;
                    return 100 - zeroNormalizedPosition; // Invert for SVG (0 at top, 100 at bottom)
                  };
                  
                  const xAxisLabels = generateXAxisLabels();
                  const yAxisLabels = generateYAxisLabels();
                  const targetLineY = getTargetLinePosition();
                  const zeroLineY = getZeroLinePosition();
                  
                  return (
                    <div
                      className={`mini-chart expanded${chartHover && chartHover.indicatorId === expandedIndicator.id ? ' chart-hover' : ''}`}
                      onMouseMove={(event) => handleChartHover(expandedIndicator.id, event, chartDataToUse, originalDataToUse)}
                      onMouseLeave={clearChartHover}
                    >
                      <svg className="chart-line" viewBox="0 0 100 100" preserveAspectRatio="none">
                        <defs>
                          <linearGradient id={`chart-gradient-modal-${expandedIndicator.id}`} x1="0%" y1="0%" x2="0%" y2="100%">
                            <stop offset="0%" stopColor="rgba(255, 59, 48, 0.4)" />
                            <stop offset="100%" stopColor="rgba(255, 59, 48, 0)" />
                          </linearGradient>
                        </defs>
                        {/* Grid lines - horizontal lines aligned with Y-axis labels */}
                        {yAxisLabels.map((label, idx) => (
                          <line 
                            key={`grid-h-${idx}`}
                            x1="0" 
                            y1={label.position} 
                            x2="100" 
                            y2={label.position} 
                            className="chart-grid-line"
                          />
                        ))}
                        {/* Grid lines - vertical lines (fixed positions for X-axis) */}
                        <line x1="0" y1="0" x2="0" y2="100" className="chart-grid-line" />
                        <line x1="25" y1="0" x2="25" y2="100" className="chart-grid-line" />
                        <line x1="50" y1="0" x2="50" y2="100" className="chart-grid-line" />
                        <line x1="75" y1="0" x2="75" y2="100" className="chart-grid-line" />
                        <line x1="100" y1="0" x2="100" y2="100" className="chart-grid-line" />
                        {/* Area fill */}
                        <path 
                          className="chart-area"
                          d={generateAreaPath(chartDataToUse)}
                          fill={`url(#chart-gradient-modal-${expandedIndicator.id})`}
                        />
                        {/* Zero Line */}
                        {zeroLineY !== null && (
                          <line x1="0" y1={zeroLineY} x2="100" y2={zeroLineY} className="chart-zero-line" />
                        )}
                        {/* 2% Fed Target Line */}
                        {targetLineY !== null && (
                          <line x1="0" y1={targetLineY} x2="100" y2={targetLineY} className="chart-target-line" />
                        )}
                        {/* Multi-layer rendering */}
                        <path className="chart-path-glow" d={generateLinePath(chartDataToUse)} />
                        <path className="chart-path" d={generateLinePath(chartDataToUse)} />
                        {/* Crosshair lines - only in expanded modal */}
                        {chartHover && chartHover.indicatorId === expandedIndicator.id && (() => {
                          // Calculate exact dot position for vertical line alignment
                          const lastIndex = chartDataToUse.length - 1;
                          const exactXPercent = lastIndex === 0 ? 0 : (chartHover.index / lastIndex) * 100;
                          const exactYPercent = 100 - chartDataToUse[chartHover.index];
                          
                          return (
                            <>
                              {/* Vertical crosshair line - aligned with exact dot position */}
                              <line 
                                x1={exactXPercent} 
                                y1="0" 
                                x2={exactXPercent} 
                                y2="100" 
                                className="chart-crosshair-line chart-crosshair-vertical"
                              />
                              {/* Horizontal crosshair line - aligned with exact dot position */}
                              <line 
                                x1="0" 
                                y1={exactYPercent} 
                                x2="100" 
                                y2={exactYPercent} 
                                className="chart-crosshair-line chart-crosshair-horizontal"
                              />
                            </>
                          );
                        })()}
                      </svg>
                      <div className="chart-dots">
                        {generateDotPositions(chartDataToUse).map((position, index) => (
                          <div 
                            key={index}
                            className={`chart-dot${
                              chartHover &&
                              chartHover.indicatorId === expandedIndicator.id &&
                              chartHover.index === index ? ' active' : ''
                            }`}
                            style={{ left: `${position.x}%`, top: `${position.y}%` }}
                          />
                        ))}
                      </div>
                      <div className="chart-axes">
                        <div className="chart-axis chart-axis-x"></div>
                        <div className="chart-axis chart-axis-y"></div>
                      </div>
                      <div className="chart-labels">
                        {xAxisLabels.map((label, idx) => (
                          <div key={idx} className="chart-label-x" style={{ left: `${label.position}%` }}>
                            {label.label}
                          </div>
                        ))}
                        {yAxisLabels.map((label, idx) => (
                          <div key={`y-${idx}`} className="chart-label-y" style={{ top: `${label.position}%` }}>
                            {label.label}
                          </div>
                        ))}
                      </div>
                      {/* 2% Target Label (Fed for US, BoJ for Japan) */}
                      {targetLineY !== null && (
                        <div className="chart-target-label" style={{ top: `${targetLineY}%`, right: '12px' }}>
                          {selectedEconomy === 'US' ? 'Fed 2% Target' : selectedEconomy === 'JPY' ? 'BoJ 2% Target' : selectedEconomy === 'EUR' ? 'ECB 2% Target' : selectedEconomy === 'GBP' ? 'BoE 2% Target' : '2% Target'}
                        </div>
                      )}
                      {chartHover && chartHover.indicatorId === expandedIndicator.id && (
                        <div
                          className={`chart-tooltip chart-tooltip-${chartHover.position || 'top'}`}
                          style={{ left: `${chartHover.xPercent}%`, top: `${chartHover.yPercent}%` }}
                        >
                          <div className="chart-tooltip-value">
                            {typeof chartHover.value === 'number'
                              ? (expandedIndicator.id === 'nonfarm-payrolls' 
                                  ? chartHover.value.toFixed(0) + 'K'
                                  : chartHover.value.toFixed(2) + '%')
                              : chartHover.value}
                            {chartHover.trend && (
                              <span className={`chart-tooltip-trend chart-tooltip-trend-${chartHover.trend}`}>
                                {chartHover.trend === 'up' ? '↑' : chartHover.trend === 'down' ? '↓' : '→'}
                              </span>
                            )}
                          </div>
                          {chartHover.changePercent && chartHover.trend && (
                            <div className="chart-tooltip-change">
                              {chartHover.trend === 'up' ? '+' : ''}{chartHover.changePercent}%
                            </div>
                          )}
                          {datesToUse && datesToUse[chartHover.index] ? (
                            <div className="chart-tooltip-date">
                              {new Date(datesToUse[chartHover.index]).toLocaleDateString('en-US', { 
                                month: 'short', day: 'numeric', year: 'numeric' 
                              })}
                            </div>
                          ) : (
                            <div className="chart-tooltip-index">Point {chartHover.index + 1}</div>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })()}
                <div className="chart-label">{expandedIndicator.chartLabel}</div>
              </div>
              
              {isLoading && (
                <div className="indicator-loading">
                  <div className="loading-spinner"></div>
                </div>
              )}
              
              <div className={`indicator-expanded-content ${isLoading ? 'loading' : ''}`}>
                <div className="indicator-expanded-main">
                <div className="indicator-expanded-section">
                  <div className="indicator-section-title">Key Insights</div>
                  <ul className="indicator-insights-list">
                    {insightItems.map((insight, index) => (
                      <li key={index} className="indicator-insight-item">
                        {insight}
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="indicator-expanded-section">
                  <div className="indicator-section-title">Indicator Overview</div>
                  <div className="indicator-section-text">
                    {renderParagraphs(overview)}
                  </div>
                </div>

                <div className="indicator-expanded-section">
                  <div className="indicator-section-title">How It's Measured</div>
                  <div className="indicator-section-text">
                    {renderParagraphs(measurement)}
                  </div>
                </div>

                <div className="indicator-expanded-section">
                  <div className="indicator-section-title">Currency & Market Impact</div>
                  <div className="indicator-section-text">
                    {renderParagraphs(impact)}
                  </div>
                </div>

                {context && (
                  <div className="indicator-expanded-section">
                    <div className="indicator-section-title">Current Policy Context – December 2025</div>
                    <div className="indicator-section-text">
                      {renderParagraphs(context)}
                    </div>
                  </div>
                )}

                {traderImplications && (
                  <div className="indicator-expanded-section">
                    <div className="indicator-section-title">What This Means for Traders</div>
                    <div className="indicator-section-text">
                      {renderParagraphs(traderImplications)}
                    </div>
                  </div>
                )}
                </div>

                <div className="indicator-expanded-sidebar">
                  <div className="indicator-sidebar-section">
                    <div className="indicator-sidebar-title">Quick Reference</div>
                    <div className="indicator-sidebar-item">
                      <span className="indicator-sidebar-label">Current Value</span>
                      <span className="indicator-sidebar-value highlight">{quickRefData.currentValue}</span>
                    </div>
                    {quickRefData.lastChange && (
                      <div className="indicator-sidebar-item">
                        <span className="indicator-sidebar-label">Last Change</span>
                        <span className="indicator-sidebar-value">{quickRefData.lastChange}</span>
                      </div>
                    )}
                    {quickRefData.policyStance && (
                      <div className="indicator-sidebar-item">
                        <span className="indicator-sidebar-label">Policy Stance</span>
                        <span className="indicator-sidebar-value">{quickRefData.policyStance}</span>
                      </div>
                    )}
                    {quickRefData.trend && (
                      <div className="indicator-sidebar-item">
                        <span className="indicator-sidebar-label">Trend</span>
                        <span className="indicator-sidebar-value">{quickRefData.trend}</span>
                      </div>
                    )}
                    {quickRefData.lastReading && (
                      <div className="indicator-sidebar-item">
                        <span className="indicator-sidebar-label">Last Reading</span>
                        <span className="indicator-sidebar-value">{quickRefData.lastReading}</span>
                      </div>
                    )}
                    {quickRefData.previousReading && (
                      <div className="indicator-sidebar-item">
                        <span className="indicator-sidebar-label">Previous</span>
                        <span className="indicator-sidebar-value">{quickRefData.previousReading}</span>
                      </div>
                    )}
                    {quickRefData.target && (
                      <div className="indicator-sidebar-item">
                        <span className="indicator-sidebar-label">Target</span>
                        <span className="indicator-sidebar-value">{quickRefData.target}</span>
                      </div>
                    )}
                    {quickRefData.meetingFrequency && (
                      <div className="indicator-sidebar-item">
                        <span className="indicator-sidebar-label">Meeting Frequency</span>
                        <span className="indicator-sidebar-value">{quickRefData.meetingFrequency}</span>
                      </div>
                    )}
                    {quickRefData.releaseDate && (
                      <div className="indicator-sidebar-item">
                        <span className="indicator-sidebar-label">Release Date</span>
                        <span className="indicator-sidebar-value">{quickRefData.releaseDate}</span>
                      </div>
                    )}
                    {quickRefData.releaseTime && (
                      <div className="indicator-sidebar-item">
                        <span className="indicator-sidebar-label">Release Time</span>
                        <span className="indicator-sidebar-value">{quickRefData.releaseTime}</span>
                      </div>
                    )}
                    {quickRefData.nextAction && (
                      <div className="indicator-sidebar-item">
                        <span className="indicator-sidebar-label">Market Expectation</span>
                        <span className="indicator-sidebar-value">{quickRefData.nextAction}</span>
                      </div>
                    )}
                    {quickRefData.impact && (
                      <div className="indicator-sidebar-item">
                        <span className="indicator-sidebar-label">Market Impact</span>
                        <span className="indicator-sidebar-value">{quickRefData.impact}</span>
                      </div>
                    )}
                    {quickRefData.note && (
                      <div className="indicator-sidebar-item">
                        <span className="indicator-sidebar-label">Note</span>
                        <span className="indicator-sidebar-value">{quickRefData.note}</span>
                      </div>
                    )}
                    {quickRefData.lastUpdated && (
                      <div className="indicator-sidebar-item">
                        <span className="indicator-sidebar-label">Last Updated</span>
                        <span className="indicator-sidebar-value">{quickRefData.lastUpdated}</span>
                      </div>
                    )}
                  </div>

                  {(expandedIndicator.source || expandedIndicator.sourceUrl) && (
                    <div className="indicator-sidebar-section">
                      <div className="indicator-sidebar-title">Data Source</div>
                      {expandedIndicator.source && (
                        <div className="indicator-sidebar-item">
                          <span className="indicator-sidebar-label">Source</span>
                          <span className="indicator-sidebar-value">
                            {expandedIndicator.sourceUrl ? (
                              <a 
                                href={expandedIndicator.sourceUrl} 
                                target="_blank" 
                                rel="noopener noreferrer"
                                className="source-link"
                              >
                                {expandedIndicator.source}
                              </a>
                            ) : (
                              expandedIndicator.source
                            )}
                          </span>
                        </div>
                      )}
                      {expandedIndicator.notes && (
                        <div className="indicator-sidebar-item">
                          <span className="indicator-sidebar-label">Notes</span>
                          <span className="indicator-sidebar-value">{expandedIndicator.notes}</span>
                        </div>
                      )}
                  </div>
                )}
                </div>
              </div>
            </div>
          </div>
        );
      })()}

      <div className="economy-description">
        {data.description}
          </div>

      <div className="analysis-sections-container">
        <div className="economy-analysis" ref={analysisRef}>
          <h2 className="analysis-title">Hollistic Scan</h2>
          <p className="analysis-placeholder">Coming soon</p>
        </div>

        <div className="yield-indicators-section">
          <h2 className="analysis-title">Bond Indicators - More Coming Soon</h2>
          <p className="yield-subtext">Pick a bond/yield indicator from the list below.</p>
          <div className="yield-symbol-scroll" role="tablist" aria-label="Yield symbols by economy">
            {YIELD_ECONOMY_ORDER.map((economyCode) => {
              const group = YIELD_MARKETS.filter((m) => m.economy === economyCode);
              if (group.length === 0) return null;
              return (
                <div key={economyCode} className="yield-symbol-group" role="presentation">
                  <span className="yield-symbol-group-label" aria-hidden="true">
                    {economyCode}
                  </span>
                  {group.map((item) => (
                    <button
                      key={item.symbol}
                      type="button"
                      className={`yield-symbol-chip ${activeYieldSymbol === item.symbol ? 'active' : ''}`}
                      onClick={() => setActiveYieldSymbol(item.symbol)}
                      aria-selected={activeYieldSymbol === item.symbol}
                    >
                      <span className="yield-chip-economy">{item.economy}</span>
                      <span className="yield-chip-label">{item.label}</span>
                    </button>
                  ))}
                </div>
              );
            })}
          </div>
          <div className="yield-widget-card-single" onWheel={handleYieldWheel}>
            <TradingViewYieldWidget key={activeYield.symbol} symbol={activeYield.symbol} />
          </div>
        </div>
      </div>
    </div>
  );
}
