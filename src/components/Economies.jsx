import React, { useMemo, useState } from 'react';
import './Economies.css';

const indicatorDetails = {
  'interest-rate': {
    overview:
      'Policy rates define the cost of overnight liquidity for commercial banks and anchor the entire short-end of the yield curve. Traders watch the path of policy rates to gauge how restrictive or accommodative a central bank stance is relative to inflation and growth.',
    measurement:
      'Measured as the target rate (or target range midpoint) announced at scheduled central bank policy meetings. It reflects the price banks pay to borrow reserves and is communicated via official statements, minutes, and press conferences.',
    impact:
      'Higher policy rates typically attract capital inflows by improving local yield advantage, which can lift the currency. Conversely, rate cuts or guidance towards lower rates often weaken the currency as investors seek higher returns elsewhere.',
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
      rate: 4.00,
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
  const [chartHover, setChartHover] = useState(null);
  const economyData = useMemo(() => ({
    US: {
      flag: '🇺🇸',
      name: 'United States',
      description:
        'Data sources: Federal Reserve (FRED), Bureau of Labor Statistics, BEA. The US economy is a diversified, consumer-driven economy with significant services output, deep financial markets, and the USD as the world\'s reserve currency. Key drivers: labor market strength, consumer spending, credit conditions, and Fed policy.',
      indicators: [
        {
          id: 'interest-rate',
          title: 'Interest Rate',
          currentValue: '4.25%',
          description: 'Federal Funds Rate - Key monetary policy tool',
          chartData: [85, 78, 82, 88, 92, 89, 87, 90],
          chartLabel: 'Last 8 months'
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
  }), []);

  const data = economyData[selectedEconomy] || economyData.US;
  const toggleIndicatorCard = (indicatorId) => {
    setExpandedIndicatorId((prev) => (prev === indicatorId ? null : indicatorId));
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

    const label = typeof indicator.chartLabel === 'string' ? indicator.chartLabel : 'recent trend';

    return [
      `${indicator.title} is under review relative to its ${label.toLowerCase()} trajectory.`,
      'Change-rate, percentile, and consensus comparisons will appear here once live data integrates.',
      'Holistic Scan will merge this indicator with broader macro drivers in the upcoming release.',
    ];
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
    };
  };

  const handleChartHover = (indicatorId, event, chartData) => {
    if (!Array.isArray(chartData) || chartData.length === 0) {
      return;
    }

    const rect = event.currentTarget.getBoundingClientRect();
    const relativeX = Math.min(Math.max((event.clientX - rect.left) / rect.width, 0), 1);
    const lastIndex = chartData.length - 1;
    const index = Math.round(relativeX * lastIndex);
    const value = chartData[index];

    const xPercent = lastIndex === 0 ? 0 : (index / lastIndex) * 100;
    const yPercent = 100 - value;

    setChartHover({
      indicatorId,
      index,
      value,
      xPercent,
      yPercent,
    });
  };

  const clearChartHover = () => {
    setChartHover(null);
  };

  // Generate SVG path for line chart
  const generateLinePath = (data) => {
    if (data.length === 0) return '';
    
    const points = data.map((value, index) => {
      const x = (index / (data.length - 1)) * 100;
      const y = 100 - value;
      return `${x},${y}`;
    });
    
    return `M ${points.join(' L ')}`;
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
          const { overview, measurement, impact } = getIndicatorDetails(indicator);

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
                <div
                  className="mini-chart"
                  onMouseMove={(event) => handleChartHover(indicator.id, event, indicator.chartData)}
                  onMouseLeave={clearChartHover}
                >
                  <svg className="chart-line" viewBox="0 0 100 100" preserveAspectRatio="none">
                    <path 
                      className="chart-path"
                      d={generateLinePath(indicator.chartData)}
                    />
                  </svg>
                  <div className="chart-dots">
                    {generateDotPositions(indicator.chartData).map((position, index) => (
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
                    <div className="chart-label-x" style={{ left: '0%' }}>0</div>
                    <div className="chart-label-x" style={{ left: '50%' }}>4</div>
                    <div className="chart-label-x" style={{ left: '100%' }}>8</div>
                    <div className="chart-label-y" style={{ top: '0%' }}>100</div>
                    <div className="chart-label-y" style={{ top: '50%' }}>50</div>
                    <div className="chart-label-y" style={{ top: '100%' }}>0</div>
                  </div>
                  {chartHover && chartHover.indicatorId === indicator.id && (
                    <div
                      className="chart-tooltip"
                      style={{
                        left: `${chartHover.xPercent}%`,
                        top: `${chartHover.yPercent}%`,
                      }}
                    >
                      <div className="chart-tooltip-value">
                        {typeof chartHover.value === 'number'
                          ? chartHover.value.toFixed(1)
                          : chartHover.value}
                      </div>
                      <div className="chart-tooltip-index">Point {chartHover.index + 1}</div>
                    </div>
                  )}
                </div>
                <div className="chart-label">{indicator.chartLabel}</div>
              </div>

              {isExpanded && (
                <div className="indicator-expanded">
                  <div className="indicator-expanded-content">
                    <div className="indicator-expanded-section">
                      <div className="indicator-section-title">Key insights</div>
                      <ul className="indicator-insights-list">
                        {insightItems.map((insight, index) => (
                          <li key={index} className="indicator-insight-item">
                            {insight}
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div className="indicator-expanded-section">
                      <div className="indicator-section-title">Indicator overview</div>
                      <p className="indicator-section-text">{overview}</p>
                    </div>

                    <div className="indicator-expanded-section">
                      <div className="indicator-section-title">How it is measured</div>
                      <p className="indicator-section-text">{measurement}</p>
                    </div>

                    <div className="indicator-expanded-section">
                      <div className="indicator-section-title">Currency impact</div>
                      <p className="indicator-section-text">{impact}</p>
                    </div>
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
