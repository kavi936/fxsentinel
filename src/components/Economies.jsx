import React, { useMemo, useState } from 'react';
import './Economies.css';

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
        {data.indicators.map((indicator) => (
          <div key={indicator.id} className="indicator-card">
            <div className="indicator-header">
              <div className="indicator-title">{indicator.title}</div>
              <div className="indicator-value">{indicator.currentValue}</div>
            </div>
            <div className="indicator-description">{indicator.description}</div>
            <div className="indicator-chart">
              <div className="mini-chart">
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
                      className="chart-dot"
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
              </div>
              <div className="chart-label">{indicator.chartLabel}</div>
            </div>
          </div>
        ))}
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
