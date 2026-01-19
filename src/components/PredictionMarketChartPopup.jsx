import React, { useState, useEffect } from 'react';
import { config } from '../config.js';
import './EconomicChartPopup.css';

const PredictionMarketChartPopup = ({ market, isOpen, onClose }) => {
  const [chartData, setChartData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedInterval, setSelectedInterval] = useState('max');
  const [selectedFidelity, setSelectedFidelity] = useState(60);
  const [tooltip, setTooltip] = useState(null);

  useEffect(() => {
    if (isOpen && market) {
      fetchChartData();
    }
  }, [isOpen, market, selectedInterval, selectedFidelity]);

  const fetchChartData = async () => {
    if (!market) return;

    setLoading(true);
    setError(null);

    try {
      const clobTokenIds = market.clob_token_ids;
      if (!clobTokenIds || !Array.isArray(clobTokenIds) || clobTokenIds.length === 0) {
        setError('No CLOB token ID available for this market. Historical data is only available for Polymarket markets.');
        setLoading(false);
        return;
      }

      // Use first token ID (usually "Yes" token)
      const clobTokenId = clobTokenIds[0];
      const url = `${config.endpoints.predictionMarketHistory(market.id)}?clob_token_id=${clobTokenId}&interval=${selectedInterval}&fidelity=${selectedFidelity}`;
      
      console.log('🔍 Fetching price history for market:', market.question);
      console.log('🔍 URL:', url);

      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('🔍 Response data:', data);

      if (data.status === 'success' && data.data && data.data.history) {
        console.log('✅ Price history received:', data.data.history.length, 'points');
        setChartData(data.data);
      } else {
        setError(data.error || 'No historical data available');
      }
    } catch (err) {
      console.error('❌ Error fetching price history:', err);
      setError('Failed to load historical data');
    } finally {
      setLoading(false);
    }
  };

  const renderChart = () => {
    try {
      if (!chartData || !chartData.history || chartData.history.length === 0) {
        return (
          <div className="no-chart-data">
            <div className="no-data-icon">📊</div>
            <p>No historical data available</p>
            <p className="no-data-subtext">Try selecting a different interval</p>
          </div>
        );
      }

      const data = chartData.history;
      
      // Filter out invalid data points
      const validData = data.filter(point => 
        point && 
        point.yes_price !== null && 
        point.yes_price !== undefined && 
        typeof point.yes_price === 'number' && 
        !isNaN(point.yes_price) &&
        point.timestamp
      );

      if (validData.length === 0) {
        return (
          <div className="no-chart-data">
            <div className="no-data-icon">⚠️</div>
            <p>No valid price data available</p>
          </div>
        );
      }

      // Sort by timestamp
      const sortedData = [...validData].sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

      // Chart dimensions
      const width = 700;
      const height = 400;
      const padding = { top: 50, right: 50, bottom: 80, left: 80 };
      const chartWidth = width - padding.left - padding.right;
      const chartHeight = height - padding.top - padding.bottom;

      // Calculate Y scale (0-100% for probabilities)
      const minPrice = 0;
      const maxPrice = 100;
      const priceRange = maxPrice - minPrice;

      // Calculate X positions
      const xStep = chartWidth / (sortedData.length - 1 || 1);
      const points = sortedData.map((point, index) => {
        const x = padding.left + (index * xStep);
        const yesPricePercent = point.yes_price * 100; // Convert to percentage
        const y = padding.top + ((maxPrice - yesPricePercent) / priceRange) * chartHeight;
        return { ...point, x, y, yesPricePercent };
      });

      // Create path for line
      const linePath = points.map((point, index) => 
        `${index === 0 ? 'M' : 'L'} ${point.x} ${point.y}`
      ).join(' ');

      // Create area path (fill under line)
      const areaPath = `${linePath} L ${points[points.length - 1].x} ${padding.top + chartHeight} L ${points[0].x} ${padding.top + chartHeight} Z`;

      // Format timestamp for display
      const formatDate = (timestamp) => {
        const date = new Date(timestamp);
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
      };

      // Get Y-axis labels (0%, 25%, 50%, 75%, 100%)
      const yAxisLabels = [0, 25, 50, 75, 100].map(percent => ({
        value: percent,
        y: padding.top + ((maxPrice - percent) / priceRange) * chartHeight
      }));

      // Get X-axis labels (first, middle, last)
      const xAxisLabels = [];
      if (sortedData.length > 0) {
        xAxisLabels.push({ index: 0, label: formatDate(sortedData[0].timestamp) });
        if (sortedData.length > 1) {
          const midIndex = Math.floor(sortedData.length / 2);
          xAxisLabels.push({ index: midIndex, label: formatDate(sortedData[midIndex].timestamp) });
        }
        if (sortedData.length > 2) {
          xAxisLabels.push({ index: sortedData.length - 1, label: formatDate(sortedData[sortedData.length - 1].timestamp) });
        }
      }

      return (
        <div className="chart-container">
          <div className="chart-header">
            <h3>{market.question}</h3>
            <div className="chart-stats">
              <div className="stat-card">
                <div className="stat-label">Current Probability</div>
                <div className="stat-value">
                  {points.length > 0 ? `${points[points.length - 1].yesPricePercent.toFixed(1)}%` : 'N/A'}
                </div>
                {points.length > 1 && (
                  <div className="stat-change">
                    {(() => {
                      const latest = points[points.length - 1].yesPricePercent;
                      const previous = points[points.length - 2].yesPricePercent;
                      const change = latest - previous;
                      return (
                        <span className={change >= 0 ? 'positive' : 'negative'}>
                          {change >= 0 ? '+' : ''}{change.toFixed(1)}%
                        </span>
                      );
                    })()}
                  </div>
                )}
              </div>
              <div className="stat-card">
                <div className="stat-label">Average</div>
                <div className="stat-value">
                  {(() => {
                    const avg = points.reduce((sum, p) => sum + p.yesPricePercent, 0) / points.length;
                    return `${avg.toFixed(1)}%`;
                  })()}
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Range</div>
                <div className="stat-value">
                  {(() => {
                    const prices = points.map(p => p.yesPricePercent);
                    const min = Math.min(...prices);
                    const max = Math.max(...prices);
                    return `${min.toFixed(1)}% - ${max.toFixed(1)}%`;
                  })()}
                </div>
              </div>
            </div>
          </div>

          <div className="chart-controls">
            <div className="timeframe-selector">
              <label>Interval:</label>
              <select value={selectedInterval} onChange={(e) => setSelectedInterval(e.target.value)}>
                <option value="1h">Last Hour</option>
                <option value="6h">Last 6 Hours</option>
                <option value="1d">Last Day</option>
                <option value="1w">Last Week</option>
                <option value="max">All Time</option>
              </select>
            </div>
            <div className="fidelity-selector">
              <label>Resolution:</label>
              <select value={selectedFidelity} onChange={(e) => setSelectedFidelity(parseInt(e.target.value))}>
                <option value="10">10 minutes</option>
                <option value="30">30 minutes</option>
                <option value="60">1 hour</option>
                <option value="240">4 hours</option>
                <option value="1440">1 day</option>
              </select>
            </div>
          </div>

          <div className="chart-wrapper" style={{ position: 'relative' }}>
            <svg width={width} height={height} style={{ background: 'transparent' }}>
              <defs>
                <linearGradient id="pm-chart-gradient" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stopColor="rgba(59, 130, 246, 0.4)" />
                  <stop offset="100%" stopColor="rgba(59, 130, 246, 0)" />
                </linearGradient>
              </defs>

              {/* Grid lines */}
              {yAxisLabels.map((label, idx) => (
                <line
                  key={`grid-${idx}`}
                  x1={padding.left}
                  y1={label.y}
                  x2={width - padding.right}
                  y2={label.y}
                  stroke="rgba(255, 255, 255, 0.1)"
                  strokeWidth="1"
                />
              ))}

              {/* Area fill */}
              <path
                d={areaPath}
                fill="url(#pm-chart-gradient)"
              />

              {/* Line */}
              <path
                d={linePath}
                fill="none"
                stroke="#3b82f6"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />

              {/* Data points */}
              {points.map((point, index) => (
                <circle
                  key={index}
                  cx={point.x}
                  cy={point.y}
                  r="3"
                  fill="#60a5fa"
                  style={{ cursor: 'pointer' }}
                  onMouseEnter={(e) => {
                    const rect = e.currentTarget.getBoundingClientRect();
                    setTooltip({
                      x: rect.left,
                      y: rect.top - 10,
                      value: `${point.yesPricePercent.toFixed(1)}%`,
                      date: formatDate(point.timestamp)
                    });
                  }}
                  onMouseLeave={() => setTooltip(null)}
                />
              ))}

              {/* Y-axis labels */}
              {yAxisLabels.map((label, idx) => (
                <text
                  key={`y-label-${idx}`}
                  x={padding.left - 10}
                  y={label.y + 4}
                  textAnchor="end"
                  fill="rgba(255, 255, 255, 0.6)"
                  fontSize="12"
                >
                  {label.value}%
                </text>
              ))}

              {/* X-axis labels */}
              {xAxisLabels.map((label, idx) => {
                const point = points[label.index];
                if (!point) return null;
                return (
                  <text
                    key={`x-label-${idx}`}
                    x={point.x}
                    y={height - padding.bottom + 20}
                    textAnchor="middle"
                    fill="rgba(255, 255, 255, 0.6)"
                    fontSize="12"
                  >
                    {label.label}
                  </text>
                );
              })}
            </svg>

            {/* Tooltip */}
            {tooltip && (
              <div
                className="chart-tooltip"
                style={{
                  position: 'absolute',
                  left: tooltip.x,
                  top: tooltip.y,
                  transform: 'translate(-50%, -100%)',
                  background: 'rgba(0, 0, 0, 0.9)',
                  color: '#fff',
                  padding: '8px 12px',
                  borderRadius: '6px',
                  fontSize: '12px',
                  pointerEvents: 'none',
                  zIndex: 1000
                }}
              >
                <div>{tooltip.date}</div>
                <div style={{ fontWeight: 'bold', marginTop: '4px' }}>YES: {tooltip.value}</div>
              </div>
            )}
          </div>
        </div>
      );
    } catch (err) {
      console.error('Error rendering chart:', err);
      return (
        <div className="no-chart-data">
          <div className="no-data-icon">⚠️</div>
          <p>Error rendering chart</p>
        </div>
      );
    }
  };

  if (!isOpen) return null;

  return (
    <div className="chart-popup-overlay" onClick={onClose}>
      <div className="chart-popup" onClick={(e) => e.stopPropagation()}>
        <div className="chart-popup-header">
          <h2>Price History</h2>
          <button className="chart-popup-close" onClick={onClose}>×</button>
        </div>
        <div className="chart-popup-content">
          {loading && (
            <div className="chart-loading">
              <div className="loading-spinner"></div>
              <p>Loading price history...</p>
            </div>
          )}
          {error && (
            <div className="chart-error">
              <div className="error-icon">⚠️</div>
              <p>{error}</p>
            </div>
          )}
          {!loading && !error && renderChart()}
        </div>
      </div>
    </div>
  );
};

export default PredictionMarketChartPopup;

