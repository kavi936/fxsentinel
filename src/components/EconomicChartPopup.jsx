import React, { useState, useEffect } from 'react';
import { config } from '../config.js';
import './EconomicChartPopup.css';

const EconomicChartPopup = ({ event, isOpen, onClose }) => {
  const [chartData, setChartData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedTimeframe, setSelectedTimeframe] = useState(12);
  const [tooltip, setTooltip] = useState(null);

  useEffect(() => {
    console.log('🔍 Chart popup useEffect triggered:', { isOpen, event: event?.title });
    if (isOpen && event) {
      console.log('🔍 Starting to fetch chart data for:', event.title);
      fetchChartData();
    }
  }, [isOpen, event, selectedTimeframe]);

  const fetchChartData = async () => {
    if (!event) return;

    setLoading(true);
    setError(null);

    try {
      // Encode the event title for URL
      const encodedEventName = encodeURIComponent(event.title);
      const url = `${config.endpoints.economicChart}/${encodedEventName}?months=${selectedTimeframe}`;
      
      console.log('🔍 Fetching chart data for event:', event.title);
      console.log('🔍 URL:', url);

      const response = await fetch(url);
      console.log('🔍 Response status:', response.status);
      
      const data = await response.json();
      console.log('🔍 Response data:', data);

      if (data.status === 'success' && data.chart_data) {
        console.log('✅ Chart data received:', data.chart_data);
        setChartData(data.chart_data);
      } else {
        console.log('❌ No chart data:', data.message);
        setError(data.message || 'No historical data available');
      }
    } catch (err) {
      console.error('❌ Error fetching chart data:', err);
      setError('Failed to load historical data');
    } finally {
      setLoading(false);
    }
  };

  const formatValue = (value, unit) => {
    if (value === null || value === undefined) return 'N/A';
    
    // Format based on unit type with proper rounding
    if (typeof value === 'number') {
      if (unit === '%') {
        return `${value.toFixed(3)}%`;
      } else {
        return value.toFixed(3);
      }
    }
    return value.toString();
  };

  const renderChart = () => {
    try {
      if (!chartData || !chartData.historical_data || chartData.historical_data.length === 0) {
        return (
          <div className="no-chart-data">
            <div className="no-data-icon">📊</div>
            <p>No historical data available</p>
            <p className="no-data-subtext">Try selecting a different timeframe or event</p>
          </div>
        );
      }

      const data = chartData.historical_data;
      
      // Filter out any invalid data points and ensure all values are numbers
      const validData = data.filter(point => 
        point && 
        point.value !== null && 
        point.value !== undefined && 
        typeof point.value === 'number' && 
        !isNaN(point.value) &&
        point.date // Ensure date exists
      );

      if (validData.length === 0) {
        return (
          <div className="no-chart-data">
            <div className="no-data-icon">⚠️</div>
            <p>No valid numeric data available</p>
            <p className="no-data-subtext">All data points contain invalid values</p>
          </div>
        );
      }

      // Sort data by date to ensure chronological order
      const sortedData = [...validData].sort((a, b) => new Date(a.date) - new Date(b.date));
      
      // Remove any remaining duplicates by date (in case backend didn't catch all)
      const uniqueData = [];
      const seenDates = new Set();
      for (const point of sortedData) {
        if (!seenDates.has(point.date)) {
          seenDates.add(point.date);
          uniqueData.push(point);
        }
      }

      if (uniqueData.length === 0) {
        return (
          <div className="no-chart-data">
            <div className="no-data-icon">⚠️</div>
            <p>No unique data points available</p>
            <p className="no-data-subtext">All data points have duplicate dates</p>
          </div>
        );
      }

      // Additional validation: check for reasonable data ranges
      const values = uniqueData.map(d => d.value);
      const maxValue = Math.max(...values);
      const minValue = Math.min(...values);
      
      // Check for extreme values that might indicate data quality issues
      const extremeValues = values.filter(v => Math.abs(v) > 50);
      if (extremeValues.length > 0) {
        console.warn('⚠️ Extreme values detected:', extremeValues);
      }

      const range = maxValue - minValue || 1; // Prevent division by zero

      // Determine value type and formatting
      const valueType = determineValueType(uniqueData[0]?.unit, uniqueData[0]?.value);
      const chartConfig = getChartConfig(valueType, minValue, maxValue, range);

      // Add debugging information
      console.log('Chart Data Debug:', {
        totalPoints: data.length,
        validPoints: validData.length,
        uniquePoints: uniqueData.length,
        minValue,
        maxValue,
        range,
        valueType,
        sampleValues: values.slice(0, 5),
        sampleDates: uniqueData.slice(0, 5).map(d => d.date),
        extremeValuesCount: extremeValues.length
      });

      return (
        <div className="chart-container">
          <div className="chart-header">
            <h3>{chartData.indicator} Historical Data</h3>
            <div className="chart-stats">
              <div className="stat-card">
                <div className="stat-label">Latest Value</div>
                <div className="stat-value">{formatValue(uniqueData[uniqueData.length - 1]?.value, uniqueData[0]?.unit)}</div>
                {uniqueData.length > 1 && (
                  <div className="stat-change">
                    {(() => {
                      const latest = uniqueData[uniqueData.length - 1].value;
                      const previous = uniqueData[uniqueData.length - 2].value;
                      const change = latest - previous;
                      const changePercent = (change / previous) * 100;
                      return (
                        <span className={change >= 0 ? 'positive' : 'negative'}>
                          {change >= 0 ? '+' : ''}{formatValue(change, uniqueData[0]?.unit)} ({changePercent >= 0 ? '+' : ''}{changePercent.toFixed(2)}%)
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
                    const avg = uniqueData.reduce((sum, d) => sum + d.value, 0) / uniqueData.length;
                    return formatValue(avg, uniqueData[0]?.unit);
                  })()}
                </div>
                <div className="stat-subtitle">{selectedTimeframe}-month average</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Range</div>
                <div className="stat-value">
                  {formatValue(minValue, uniqueData[0]?.unit)} - {formatValue(maxValue, uniqueData[0]?.unit)}
                </div>
                <div className="stat-subtitle">Min to Max</div>
              </div>
            </div>
          </div>

          <div className="chart-visualization">
            <div className="chart-grid">
              {/* Y-axis labels */}
              <div className="y-axis">
                {generateYAxisLabels(chartConfig, uniqueData[0]?.unit, uniqueData)}
              </div>
              
              {/* Chart area */}
              <div className="chart-area">
                {/* Grid lines */}
                <div className="grid-lines">
                  {Array.from({ length: chartConfig.gridLines }, (_, i) => (
                    <div key={i} className="grid-line" />
                  ))}
                </div>
                
                {/* Chart type specific rendering */}
                {renderChartType(uniqueData, chartConfig, valueType)}
                
                {/* Enhanced Professional Tooltip */}
                {tooltip && (
                  <div 
                    className="chart-tooltip professional"
                    style={{
                      position: 'absolute',
                      left: `${tooltip.x}px`,
                      top: `${tooltip.y - 80}px`,
                      transform: 'translateX(-50%)',
                      zIndex: 1000
                    }}
                  >
                    <div className="tooltip-header">
                      <strong>{tooltip.value}</strong>
                      {tooltip.isOutlier && <span className="outlier-badge">OUTLIER</span>}
                    </div>
                    <div className="tooltip-date">{tooltip.date}</div>
                    <div className="tooltip-expected">
                      Expected: <span>{tooltip.expected}</span>
                    </div>
                    <div className="tooltip-actual">
                      Actual: <span>{tooltip.actual}</span>
                    </div>
                    {tooltip.change !== 'N/A' && (
                      <div className="tooltip-change">
                        Change: <span className={tooltip.change >= 0 ? 'positive' : 'negative'}>
                          {tooltip.change >= 0 ? '+' : ''}{tooltip.change}
                        </span>
                      </div>
                    )}
                    {tooltip.isOutlier && (
                      <div className="tooltip-warning">
                        ⚠️ Statistical outlier detected
                      </div>
                    )}
                  </div>
                )}
              </div>
              
              {/* X-axis labels */}
              <div className="x-axis">
                {generateXAxisLabels(uniqueData)}
              </div>
            </div>
          </div>

          <div className="chart-footer">
            <p>Showing {uniqueData.length} data points over {chartData.timeframe}</p>
            <p>Data source: Finnhub Economic Calendar</p>
            <p className="value-type-info">Value type: {valueType.name} ({valueType.description})</p>
            {data.length !== uniqueData.length && (
              <p style={{color: '#ffa500', fontSize: '12px'}}>
                ⚠️ Filtered out {data.length - uniqueData.length} invalid/duplicate data points
              </p>
            )}
            {extremeValues.length > 0 && (
              <p style={{color: '#ff6b6b', fontSize: '12px'}}>
                ⚠️ {extremeValues.length} extreme values detected - data quality may be affected
              </p>
            )}
          </div>
        </div>
      );
    } catch (error) {
      console.error('Error rendering chart:', error);
      return (
        <div className="chart-error">
          <div className="error-icon">⚠️</div>
          <p>Error rendering chart: {error.message}</p>
          <p className="error-subtext">Please try refreshing the page</p>
        </div>
      );
    }
  };

  // Helper functions for chart rendering
  const determineValueType = (unit, sampleValue) => {
    try {
      if (!unit && !sampleValue) return { name: 'Unknown', description: 'No unit information' };
      
      const unitLower = (unit || '').toLowerCase();
      const value = Math.abs(sampleValue || 0);
      
      // Percentage values (CPI, Unemployment, etc.)
      if (unitLower.includes('%') || unitLower.includes('percent') || 
          (value > 0 && value < 100 && unitLower === '')) {
        return { name: 'Percentage', description: 'Percentage values (0-100%)' };
      }
      
      // Large numbers (GDP, Employment numbers)
      if (value > 1000 || unitLower.includes('k') || unitLower.includes('thousand') ||
          unitLower.includes('million') || unitLower.includes('billion')) {
        return { name: 'Large Number', description: 'Large numeric values (thousands/millions)' };
      }
      
      // Small decimals (Interest rates, small percentages)
      if (value < 10 && value > 0) {
        return { name: 'Small Decimal', description: 'Small decimal values (0-10)' };
      }
      
      // Index values (PMI, etc.)
      if (unitLower.includes('index') || (value > 0 && value < 1000)) {
        return { name: 'Index', description: 'Index values (0-1000 range)' };
      }
      
      return { name: 'Numeric', description: 'General numeric values' };
    } catch (error) {
      console.error('Error determining value type:', error);
      return { name: 'Unknown', description: 'Error determining value type' };
    }
  };

  const getChartConfig = (valueType, minValue, maxValue, range) => {
    const baseConfig = {
      gridLines: 5,
      yAxisSteps: 5,
      dataPointRadius: 3,
      latestPointRadius: 4,
      strokeWidth: 2,
      showDataLabels: true,
      showTrendLine: true
    };

    switch (valueType.name) {
      case 'Percentage':
        return {
          ...baseConfig,
          yAxisSteps: 6,
          dataPointRadius: 4,
          latestPointRadius: 5,
          strokeWidth: 3,
          showTrendLine: true
        };
      
      case 'Large Number':
        return {
          ...baseConfig,
          gridLines: 4,
          yAxisSteps: 4,
          dataPointRadius: 2,
          latestPointRadius: 3,
          strokeWidth: 2,
          showDataLabels: false
        };
      
      case 'Small Decimal':
        return {
          ...baseConfig,
          yAxisSteps: 6,
          dataPointRadius: 3,
          latestPointRadius: 4,
          strokeWidth: 2,
          showTrendLine: true
        };
      
      case 'Index':
        return {
          ...baseConfig,
          gridLines: 5,
          yAxisSteps: 5,
          dataPointRadius: 3,
          latestPointRadius: 4,
          strokeWidth: 2
        };
      
      default:
        return baseConfig;
    }
  };

  const generateYAxisLabels = (config, unit, validData) => {
    try {
      const steps = config.yAxisSteps;
      const values = validData.map(d => d.value);
      const maxValue = Math.max(...values);
      const minValue = Math.min(...values);
      const range = maxValue - minValue || 1; // Prevent division by zero
      const stepValue = range / steps;
      
      return Array.from({ length: steps + 1 }, (_, i) => {
        const value = maxValue - (i * stepValue);
        const formattedValue = formatValue(value, unit);
        
        return (
          <div key={i} className="y-axis-label">
            {formattedValue}
          </div>
        );
      });
    } catch (error) {
      console.error('Error generating Y-axis labels:', error);
      return <div className="y-axis-label">Error</div>;
    }
  };

  const generateXAxisLabels = (validData) => {
    try {
      const maxLabels = 6;
      const step = Math.max(1, Math.floor(validData.length / maxLabels));
      
      const labels = validData
        .filter((_, index) => index % step === 0 || index === validData.length - 1)
        .slice(0, maxLabels)
        .map((point, index) => {
          const date = new Date(point.date);
          const formattedDate = date.toLocaleDateString('en-US', { 
            month: 'short', 
            year: '2-digit' 
          });
          
          return (
            <div key={index} className="x-axis-label">
              {formattedDate}
            </div>
          );
        });
      
      return labels;
    } catch (error) {
      console.error('Error generating X-axis labels:', error);
      return <div className="x-axis-label">Error</div>;
    }
  };

  const renderChartType = (validData, config, valueType) => {
    try {
      if (validData.length === 0) return <div>No data available</div>;
      
      // Data is already sorted and deduplicated from the parent function
      // Limit data points to prevent overcrowding - show max 24 points (2 years of monthly data)
      const maxPoints = Math.min(validData.length, 24);
      const displayData = validData.slice(-maxPoints); // Take the most recent points
      
      const values = displayData.map(d => d.value);
      const maxValue = Math.max(...values);
      const minValue = Math.min(...values);
      
      // Improve scaling for better visualization
      const range = maxValue - minValue;
      const rangePadding = 0.1; // Add 10% padding to the range
      const adjustedMin = minValue - (range * rangePadding);
      const adjustedMax = maxValue + (range * rangePadding);
      const adjustedRange = adjustedMax - adjustedMin || 1;
      
      // Chart dimensions
      const width = 700;
      const height = 400;
      const padding = { top: 50, right: 50, bottom: 80, left: 80 };
      const chartWidth = width - padding.left - padding.right;
      const chartHeight = height - padding.top - padding.bottom;
      
      // Calculate X positions - evenly spaced across the chart width
      const xStep = chartWidth / (displayData.length - 1);
      const points = displayData.map((point, index) => {
        const x = padding.left + (index * xStep);
        const y = padding.top + ((adjustedMax - point.value) / adjustedRange) * chartHeight;
        return { ...point, x, y };
      });
      
      // Create path for main data line
      const mainLinePath = points.map((point, index) => 
        `${index === 0 ? 'M' : 'L'} ${point.x} ${point.y}`
      ).join(' ');
      
      return (
        <svg width={width} height={height} style={{ background: 'transparent', position: 'relative' }}>
          {/* Background grid */}
          <defs>
            <pattern id="grid" width="50" height="50" patternUnits="userSpaceOnUse">
              <path d="M 50 0 L 0 0 0 50" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="1"/>
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />
          
          {/* Y-axis grid lines */}
          {Array.from({ length: 6 }, (_, i) => {
            const y = padding.top + (i * chartHeight / 5);
            return (
              <line
                key={`grid-y-${i}`}
                x1={padding.left}
                y1={y}
                x2={width - padding.right}
                y2={y}
                stroke="rgba(255,255,255,0.1)"
                strokeWidth="1"
              />
            );
          })}
          
          {/* Main data line */}
          <path
            d={mainLinePath}
            fill="none"
            stroke="#FF4444"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          
          {/* Data points */}
          {points.map((point, index) => {
            const isLatest = index === points.length - 1;
            
            return (
              <g key={index} className="data-point">
                <circle
                  cx={point.x}
                  cy={point.y}
                  r={isLatest ? 6 : 4}
                  fill={isLatest ? "#FF6666" : "#FF4444"}
                  stroke={isLatest ? "#FFFFFF" : "none"}
                  strokeWidth={isLatest ? 2 : 0}
                  onMouseEnter={(e) => {
                    // Get the SVG container
                    const svg = e.currentTarget.closest('svg');
                    const svgRect = svg.getBoundingClientRect();
                    const circleRect = e.currentTarget.getBoundingClientRect();
                    
                    // Calculate position relative to SVG
                    const relativeX = circleRect.left - svgRect.left + circleRect.width / 2;
                    const relativeY = circleRect.top - svgRect.top;
                    
                    setTooltip({
                      x: relativeX,
                      y: relativeY,
                      value: formatValue(point.value, point.unit),
                      date: new Date(point.date).toLocaleDateString('en-GB', { 
                        day: '2-digit',
                        month: '2-digit',
                        year: '2-digit'
                      }),
                      expected: point.expected ? formatValue(point.expected, point.unit) : 'N/A',
                      actual: point.actual ? formatValue(point.actual, point.unit) : 'N/A',
                      isOutlier: false,
                      change: index > 0 ? (point.value - points[index - 1].value).toFixed(3) : 'N/A'
                    });
                  }}
                  onMouseLeave={() => setTooltip(null)}
                />
              </g>
            );
          })}
          
          {/* Y-axis */}
          <line
            x1={padding.left}
            y1={padding.top}
            x2={padding.left}
            y2={height - padding.bottom}
            stroke="rgba(255,255,255,0.3)"
            strokeWidth="2"
          />
          
          {/* X-axis */}
          <line
            x1={padding.left}
            y1={height - padding.bottom}
            x2={width - padding.right}
            y2={height - padding.bottom}
            stroke="rgba(255,255,255,0.3)"
            strokeWidth="2"
          />
          
          {/* Y-axis labels */}
          {Array.from({ length: 6 }, (_, i) => {
            const value = adjustedMin + (i * (adjustedRange / 5));
            const y = padding.top + ((adjustedMax - value) / adjustedRange) * chartHeight;
            return (
              <text
                key={`y-label-${i}`}
                x={padding.left - 10}
                y={y + 4}
                textAnchor="end"
                fontSize="12"
                fill="rgba(255,255,255,0.7)"
                fontWeight="500"
              >
                {formatValue(value, displayData[0]?.unit)}
              </text>
            );
          })}
          
          {/* X-axis labels - show every 4th label to avoid crowding */}
          {displayData.map((point, index) => {
            // Show every 4th label or the last one to avoid crowding
            if (index % 4 === 0 || index === displayData.length - 1) {
              const x = padding.left + (index * xStep);
              const date = new Date(point.date);
              const label = date.toLocaleDateString('en-GB', { 
                day: '2-digit',
                month: '2-digit',
                year: '2-digit'
              });
              
              return (
                <text
                  key={`x-label-${index}`}
                  x={x}
                  y={height - padding.bottom + 20}
                  textAnchor="middle"
                  fontSize="11"
                  fill="rgba(255,255,255,0.7)"
                  fontWeight="500"
                >
                  {label}
                </text>
              );
            }
            return null;
          })}
          
          {/* Chart title */}
          <text
            x={width / 2}
            y={25}
            textAnchor="middle"
            fontSize="16"
            fill="rgba(255,255,255,0.9)"
            fontWeight="600"
          >
            {chartData?.indicator || 'Historical Data'} Trend
          </text>
          
          {/* Data summary */}
          <text
            x={width / 2}
            y={height - 10}
            textAnchor="middle"
            fontSize="11"
            fill="rgba(255,255,255,0.5)"
            fontWeight="400"
          >
            Showing {displayData.length} of {validData.length} data points
          </text>
        </svg>
      );
    } catch (error) {
      console.error('Error rendering chart:', error);
      return <div>Error rendering chart</div>;
    }
  };

  // Advanced trading analysis functions
  const detectOutliers = (values, data) => {
    try {
      const mean = values.reduce((a, b) => a + b, 0) / values.length;
      const variance = values.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / values.length;
      const stdDev = Math.sqrt(variance);
      const threshold = 2.5; // 2.5 standard deviations
      
      const outliers = [];
      const cleanData = [];
      
      data.forEach((point, index) => {
        const zScore = Math.abs((point.value - mean) / stdDev);
        if (zScore > threshold) {
          outliers.push({ index, value: point.value, zScore });
        } else {
          cleanData.push(point);
        }
      });
      
      return {
        cleanData,
        outliers,
        statistics: { mean, stdDev, threshold }
      };
    } catch (error) {
      console.error('Error detecting outliers:', error);
      return { cleanData: data, outliers: [], statistics: {} };
    }
  };

  const calculateMovingAverage = (values, period) => {
    try {
      if (values.length < period) return [];
      
      const result = [];
      for (let i = period - 1; i < values.length; i++) {
        const sum = values.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0);
        result.push(sum / period);
      }
      return result;
    } catch (error) {
      console.error('Error calculating moving average:', error);
      return [];
    }
  };

  const calculateVolatility = (values) => {
    try {
      if (values.length < 2) return 0;
      
      const returns = [];
      for (let i = 1; i < values.length; i++) {
        returns.push((values[i] - values[i - 1]) / values[i - 1]);
      }
      
      const meanReturn = returns.reduce((a, b) => a + b, 0) / returns.length;
      const variance = returns.reduce((a, b) => a + Math.pow(b - meanReturn, 2), 0) / returns.length;
      return Math.sqrt(variance);
    } catch (error) {
      console.error('Error calculating volatility:', error);
      return 0;
    }
  };

  const calculateTrend = (values) => {
    try {
      if (values.length < 2) return { direction: 'neutral', strength: 0 };
      
      const firstHalf = values.slice(0, Math.floor(values.length / 2));
      const secondHalf = values.slice(Math.floor(values.length / 2));
      
      const firstAvg = firstHalf.reduce((a, b) => a + b, 0) / firstHalf.length;
      const secondAvg = secondHalf.reduce((a, b) => a + b, 0) / secondHalf.length;
      
      const change = ((secondAvg - firstAvg) / firstAvg) * 100;
      const strength = Math.abs(change);
      
      return {
        direction: change > 1 ? 'up' : change < -1 ? 'down' : 'neutral',
        strength: Math.round(strength)
      };
    } catch (error) {
      console.error('Error calculating trend:', error);
      return { direction: 'neutral', strength: 0 };
    }
  };

  if (!isOpen) return null;

  return (
    <div className="chart-popup-overlay" onClick={onClose}>
      <div className="chart-popup" onClick={(e) => e.stopPropagation()}>
        <div className="chart-popup-header">
          <h2>Historical Data: {event?.title}</h2>
          <button className="close-button" onClick={onClose}>×</button>
        </div>

        <div className="chart-controls">
          <div className="timeframe-selector">
            <label>Historical Data Period:</label>
            <div className="timeframe-buttons">
              <button 
                className={`timeframe-btn ${selectedTimeframe === 6 ? 'active' : ''}`}
                onClick={() => setSelectedTimeframe(6)}
              >
                6 Months
              </button>
              <button 
                className={`timeframe-btn ${selectedTimeframe === 12 ? 'active' : ''}`}
                onClick={() => setSelectedTimeframe(12)}
              >
                1 Year
              </button>
              <button 
                className={`timeframe-btn ${selectedTimeframe === 24 ? 'active' : ''}`}
                onClick={() => setSelectedTimeframe(24)}
              >
                2 Years
              </button>
            </div>
          </div>
          

        </div>

        <div className="chart-content">
          {loading && (
            <div className="loading-chart">
              <div className="loading-spinner"></div>
              <p>Loading historical data...</p>
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

export default EconomicChartPopup;

