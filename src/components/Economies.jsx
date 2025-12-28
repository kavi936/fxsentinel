import React, { useMemo, useState, useEffect } from 'react';
import './Economies.css';
import economyIndicatorsData from '../data/economyIndicators.json';
import { config } from '../config';

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
      '• A [[macro regime filter]] (tightening vs easing)\n\n' +
      '• A [[USD directional bias tool]]\n\n' +
      '• A [[cross-asset sentiment anchor]]\n\n' +
      'Future enhancements may include:\n\n' +
      '• Market-implied rate path vs Fed guidance\n\n' +
      '• Bank forecast aggregation\n\n' +
      '• Political risk overlays\n\n' +
      '• Event-driven volatility flags',
  },
  'inflation-YoY': {
    overview:
      'The [[Consumer Price Index (CPI) Year-over-Year]] measures the annual percentage change in the price level of a basket of consumer goods and services. It is the [[primary inflation gauge]] used by the Federal Reserve and financial markets to assess price stability and purchasing power erosion.\n\n' +
      'For financial markets, inflation data is a [[critical input]] for monetary policy expectations, real yield calculations, and currency valuation models.\n\n' +
      'Why traders care:\n\n' +
      '• Directly influences [[Fed policy expectations]] and interest rate forecasts.\n\n' +
      '• Affects [[real yields]] (nominal rates minus inflation), which drive currency flows.\n\n' +
      '• Signals [[economic overheating]] or [[deflation risks]], impacting risk sentiment across asset classes.',
    measurement:
      'The [[Bureau of Labor Statistics (BLS)]] calculates CPI by tracking price changes for a representative basket of goods and services across urban consumers. The [[year-over-year (YoY)]] measure compares current prices to the same month in the previous year.\n\n' +
      'Two key variants are monitored:\n\n' +
      '• [[Headline CPI]]: Includes all items, including volatile food and energy components.\n\n' +
      '• [[Core CPI]]: Excludes food and energy to reveal underlying inflation trends.\n\n' +
      'Data is released monthly, typically around the [[10th-15th of each month]] for the previous month, with revisions possible in subsequent releases.',
    impact:
      'Inflation readings have [[profound implications]] for currency markets through multiple channels:\n\n' +
      '[[Elevated Inflation]]\n\n' +
      '• Can [[undermine currency]] by eroding real returns on dollar-denominated assets.\n\n' +
      '• If it prompts [[hawkish Fed response]] (rate hikes), the USD may strengthen despite initial weakness.\n\n' +
      '• Increases [[inflation expectations]], potentially steepening yield curves and supporting USD.\n\n' +
      '[[Moderate/Declining Inflation]]\n\n' +
      '• Relieves pressure on policymakers, potentially [[weakening USD]] if it leads to dovish policy.\n\n' +
      '• Supports [[real yield calculations]], making dollar assets more attractive if nominal rates hold.\n\n' +
      '• Can encourage [[risk-taking]] in carry trades if inflation remains contained.\n\n' +
      '[[Forward-looking dynamics]]: Markets react not just to current inflation but to [[trends and expectations]]. Persistent inflation above the Fed\'s 2% target can trigger policy responses that strengthen the USD, while disinflationary trends may support risk assets but pressure the dollar.',
    context:
      'U.S. inflation has shown [[gradual moderation]] from peak levels, with the latest reading at 3.0% YoY (September 2025). The path has been uneven, reflecting [[sticky services inflation]] alongside moderating goods prices.\n\n' +
      'Key themes shaping markets:\n\n' +
      '• [[Fed\'s 2% target]]: Core inflation remains above target, keeping policy makers cautious about premature easing.\n\n' +
      '• [[Services vs. goods]]: Services inflation has proven more persistent, driven by wage growth and housing costs.\n\n' +
      '• [[Policy implications]]: Current inflation levels allow for measured rate cuts but limit aggressive easing.\n\n' +
      '• [[Market sensitivity]]: Each CPI release triggers significant volatility as traders reassess Fed policy expectations.',
    traderImplications:
      '[[FX volatility]]: CPI releases are among the [[highest-impact economic events]], often causing sharp USD moves, especially in USD/JPY and EUR/USD pairs.\n\n' +
      '[[Real yield calculations]]: Inflation data directly affects real yield spreads, which drive [[carry trade flows]] and relative currency strength.\n\n' +
      '[[Cross-asset reactions]]: Inflation surprises can trigger simultaneous moves in [[bonds, equities, and commodities]] as markets reassess growth and policy outlooks.',
  },
  'gdp-growth': {
    overview:
      '[[Gross Domestic Product (GDP) Growth Rate]] measures the quarterly percentage change in real GDP (adjusted for inflation), representing the [[overall economic expansion or contraction]]. It aggregates activity across consumption, investment, government spending, and net trade.\n\n' +
      'For financial markets, GDP growth is a [[fundamental driver]] of currency strength, monetary policy expectations, and risk sentiment.\n\n' +
      'Why traders care:\n\n' +
      '• Signals [[economic health]] and growth momentum, directly influencing currency valuations.\n\n' +
      '• Affects [[monetary policy expectations]]: strong growth supports rate hikes, weak growth suggests easing.\n\n' +
      '• Drives [[capital flows]]: higher growth attracts foreign investment, strengthening the currency.',
    measurement:
      'The [[Bureau of Economic Analysis (BEA)]] calculates GDP growth as the percentage change in real GDP from one quarter to the previous quarter, [[annualized for comparability]]. The calculation uses chained dollars to adjust for inflation.\n\n' +
      'GDP is measured through three approaches:\n\n' +
      '• [[Expenditure approach]]: Sum of consumption, investment, government spending, and net exports.\n\n' +
      '• [[Income approach]]: Sum of all income earned in production.\n\n' +
      '• [[Production approach]]: Value added at each stage of production.\n\n' +
      'Data is released quarterly, typically around the [[end of the month]] following the quarter end, with [[multiple revisions]] as more comprehensive data becomes available.',
    impact:
      'GDP growth has [[profound implications]] for currency markets through multiple transmission channels:\n\n' +
      '[[Strong Growth]]\n\n' +
      '• [[Attracts foreign capital]] as investors seek exposure to expanding economies.\n\n' +
      '• Raises [[inflation expectations]], prompting central banks to consider tighter policy.\n\n' +
      '• Strengthens the currency through [[higher rate expectations]] and capital inflows.\n\n' +
      '[[Weak or Negative Growth]]\n\n' +
      '• Signals [[economic weakness]], potentially weakening the currency.\n\n' +
      '• Increases odds of [[monetary easing]], reducing yield attractiveness.\n\n' +
      '• Discourages [[foreign investment]], reducing demand for the currency.\n\n' +
      '[[Market dynamics]]: GDP releases are [[high-impact events]], often causing significant currency volatility. Markets react not just to the headline number but to [[components and revisions]], with consumption and investment data particularly scrutinized for forward-looking signals.',
    context:
      'U.S. GDP growth has shown [[resilience]] despite global headwinds, with Q2 2025 registering 3.8% growth following a contraction in Q1 2025 (-0.6%). The economy has demonstrated [[structural strength]] in consumption and services, offsetting weakness in some sectors.\n\n' +
      'Key themes shaping markets:\n\n' +
      '• [[Growth sustainability]]: Markets assess whether current growth rates are sustainable or driven by temporary factors.\n\n' +
      '• [[Component analysis]]: Consumption strength vs. investment weakness provides insights into economic drivers.\n\n' +
      '• [[Policy implications]]: Growth data influences Fed policy decisions, balancing growth support with inflation control.\n\n' +
      '• [[Global context]]: U.S. growth relative to other major economies affects [[currency differentials]] and capital flows.',
    traderImplications:
      '[[FX volatility]]: GDP releases are among the [[most market-moving economic events]], causing sharp moves in USD pairs, especially EUR/USD and GBP/USD.\n\n' +
      '[[Growth differentials]]: Relative GDP growth between economies drives [[currency strength]], with stronger growth typically supporting currency appreciation.\n\n' +
      '[[Cross-asset reactions]]: GDP data triggers simultaneous moves in [[equities, bonds, and commodities]] as markets reassess growth and policy outlooks.',
  },
  unemployment: {
    overview:
      'The [[Unemployment Rate]] measures the percentage of the labor force that is jobless but actively seeking work. It reflects [[labor market slack]] and the economy\'s ability to absorb workers, serving as a [[key indicator]] of economic health.\n\n' +
      'For financial markets, unemployment data is a [[critical input]] for monetary policy expectations, wage inflation forecasts, and currency valuation models.\n\n' +
      'Why traders care:\n\n' +
      '• Directly influences [[Fed policy decisions]] through the dual mandate (employment and inflation).\n\n' +
      '• Signals [[labor market tightness]], which affects wage growth and inflation expectations.\n\n' +
      '• Impacts [[currency strength]] through policy expectations and economic health assessments.',
    measurement:
      'The [[Bureau of Labor Statistics (BLS)]] calculates the unemployment rate from the [[Current Population Survey (CPS)]], a monthly survey of approximately 60,000 households. The rate represents the percentage of the [[civilian labor force]] (employed + unemployed) that is unemployed.\n\n' +
      'Key definitions:\n\n' +
      '• [[Unemployed]]: People without jobs who have actively looked for work in the past 4 weeks.\n\n' +
      '• [[Labor force]]: Employed + unemployed (excludes those not seeking work).\n\n' +
      '• [[U-6 rate]]: Broader measure including discouraged workers and part-time workers seeking full-time employment.\n\n' +
      'Data is released monthly, typically on the [[first Friday]] of each month for the previous month, with revisions possible in subsequent releases.',
    impact:
      'Unemployment readings have [[significant implications]] for currency markets through policy and economic health channels:\n\n' +
      '[[Falling Unemployment]]\n\n' +
      '• Signals [[tightening labor market]], potentially pushing wages and inflation higher.\n\n' +
      '• Encourages [[hawkish Fed policy]] (rate hikes), supporting USD strength.\n\n' +
      '• Indicates [[economic strength]], attracting foreign capital and strengthening the currency.\n\n' +
      '[[Rising Unemployment]]\n\n' +
      '• Suggests [[economic weakness]], potentially weakening the currency.\n\n' +
      '• Increases odds of [[monetary easing]], reducing yield attractiveness.\n\n' +
      '• Depresses [[wage growth]] and inflation pressure, supporting dovish policy expectations.\n\n' +
      '[[Policy dynamics]]: The Fed\'s [[dual mandate]] makes unemployment a key policy input. The [[natural rate of unemployment]] (NAIRU) concept suggests that unemployment below a certain level can trigger inflation, influencing policy decisions and currency markets.',
    context:
      'U.S. unemployment has [[gradually increased]] from historic lows, reaching 4.4% in September 2025, up from 3.7% in January 2024. The labor market remains [[relatively tight]] by historical standards, but the upward trend signals potential [[cooling]] in the economy.\n\n' +
      'Key themes shaping markets:\n\n' +
      '• [[Labor market normalization]]: Markets assess whether the increase represents a return to pre-pandemic levels or signals economic weakness.\n\n' +
      '• [[Wage pressure]]: Despite rising unemployment, wage growth remains a focus for inflation concerns.\n\n' +
      '• [[Policy implications]]: Unemployment trends influence Fed decisions on the balance between employment and inflation goals.\n\n' +
      '• [[Economic resilience]]: Current levels remain low historically, suggesting underlying economic strength.',
    traderImplications:
      '[[FX volatility]]: Unemployment releases (first Friday of each month) are [[high-impact events]], causing significant USD moves, especially in EUR/USD and GBP/USD pairs.\n\n' +
      '[[Policy expectations]]: Unemployment data directly affects [[Fed policy forecasts]], influencing yield curves and currency strength.\n\n' +
      '[[Cross-asset reactions]]: Unemployment surprises trigger moves in [[equities, bonds, and commodities]] as markets reassess growth and policy outlooks.',
  },
  'nonfarm-payrolls': {
    overview:
      '[[Non-Farm Payrolls (NFP)]] measures the monthly change in employment, excluding farm workers, government employees, and non-profit organization employees. It represents the [[net number of jobs added or lost]] in the U.S. economy and is one of the [[most closely watched economic indicators]] by traders and policymakers.\n\n' +
      'For financial markets, NFP is a [[critical high-impact release]] that directly influences monetary policy expectations, currency valuations, and risk sentiment.\n\n' +
      'Why traders care:\n\n' +
      '• [[Highest-impact economic release]]: NFP releases (first Friday of each month) cause significant market volatility.\n\n' +
      '• Directly affects [[Fed policy expectations]] through the employment component of the dual mandate.\n\n' +
      '• Signals [[economic strength or weakness]], influencing currency flows and risk sentiment across asset classes.',
    measurement:
      'The [[Bureau of Labor Statistics (BLS)]] calculates NFP from the [[Establishment Survey]], which covers approximately 145,000 businesses and government agencies representing about 697,000 worksites. The survey measures [[non-farm employment]] across all major industry sectors.\n\n' +
      'Key components:\n\n' +
      '• [[Total non-farm employment]]: The headline number reported in thousands (K).\n\n' +
      '• [[Private sector employment]]: Excludes government workers.\n\n' +
      '• [[Average hourly earnings]]: Wage growth component, also closely watched.\n\n' +
      '• [[Average workweek]]: Hours worked, indicating labor demand.\n\n' +
      'Data is released monthly on the [[first Friday]] of each month at 8:30 AM ET for the previous month, with [[revisions]] common in subsequent months as more complete data arrives.',
    impact:
      'NFP releases have [[profound market-moving effects]] through multiple transmission channels:\n\n' +
      '[[Strong NFP (High Job Gains)]]\n\n' +
      '• Signals [[robust economic growth]] and labor market strength.\n\n' +
      '• Supports [[hawkish Fed policy]] expectations (rate hikes), strengthening USD.\n\n' +
      '• Attracts [[foreign capital]] as investors seek exposure to strong economies.\n\n' +
      '• Can trigger [[risk-on sentiment]] if growth is seen as sustainable.\n\n' +
      '[[Weak NFP (Low/Negative Job Gains)]]\n\n' +
      '• Suggests [[economic weakness]], potentially weakening the currency.\n\n' +
      '• Increases odds of [[monetary easing]], reducing yield attractiveness.\n\n' +
      '• Triggers [[risk-off sentiment]] as markets reassess growth outlooks.\n\n' +
      '[[Market dynamics]]: NFP is known as the [["king of economic indicators"]] due to its market impact. The release often causes [[immediate and significant volatility]] in USD pairs, with EUR/USD and GBP/USD particularly sensitive. Markets react not just to the headline number but to [[revisions, wage data, and unemployment rate]] released simultaneously.',
    context:
      'U.S. Non-Farm Payrolls have shown [[volatile patterns]] in recent months, with September 2025 registering 119K jobs added, following a contraction of -4K in August 2025. The labor market has demonstrated [[resilience]] despite some monthly volatility, with strong gains in services sectors offsetting weakness in some industries.\n\n' +
      'Key themes shaping markets:\n\n' +
      '• [[Job growth sustainability]]: Markets assess whether current job gains are sustainable or driven by temporary factors.\n\n' +
      '• [[Wage pressure]]: Average hourly earnings data influences inflation expectations and Fed policy.\n\n' +
      '• [[Sector composition]]: Strength in services vs. goods sectors provides insights into economic drivers.\n\n' +
      '• [[Policy implications]]: NFP data directly influences Fed decisions on the balance between employment and inflation goals.',
    traderImplications:
      '[[FX volatility]]: NFP releases are the [[most market-moving economic events]], causing immediate and significant USD moves, especially in EUR/USD, GBP/USD, and USD/JPY pairs.\n\n' +
      '[[Trading opportunities]]: The first Friday NFP release creates [[high-volatility trading opportunities]], with markets often gapping and trending strongly post-release.\n\n' +
      '[[Cross-asset reactions]]: NFP data triggers simultaneous moves in [[equities, bonds, commodities, and currencies]] as markets reassess growth, policy, and risk outlooks.',
  },
  'core-inflation-YoY': {
    overview:
      '[[Core Inflation Year-over-Year]] measures the annual change in consumer prices excluding [[volatile food and energy components]]. It is the [[Federal Reserve\'s preferred inflation gauge]] for monetary policy decisions, providing a clearer view of [[underlying inflation trends]] without short-term commodity price fluctuations.\n\n' +
      'For financial markets, Core Inflation is a [[critical policy input]] that directly influences Fed rate decisions and currency valuations.\n\n' +
      'Why traders care:\n\n' +
      '• [[Primary Fed policy input]]: The Fed focuses on core inflation for rate decisions, making it more important than headline inflation.\n\n' +
      '• [[Underlying trend indicator]]: Removes noise from volatile food/energy prices, showing true inflation momentum.\n\n' +
      '• [[Currency impact]]: Core inflation readings directly affect Fed policy expectations and USD strength.',
    measurement:
      'The [[Bureau of Labor Statistics (BLS)]] calculates Core CPI by taking the Consumer Price Index and [[excluding food and energy components]]. The year-over-year change is calculated by comparing the current month\'s Core CPI to the same month in the previous year.\n\n' +
      'Key components:\n\n' +
      '• [[Core CPI]]: All items except food and energy, representing approximately 78% of the CPI basket.\n\n' +
      '• [[Food excluded]]: Fresh fruits, vegetables, meat, dairy, and processed foods.\n\n' +
      '• [[Energy excluded]]: Gasoline, electricity, natural gas, and fuel oil.\n\n' +
      '• [[Included items]]: Housing, medical care, transportation services, apparel, education, and other services.\n\n' +
      'Data is released monthly, typically around the [[10th-15th of each month]] for the previous month, alongside headline CPI.',
    impact:
      'Core Inflation has [[significant implications]] for currency markets through Fed policy channels:\n\n' +
      '[[Elevated Core Inflation]]\n\n' +
      '• Signals [[persistent price pressures]], increasing likelihood of [[hawkish Fed policy]] (rate hikes).\n\n' +
      '• Strengthens [[USD]] as markets price in tighter monetary policy.\n\n' +
      '• Indicates [[underlying inflation momentum]], which is harder to control than headline inflation.\n\n' +
      '[[Moderate/Declining Core Inflation]]\n\n' +
      '• Suggests [[inflation is under control]], potentially allowing [[dovish policy]] (rate cuts).\n\n' +
      '• Can [[weaken USD]] if it leads to expectations of monetary easing.\n\n' +
      '• Supports [[risk assets]] as lower inflation reduces pressure on central banks.\n\n' +
      '[[Policy dynamics]]: The Fed\'s [[dual mandate]] makes core inflation a key policy input. The Fed targets [[2% core inflation]] over the long term, and deviations from this target directly influence rate decisions and currency markets.',
    context:
      'U.S. Core Inflation has [[moderated significantly]] from 3.9% in January 2024 to 3.0% in September 2025, showing progress toward the Fed\'s 2% target. However, core inflation remains [[above the Fed\'s objective]], indicating persistent underlying price pressures.\n\n' +
      'Key themes shaping markets:\n\n' +
      '• [[Sticky inflation]]: Core inflation has been more persistent than headline inflation, driven by services and housing costs.\n\n' +
      '• [[Fed policy focus]]: The Fed closely monitors core inflation for rate decisions, making it more market-moving than headline inflation.\n\n' +
      '• [[Services vs. goods]]: Services inflation remains elevated while goods inflation has moderated.\n\n' +
      '• [[Policy implications]]: Current core inflation levels suggest the Fed may maintain restrictive policy until inflation moves closer to 2%.',
    traderImplications:
      '[[FX volatility]]: Core Inflation releases are [[high-impact events]], causing significant USD moves, especially in EUR/USD and GBP/USD pairs.\n\n' +
      '[[Policy expectations]]: Core inflation data directly affects [[Fed policy forecasts]], influencing yield curves and currency strength.\n\n' +
      '[[Cross-asset reactions]]: Core inflation surprises trigger moves in [[equities, bonds, and commodities]] as markets reassess inflation and policy outlooks.',
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
            <span className="rates-label"><b>Central Bank Rates:</b></span>
            
            <div className="rates-grid">
              {centralBankRates.map((item, index) => (
                <React.Fragment key={item.country}>
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
          description: 'Unemployment Rate - Measures the percentage of the labor force that is jobless but actively seeking work in the eurozone. A key indicator of labor market health and economic slack, closely monitored by the European Central Bank for monetary policy decisions. Lower unemployment typically supports EUR strength through improved economic outlook.',
          chartData: [55, 58, 56, 54, 52, 53, 51, 50],
          chartLabel: 'Rate trend'
        },
        {
          id: 'current-account',
          title: 'Current Account',
          currentValue: '+€12.8B',
          description: 'Current Account Balance - Measures the difference between a country\'s savings and investment, including trade balance, net income from abroad, and net current transfers. A positive current account indicates the eurozone is a net lender to the rest of the world, supporting EUR strength through capital flows.',
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
          currentValue: '4.00%',
          description: 'Bank Rate - The primary monetary policy tool set by the Bank of England (BoE). Represents the interest rate at which the BoE lends to commercial banks. This rate influences borrowing costs across the UK and is a key driver of GBP strength.',
          chartData: [75, 78, 82, 85, 88, 86, 84, 82],
          chartLabel: 'Last 8 months'
        },
        {
          id: 'inflation',
          title: 'Inflation (CPI)',
          currentValue: '4.6%',
          description: 'Consumer Price Index (CPI) Year-over-Year - The official measure of inflation for the United Kingdom, calculated by the Office for National Statistics (ONS). CPI provides the primary inflation target for the Bank of England (BoE), which targets 2% inflation.',
          chartData: [80, 85, 88, 92, 95, 93, 90, 88],
          chartLabel: 'YoY trend'
        },
        {
          id: 'core-inflation-YoY',
          title: 'Core Inflation YoY',
          currentValue: '3.4%',
          description: 'Core CPI (Consumer Price Index) Year-over-Year - Measures the annual change in consumer prices excluding volatile food, energy, alcohol, and tobacco. This is the Bank of England\'s preferred inflation gauge for monetary policy decisions, providing a clearer view of underlying inflation trends without short-term commodity price fluctuations.',
          chartData: [70, 72, 75, 78, 82, 80, 85, 88],
          chartLabel: 'Core YoY trend'
        },
        {
          id: 'gdp-growth',
          title: 'GDP Growth',
          currentValue: '+1.5%',
          description: 'GDP Annual Growth Rate - Measures the year-over-year percentage change in Gross Domestic Product for the United Kingdom. GDP growth reflects the overall health and expansion of the economy, influencing Bank of England monetary policy decisions and GBP strength.',
          chartData: [50, 52, 48, 45, 42, 44, 46, 48],
          chartLabel: 'Q/Q growth'
        },
        {
          id: 'unemployment',
          title: 'Unemployment',
          currentValue: '4.2%',
          description: 'Unemployment Rate - Measures the percentage of the labor force that is jobless but actively seeking work in the United Kingdom. A key indicator of labor market health and economic slack, closely monitored by the Bank of England for monetary policy decisions. Lower unemployment typically supports GBP strength through improved economic outlook.',
          chartData: [35, 38, 36, 34, 32, 33, 31, 30],
          chartLabel: 'Rate trend'
        },
        {
          id: 'wage-growth',
          title: 'Wage Growth',
          currentValue: '4.7%',
          description: 'Wage Growth (Average Weekly Earnings) - Measures the year-over-year percentage change in average weekly earnings for employees in the UK. Wage growth is a key indicator for the Bank of England as it influences inflation expectations and monetary policy decisions. Strong wage growth can signal inflationary pressures and may lead to tighter monetary policy, affecting GBP strength.',
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
          currentValue: '0.50%',
          description: 'Bank of Japan Policy Rate - The overnight interest rate set by the Bank of Japan (BoJ) as its primary monetary policy tool. Represents the target for short-term interest rates in Japan.',
          chartData: [15, 18, 22, 25, 28, 26, 24, 22],
          chartLabel: 'Last 8 months'
        },
        {
          id: 'inflation',
          title: 'Inflation (CPI)',
          currentValue: '2.8%',
          description: 'Consumer Price Index Year-over-Year - Measures the annual percentage change in prices for a basket of consumer goods and services in Japan. The Bank of Japan (BoJ) targets 2% inflation as part of its monetary policy framework.',
          chartData: [35, 38, 42, 45, 48, 46, 44, 42],
          chartLabel: 'YoY trend'
        },
        {
          id: 'core-inflation-YoY',
          title: 'Core Inflation YoY',
          currentValue: '3.0%',
          description: 'Core Inflation Year-over-Year - Measures the annual change in consumer prices excluding volatile food and energy components in Japan. The Bank of Japan (BoJ) monitors core inflation closely as it provides a clearer view of underlying inflation trends and is less affected by temporary price shocks.',
          chartData: [50, 55, 52, 48, 52, 54, 56, 58, 52, 50, 56, 62, 60, 62, 66, 66, 70, 64, 62, 56, 60, 62],
          chartLabel: 'YoY trend'
        },
        {
          id: 'gdp-growth',
          title: 'GDP Growth',
          currentValue: '+1.2%',
          description: 'Gross Domestic Product Growth Rate - Measures the quarterly percentage change in real GDP (adjusted for inflation) in Japan. A key indicator of overall economic health and growth momentum, closely monitored by the Bank of Japan for monetary policy decisions.',
          chartData: [30, 32, 28, 25, 22, 24, 26, 28],
          chartLabel: 'Q/Q growth'
        },
        {
          id: 'unemployment',
          title: 'Unemployment',
          currentValue: '2.6%',
          description: 'Unemployment Rate - Measures the percentage of the labor force that is jobless but actively seeking work in Japan. A key indicator of labor market health and economic slack, closely monitored by the Bank of Japan for monetary policy decisions. Japan typically maintains very low unemployment rates compared to other developed economies.',
          chartData: [20, 22, 20, 18, 16, 17, 15, 14],
          chartLabel: 'Rate trend'
        },
        {
          id: 'trade-balance',
          title: 'Current Account',
          currentValue: '+¥1.2T',
          description: 'Current Account Balance - Measures the difference between a country\'s savings and investment, including trade balance, net income from abroad, and net current transfers. A positive current account indicates Japan is a net lender to the rest of the world, supporting JPY strength through capital flows.',
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

  const getIndicatorInsights = (indicator) => {
    if (Array.isArray(indicator.insights) && indicator.insights.length > 0) {
      return indicator.insights;
    }

    // Special handling for interest-rate with professional content
    if (indicator.id === 'interest-rate') {
      return [
        'The Federal Funds Rate has shifted from restrictive policy toward cautious easing, cutting rates to 3.50%–3.75% amid moderating inflation and signs of labor market softening.',
        'Major global banks broadly expect further rate cuts into 2026, but emphasize a measured and data-dependent pace. Markets currently price 1–3 additional 25bp cuts, with timing sensitive to incoming data.',
        'The highest-conviction trades emerge when data, expectations, and policy guidance align. Monitor core inflation trends, labor market data, Fed communication tone, and yield curve dynamics for rate repricing signals.',
        'Political pressure from President Trump for lower rates adds headline-driven volatility and can influence market narratives around Fed independence and policy credibility.',
      ];
    }

    // Special handling for inflation-YoY with professional content
    if (indicator.id === 'inflation-YoY') {
      return [
        'U.S. inflation (CPI YoY) has moderated to 3.0% as of September 2025, down from peak levels but still above the Federal Reserve\'s 2% target.',
        'The disinflationary trend has been gradual, with services inflation remaining sticky while goods prices have eased more substantially.',
        'Markets closely monitor each monthly release to assess whether inflation is on a sustainable path toward the Fed\'s target, which influences policy expectations and currency flows.',
        'Inflation expectations, momentum, and consensus forecasts will appear here once live data is integrated.',
      ];
    }

    // Special handling for gdp-growth with professional content
    if (indicator.id === 'gdp-growth') {
      return [
        'U.S. GDP growth registered 3.8% in Q2 2025, rebounding from a contraction of -0.6% in Q1 2025, demonstrating economic resilience amid global headwinds.',
        'The economy has shown structural strength in consumption and services sectors, with growth driven by robust consumer spending despite some weakness in investment components.',
        'Markets closely watch GDP releases for signals on economic momentum, as strong growth supports currency strength through capital inflows and higher rate expectations.',
        'GDP growth expectations, momentum, and consensus forecasts will appear here once live data is integrated.',
      ];
    }

    // Special handling for unemployment with professional content
    if (indicator.id === 'unemployment') {
      return [
        'U.S. unemployment has gradually increased to 4.4% in September 2025, up from 3.7% in January 2024, signaling potential cooling in the labor market while remaining relatively tight by historical standards.',
        'The labor market continues to show resilience, with unemployment levels remaining low historically despite the upward trend, suggesting underlying economic strength.',
        'Markets closely monitor unemployment data for signals on labor market tightness, wage pressure, and Fed policy implications, as it directly affects monetary policy expectations and currency flows.',
        'Unemployment expectations, momentum, and consensus forecasts will appear here once live data is integrated.',
      ];
    }

    // Special handling for nonfarm-payrolls with professional content
    if (indicator.id === 'nonfarm-payrolls') {
      return [
        'U.S. Non-Farm Payrolls registered 119K jobs added in September 2025, following a contraction of -4K in August 2025, demonstrating the volatile nature of monthly employment data.',
        'The labor market has shown resilience with strong gains in services sectors, though monthly readings can vary significantly due to seasonal adjustments and economic fluctuations.',
        'Markets closely watch NFP releases (first Friday of each month) as they are among the highest-impact economic events, directly influencing Fed policy expectations and causing significant currency volatility.',
        'NFP expectations, momentum, and consensus forecasts will appear here once live data is integrated.',
      ];
    }

    // Special handling for core-inflation-YoY with professional content
    if (indicator.id === 'core-inflation-YoY') {
      return [
        'U.S. Core Inflation has moderated to 3.0% in September 2025, down from 3.9% in January 2024, showing progress toward the Fed\'s 2% target while remaining above the objective.',
        'Core inflation, which excludes volatile food and energy components, is the Federal Reserve\'s preferred inflation gauge for monetary policy decisions, making it more market-moving than headline inflation.',
        'The persistent elevation of core inflation, driven by services and housing costs, suggests the Fed may maintain restrictive policy until inflation moves closer to the 2% target.',
        'Core inflation expectations, momentum, and consensus forecasts will appear here once live data is integrated.',
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

  const getIndicatorDetails = (indicator) => {
    const defaults = indicatorDetails[indicator.id] || {};
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
        const insightItems = getIndicatorInsights(expandedIndicator);
        const { overview, measurement, impact, context, traderImplications } = getIndicatorDetails(expandedIndicator);
        
        // Get accurate quick reference data based on indicator
        const getQuickReferenceData = (indicator) => {
          const baseData = {
            currentValue: indicator.currentValue,
            indicator: indicator.title,
            lastUpdated: indicator.asOf || null,
            frequency: indicator.frequency || null,
            unit: indicator.unit || null,
          };
          
          // Add indicator-specific data
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

      <div className="economy-analysis" ref={analysisRef}>
        <h2 className="analysis-title">Hollistic Scan</h2>
        <p className="analysis-placeholder">Coming soon</p>
      </div>
    </div>
  );
}
