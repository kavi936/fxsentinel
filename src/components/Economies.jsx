import React, { useMemo, useState } from 'react';
import './Economies.css';
import economyIndicatorsData from '../data/economyIndicators.json';

const indicatorDetails = {
  'interest-rate': {
    overview:
      'The [[Federal Funds Rate]] is the overnight interest rate at which U.S. banks lend reserve balances to one another. It is established by the [[Federal Open Market Committee (FOMC)]] and serves as the benchmark for short-term interest rates across the U.S. financial system.\n\n' +
      'For financial markets, the rate is a [[cornerstone driver]]: it influences borrowing costs, risk pricing, asset valuations, and capital flows both domestically and globally.\n\n' +
      'Why traders care:\n\n' +
      '• Sets the tone for [[USD strength/weakness]] across FX markets.\n\n' +
      '• Impacts equity valuations by adjusting cost of capital and discount rates.\n\n' +
      '• Drives yield shifts across the fixed income curve, affecting carry trades and volatility.',
    measurement:
      'The FOMC announces a [[target range]] for the Federal Funds Rate at scheduled policy meetings (typically [[8 per year]]).\n\n' +
      'The [[effective federal funds rate (EFFR)]] is the actual rate banks trade overnight and typically stays within the target range due to Fed market operations.\n\n' +
      'Data is published daily by the Federal Reserve and available historically via [[FRED (Federal Reserve Economic Data)]].',
    impact:
      'Interest rate changes and forward guidance are [[primary drivers]] of currency movements:\n\n' +
      '[[Rate / Hawkish Signals]]\n\n' +
      '• Bolster the USD as [[higher yields]] attract foreign capital.\n\n' +
      '• Tend to widen yield differentials vs. other economies, lifting dollar pairs.\n\n' +
      '• Can tighten financial conditions, potentially pressuring equities.\n\n' +
      '[[Rate / Dovish Signals]]\n\n' +
      '• Compress yield advantages of dollar assets, potentially [[weakening the USD]].\n\n' +
      '• Encourage risk-taking in carry trades targeting higher-yield currencies.\n\n' +
      '• Often support equities in the near term through lower financing costs.\n\n' +
      '[[Forward expectations matter]]: Markets can price in future rate changes well before actual announcements, meaning FX and rates markets are highly sensitive to inflation data, employment releases, and Fed "dot plot" projections.',
    context:
      'The U.S. Federal Reserve has shifted away from prolonged tightening and is now [[methodically easing policy]] in response to softer employment trends and sticky—but gradually moderating—inflation. Most recently, the Fed cut rates by 25 bps, marking continued policy accommodation.\n\n' +
      'Key themes shaping markets:\n\n' +
      '• [[Data-dependence]]: Future rate moves hinge on inflation readings and labor market resilience.\n\n' +
      '• [[Market expectations]]: Traders are pricing in additional cuts, but the pace and magnitude remain uncertain.\n\n' +
      '• [[Inflation dynamics]]: Core inflation has eased but remains above the Fed\'s 2% objective, tempering expectations for aggressive easing.\n\n' +
      '• [[Risk environment]]: Geopolitical and fiscal factors (e.g., government shutdowns and tariff pressures) add uncertainty to the monetary outlook.',
    traderImplications:
      '[[FX volatility]]: Rate decisions and forward guidance can trigger rapid USD moves, especially in USD/JPY, EUR/USD, and GBP/USD.\n\n' +
      '[[Carry & yield trades]]: Changing rate expectations alter carry trade viability and relative currency strengths.\n\n' +
      '[[Cross-asset reactions]]: Fed moves often ripple into equities, commodities, and fixed income via shifts in risk sentiment.',
  },
  inflation: {
    overview:
      'Inflation tracks the change in consumer prices and acts as a proxy for purchasing power erosion. Stable, moderate inflation informs whether monetary policy is appropriately calibrated to growth dynamics.',
    measurement:
      'Derived from consumer price indices that aggregate a basket of goods and services. Headline figures include volatile components (food, energy) while core measures strip them out to highlight underlying trends.',
    impact:
      'Elevated inflation can undermine a currency by eroding real returns, but if it pushes a central bank towards tighter policy, the currency may strengthen. Soft inflation often relieves pressure on policy makers, which can weigh on rate expectations and the currency.',
  },
  'gdp-growth': {
    overview:
      'GDP growth summarises the expansion or contraction in overall economic output. It signals whether activity is accelerating, decelerating, or plateauing across consumption, investment, government spending, and net trade.',
    measurement:
      'Calculated by national statistical agencies as the percentage change in real GDP (adjusted for inflation) from one quarter to the next, typically annualised for comparability. Revisions are common as more comprehensive data arrives.',
    impact:
      'Stronger growth usually boosts currency demand by attracting capital inflows and raising expectations for tighter policy. Weak or negative growth does the opposite, increasing the odds of easing and discouraging foreign investment.',
  },
  unemployment: {
    overview:
      'The unemployment rate reflects slack in the labour market and the ability of the economy to absorb workers. Persistent cushions or shortages shape wage dynamics and ultimately influence inflation.',
    measurement:
      'Reported as the percentage of the labour force that is jobless but actively seeking work, based on monthly household surveys and administrative records. Some regions also track broader underemployment indicators.',
    impact:
      'Falling unemployment often signals a tightening labour market that can push wages and inflation higher, encouraging rate hikes and supporting the currency. Rising unemployment can depress wage growth, weaken inflation pressure, and fuel expectations for monetary easing.',
  },
  'consumer-confidence': {
    overview:
      'Consumer confidence gauges household sentiment about the current and future economic environment. It offers a forward-looking read on consumption, which dominates GDP in most developed markets.',
    measurement:
      'Compiled from survey responses that ask households about personal finances, business conditions, employment prospects, and intentions to make large purchases. Scores are indexed against historic baselines.',
    impact:
      'Improving confidence can bolster consumption and growth prospects, supporting the currency through higher rate expectations. Deteriorating confidence foreshadows weaker spending, which may prompt looser policy and dampen the currency.',
  },
  'trade-balance': {
    overview:
      'The trade balance captures the net flow of goods and services across borders—whether an economy exports more than it imports. It shapes FX flows by indicating demand for domestic versus foreign currency.',
    measurement:
      'Compiled from customs and payments data as exports minus imports over a given period, typically reported in nominal currency terms. Analysts monitor both monthly prints and rolling averages to smooth volatility.',
    impact:
      'A surplus signals net foreign demand for local goods and currency, often supporting exchange rates, while persistent deficits can weigh on a currency unless offset by capital inflows or higher yields.',
  },
};

function Economies() {
  const [selectedEconomy, setSelectedEconomy] = useState('US');
  const analysisRef = React.useRef(null);
  // Central bank rates data (will move to backend later)
  const centralBankRates = [
    {
      flag: '🇺🇸',
      country: 'USA',
      rate: 3.75,
      bankName: 'Fed',
      trend: 'down',
      nextMeeting: 'Dec 18, 2024'
    },
    {
      flag: '🇬🇧',
      country: 'UK',
      rate: 4.00,
      bankName: 'BOE',
      trend: 'stable',
      nextMeeting: 'Dec 19, 2024'
    },
    {
      flag: '🇪🇺',
      country: 'EU',
      rate: 2.15,
      bankName: 'ECB',
      trend: 'stable',
      nextMeeting: 'Dec 19, 2024'
    },
    {
      flag: '🇯🇵',
      country: 'Japan',
      rate: 0.50,
      bankName: 'BOJ',
      trend: 'stable',
      nextMeeting: 'Dec 19, 2024'
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
              <option value="US"><b>🇺🇸 United States</b></option>
              <option value="EUR"><b>🇪🇺 European Union</b></option>
              <option value="GBP"><b>🇬🇧 United Kingdom</b></option>
              <option value="JPY"><b>🇯🇵 Japan</b></option>
            </select>
            </div>
            <button type="button" className="holistic-scan-button" onClick={handleScrollToAnalysis}>
              Hollistic Scan
            </button>
          </div>
          
          {/* Card Body */}
          <div className="card-body">
            <EconomyDetails selectedEconomy={selectedEconomy} analysisRef={analysisRef} />
          </div>
        </div>
      </div>
    </div>
  );
}

export default Economies;


function EconomyDetails({ selectedEconomy, analysisRef }) {
  const [isLoading, setIsLoading] = useState(false);
  const [expandedIndicatorId, setExpandedIndicatorId] = useState(null);
  const [loadingIndicatorId, setLoadingIndicatorId] = useState(null);
  const [chartHover, setChartHover] = useState(null);

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
      description: realData.description || placeholderIndicator.description,
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
          id: 'inflation',
          title: 'Inflation (CPI)',
          currentValue: '3.2%',
          description: 'Consumer Price Index - Core inflation measure',
          chartData: [45, 52, 48, 41, 38, 42, 39, 35],
          chartLabel: 'YoY trend'
        },
        {
          id: 'gdp-growth',
          title: 'GDP Growth',
          currentValue: '+2.1%',
          description: 'Quarterly GDP growth rate (annualized)',
          chartData: [60, 65, 58, 62, 68, 64, 67, 70],
          chartLabel: 'Q/Q growth'
        },
        {
          id: 'unemployment',
          title: 'Unemployment',
          currentValue: '3.8%',
          description: 'Unemployment rate - Labor market health',
          chartData: [25, 28, 26, 24, 22, 23, 21, 20],
          chartLabel: 'Rate trend'
        },
        {
          id: 'consumer-confidence',
          title: 'Consumer Confidence',
          currentValue: '102.3',
          description: 'Consumer sentiment index - Spending outlook',
          chartData: [70, 75, 72, 78, 82, 79, 85, 88],
          chartLabel: 'Index trend'
        },
        {
          id: 'trade-balance',
          title: 'Trade Balance',
          currentValue: '-$67.4B',
          description: 'Trade deficit - Export/import balance',
          chartData: [15, 18, 22, 25, 28, 26, 24, 20],
          chartLabel: 'Monthly deficit'
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
          title: 'Interest Rate',
          currentValue: '2.15%',
          description: 'Main Refinancing Rate - ECB policy tool',
          chartData: [45, 48, 52, 55, 58, 56, 54, 52],
          chartLabel: 'Last 8 months'
        },
        {
          id: 'inflation',
          title: 'Inflation (HICP)',
          currentValue: '2.4%',
          description: 'Harmonized Index - Euro area inflation',
          chartData: [65, 68, 72, 75, 78, 76, 74, 72],
          chartLabel: 'YoY trend'
        },
        {
          id: 'gdp-growth',
          title: 'GDP Growth',
          currentValue: '+0.8%',
          description: 'Quarterly GDP growth rate',
          chartData: [40, 42, 38, 35, 32, 34, 36, 38],
          chartLabel: 'Q/Q growth'
        },
        {
          id: 'unemployment',
          title: 'Unemployment',
          currentValue: '6.4%',
          description: 'Unemployment rate - Labor market',
          chartData: [55, 58, 56, 54, 52, 53, 51, 50],
          chartLabel: 'Rate trend'
        },
        {
          id: 'consumer-confidence',
          title: 'Consumer Confidence',
          currentValue: '95.2',
          description: 'Economic sentiment indicator',
          chartData: [60, 62, 58, 55, 52, 54, 56, 58],
          chartLabel: 'Index trend'
        },
        {
          id: 'trade-balance',
          title: 'Trade Balance',
          currentValue: '+€12.8B',
          description: 'Trade surplus - Export strength',
          chartData: [70, 72, 75, 78, 82, 80, 85, 88],
          chartLabel: 'Monthly surplus'
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
          title: 'Interest Rate',
          currentValue: '4.00%',
          description: 'Bank Rate - BoE policy rate',
          chartData: [75, 78, 82, 85, 88, 86, 84, 82],
          chartLabel: 'Last 8 months'
        },
        {
          id: 'inflation',
          title: 'Inflation (CPI)',
          currentValue: '4.6%',
          description: 'Consumer Price Index - UK inflation',
          chartData: [80, 85, 88, 92, 95, 93, 90, 88],
          chartLabel: 'YoY trend'
        },
        {
          id: 'gdp-growth',
          title: 'GDP Growth',
          currentValue: '+1.5%',
          description: 'Quarterly GDP growth rate',
          chartData: [50, 52, 48, 45, 42, 44, 46, 48],
          chartLabel: 'Q/Q growth'
        },
        {
          id: 'unemployment',
          title: 'Unemployment',
          currentValue: '4.2%',
          description: 'Unemployment rate - Labor market',
          chartData: [35, 38, 36, 34, 32, 33, 31, 30],
          chartLabel: 'Rate trend'
        },
        {
          id: 'consumer-confidence',
          title: 'Consumer Confidence',
          currentValue: '89.7',
          description: 'GfK consumer confidence index',
          chartData: [45, 48, 42, 38, 35, 37, 39, 41],
          chartLabel: 'Index trend'
        },
        {
          id: 'trade-balance',
          title: 'Trade Balance',
          currentValue: '-£8.2B',
          description: 'Trade deficit - Import/export balance',
          chartData: [25, 28, 32, 35, 38, 36, 34, 32],
          chartLabel: 'Monthly deficit'
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
          description: 'Policy Rate - BoJ overnight rate',
          chartData: [15, 18, 22, 25, 28, 26, 24, 22],
          chartLabel: 'Last 8 months'
        },
        {
          id: 'inflation',
          title: 'Inflation (CPI)',
          currentValue: '2.8%',
          description: 'Consumer Price Index - Japan inflation',
          chartData: [35, 38, 42, 45, 48, 46, 44, 42],
          chartLabel: 'YoY trend'
        },
        {
          id: 'gdp-growth',
          title: 'GDP Growth',
          currentValue: '+1.2%',
          description: 'Quarterly GDP growth rate',
          chartData: [30, 32, 28, 25, 22, 24, 26, 28],
          chartLabel: 'Q/Q growth'
        },
        {
          id: 'unemployment',
          title: 'Unemployment',
          currentValue: '2.6%',
          description: 'Unemployment rate - Labor market',
          chartData: [20, 22, 20, 18, 16, 17, 15, 14],
          chartLabel: 'Rate trend'
        },
        {
          id: 'consumer-confidence',
          title: 'Consumer Confidence',
          currentValue: '36.2',
          description: 'Consumer confidence index',
          chartData: [25, 28, 24, 20, 18, 20, 22, 24],
          chartLabel: 'Index trend'
        },
        {
          id: 'trade-balance',
          title: 'Trade Balance',
          currentValue: '+¥1.2T',
          description: 'Trade surplus - Export strength',
          chartData: [60, 62, 65, 68, 72, 70, 75, 78],
          chartLabel: 'Monthly surplus'
        }
      ],
    },
    };

    // Merge real data from JSON file with placeholder data
    const mergedData = { ...baseData };
    
    Object.keys(economyIndicatorsData).forEach((countryCode) => {
      if (mergedData[countryCode] && economyIndicatorsData[countryCode]?.indicators) {
        const realIndicators = economyIndicatorsData[countryCode].indicators;
        
        mergedData[countryCode].indicators = mergedData[countryCode].indicators.map((indicator) => {
          const realData = realIndicators[indicator.id];
          return realData ? mergeIndicatorData(indicator, realData) : indicator;
        });
      }
    });

    return mergedData;
  }, []);

  const data = economyData[selectedEconomy] || economyData.US;
  const toggleIndicatorCard = (indicatorId) => {
    const isCurrentlyExpanded = expandedIndicatorId === indicatorId;
    
    if (!isCurrentlyExpanded) {
      // Starting expansion - show loading
      setLoadingIndicatorId(indicatorId);
      setExpandedIndicatorId(indicatorId);
      
      // Clear loading after expansion animation completes
      setTimeout(() => {
        setLoadingIndicatorId(null);
      }, 800); // Show spinner for 800ms to ensure visibility
    } else {
      // Collapsing - no loading needed
      setExpandedIndicatorId(null);
      setLoadingIndicatorId(null);
    }
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
        'The Federal Funds Rate — the U.S. central bank\'s key policy tool — has entered a cautious easing cycle after a series of rate cuts in 2025, most recently bringing the target range to 3.50%–3.75%.',
        'Markets now price a limited number of further cuts, with traders focusing intently on incoming inflation and labor data to gauge the next move.',
        'Rate expectations, momentum, and consensus forecasts will appear here once live data is integrated.',
        'Upcoming releases will link this indicator with the broader macro backdrop in Holistic Scan.',
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
    return paragraphs.map((para, index) => (
      <p key={index}>{renderHighlightedText(para.trim())}</p>
    ));
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

  // Generate SVG path for line chart
  // Generate smooth bezier curve path for better visual appeal
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
    
    // Create smooth bezier curve path
    let path = `M ${points[0].x},${points[0].y}`;
    
    for (let i = 0; i < points.length - 1; i++) {
      const current = points[i];
      const next = points[i + 1];
      
      // Calculate control points for smooth curve
      const cp1x = current.x + (next.x - current.x) / 3;
      const cp1y = current.y;
      const cp2x = current.x + (next.x - current.x) * 2 / 3;
      const cp2y = next.y;
      
      path += ` C ${cp1x},${cp1y} ${cp2x},${cp2y} ${next.x},${next.y}`;
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

  // Simulate loading when economy changes
  React.useEffect(() => {
    setIsLoading(true);
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 400); // 400ms loading time

    return () => clearTimeout(timer);
  }, [selectedEconomy]);

  if (isLoading) {
    return (
      <div className="economy-loading">
        <div className="loading-spinner">
          <div className="spinner-ring"></div>
          <div className="spinner-ring"></div>
          <div className="spinner-ring"></div>
        </div>
        <div className="loading-text">Loading economic data...</div>
      </div>
    );
  }

  return (
    <div className="economy-details">
      <div className="economic-indicators-grid">
        {data.indicators.map((indicator) => {
          const isExpanded = expandedIndicatorId === indicator.id;
          const insightItems = getIndicatorInsights(indicator);
          const { overview, measurement, impact, context, traderImplications } = getIndicatorDetails(indicator);

          return (
            <div
              key={indicator.id}
              className={`indicator-card ${isExpanded ? 'expanded' : ''}`}
              role="button"
              tabIndex={0}
              onClick={() => toggleIndicatorCard(indicator.id)}
              onKeyDown={(event) => handleIndicatorKeyDown(event, indicator.id)}
              aria-expanded={isExpanded}
            >
            <div className="indicator-header">
              <div className="indicator-title">{indicator.title}</div>
              <div className="indicator-value">{indicator.currentValue}</div>
            </div>
            <div className="indicator-description">{indicator.description}</div>
              <div className={`indicator-chart ${isExpanded ? 'expanded' : ''}`}>
                {(() => {
                  // Select appropriate dataset based on expansion state
                  const chartDataToUse = isExpanded && indicator.chartDataExpanded 
                    ? indicator.chartDataExpanded 
                    : indicator.chartData;
                  const originalDataToUse = isExpanded && indicator.chartDataOriginalAll 
                    ? indicator.chartDataOriginalAll 
                    : indicator.chartDataOriginal;
                  const datesToUse = isExpanded && indicator.chartDatesAll 
                    ? indicator.chartDatesAll 
                    : indicator.chartDates;
                  
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
                    
                    // Round min down and max up to nice numbers
                    // Determine rounding step based on range
                    let roundingStep;
                    if (rawRange <= 1) {
                      roundingStep = 0.1; // Round to 0.1 for very small ranges
                    } else if (rawRange <= 5) {
                      roundingStep = 0.5; // Round to 0.5 for small ranges
                    } else {
                      roundingStep = 1; // Round to whole numbers for larger ranges
                    }
                    
                    // Round min down and max up
                    const min = Math.floor(rawMin / roundingStep) * roundingStep;
                    const max = Math.ceil(rawMax / roundingStep) * roundingStep;
                    const range = max - min;
                    
                    // Calculate 5 evenly spaced values
                    const step = range / 4; // 4 steps between 5 labels
                    const labels = [];
                    
                    for (let i = 0; i < 5; i++) {
                      const position = (i / 4) * 100; // 0%, 25%, 50%, 75%, 100%
                      const value = max - (step * i);
                      
                      // Round to clean number
                      let cleanValue;
                      if (roundingStep >= 1) {
                        cleanValue = Math.round(value);
                      } else if (roundingStep === 0.5) {
                        cleanValue = Math.round(value * 2) / 2;
                      } else {
                        cleanValue = Math.round(value * 10) / 10;
                      }
                      
                      // Format based on rounding step
                      let formattedLabel;
                      if (roundingStep >= 1) {
                        formattedLabel = cleanValue.toFixed(0) + '%';
                      } else if (roundingStep === 0.5) {
                        formattedLabel = cleanValue.toFixed(1) + '%';
                      } else {
                        formattedLabel = cleanValue.toFixed(1) + '%';
                      }
                      
                      labels.push({
                        position: position,
                        label: formattedLabel
                      });
                    }
                    
                    return labels;
                  };
                  
                  const xAxisLabels = generateXAxisLabels();
                  const yAxisLabels = generateYAxisLabels();
                  
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
                  {/* Grid lines */}
                  <line x1="0" y1="0" x2="100" y2="0" className="chart-grid-line" />
                  <line x1="0" y1="25" x2="100" y2="25" className="chart-grid-line" />
                  <line x1="0" y1="50" x2="100" y2="50" className="chart-grid-line" />
                  <line x1="0" y1="75" x2="100" y2="75" className="chart-grid-line" />
                  <line x1="0" y1="100" x2="100" y2="100" className="chart-grid-line" />
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
                  {/* Line path */}
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
                              ? chartHover.value.toFixed(2) + '%'
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

              {isExpanded && (
                <div className="indicator-expanded">
                  {isLoading && (
                    <div className="indicator-loading">
                      <div className="loading-spinner"></div>
                    </div>
                  )}
                  <div className={`indicator-expanded-content ${isLoading ? 'loading' : ''}`}>
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

                    {(indicator.source || indicator.asOf || indicator.frequency) && (
                      <div className="indicator-expanded-section">
                        <div className="indicator-section-title">Data source</div>
                        <div className="indicator-metadata">
                          {indicator.source && (
                            <div className="metadata-item">
                              <span className="metadata-label">Source:</span>
                              <span className="metadata-value">
                                {indicator.sourceUrl ? (
                                  <a 
                                    href={indicator.sourceUrl} 
                                    target="_blank" 
                                    rel="noopener noreferrer"
                                    className="source-link"
                                  >
                                    {indicator.source}
                                  </a>
                                ) : (
                                  indicator.source
                                )}
                              </span>
                            </div>
                          )}
                          {indicator.asOf && (
                            <div className="metadata-item">
                              <span className="metadata-label">Last updated:</span>
                              <span className="metadata-value">{indicator.asOf}</span>
                            </div>
                          )}
                          {indicator.frequency && (
                            <div className="metadata-item">
                              <span className="metadata-label">Release frequency:</span>
                              <span className="metadata-value">{indicator.frequency}</span>
                            </div>
                          )}
                          {indicator.notes && (
                            <div className="metadata-item">
                              <span className="metadata-label">Notes:</span>
                              <span className="metadata-value">{indicator.notes}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

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
