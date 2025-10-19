import React from 'react';
import './Economies.css';

function Economies() {
  // Central bank rates data (will move to backend later)
  const centralBankRates = [
    {
      flag: '🇺🇸',
      country: 'USA',
      rate: 4.25,
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
          {/* Card content will be added here */}
        </div>
      </div>
    </div>
  );
}

export default Economies;

