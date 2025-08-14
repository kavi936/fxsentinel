import React, { useState, useEffect } from 'react';
import { config } from '../config.js';
import './EconomicChartPopup.css';

const EconomicChartPopup = ({ event, isOpen, onClose }) => {
  const [chartData, setChartData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedTimeframe, setSelectedTimeframe] = useState(12);

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
    
    // Format based on unit type
    if (unit === '%') {
      return `${value}%`;
    } else if (typeof value === 'number') {
      return value.toLocaleString();
    }
    return value.toString();
  };

  const renderChart = () => {
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
      point.value !== null && 
      point.value !== undefined && 
      typeof point.value === 'number' && 
      !isNaN(point.value)
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

    // Calculate statistics on valid data only
    const values = validData.map(d => d.value);
    const maxValue = Math.max(...values);
    const minValue = Math.min(...values);
    const range = maxValue - minValue;

    // Add debugging information
    console.log('Chart Data Debug:', {
      totalPoints: data.length,
      validPoints: validData.length,
      minValue,
      maxValue,
      range,
      sampleValues: values.slice(0, 5)
    });

    return (
      <div className="chart-container">
        <div className="chart-header">
          <h3>{chartData.indicator} Historical Data</h3>
          <div className="chart-stats">
            <span className="stat">
              <strong>Latest:</strong> {formatValue(validData[0]?.value, validData[0]?.unit)}
            </span>
            <span className="stat">
              <strong>Average:</strong> {formatValue(chartData.statistics?.average, validData[0]?.unit)}
            </span>
            <span className="stat">
              <strong>Range:</strong> {formatValue(minValue, validData[0]?.unit)} - {formatValue(maxValue, validData[0]?.unit)}
            </span>
            <span className="stat">
              <strong>Trend:</strong> 
              <span className={`trend-${chartData.statistics?.trend || 'unknown'}`}>
                {chartData.statistics?.trend || 'Unknown'}
              </span>
            </span>
          </div>
        </div>

        <div className="chart-bars">
          {validData.slice(0, 20).map((point, index) => {
            // Calculate height percentage with better handling of edge cases
            let height;
            if (range === 0) {
              height = 50; // Default height for flat data
            } else {
              height = ((point.value - minValue) / range) * 100;
              // Ensure height is within reasonable bounds
              height = Math.max(5, Math.min(95, height));
            }
            
            const isLatest = index === 0;
            
            return (
              <div key={index} className="chart-bar-container">
                <div 
                  className={`chart-bar ${isLatest ? 'latest' : ''}`}
                  style={{ height: `${height}%` }}
                  title={`${point.date}: ${formatValue(point.value, point.unit)}`}
                >
                  <div className="bar-value">{formatValue(point.value, point.unit)}</div>
                </div>
                <div className="bar-date">{point.date}</div>
              </div>
            );
          })}
        </div>

        <div className="chart-footer">
          <p>Showing {validData.length} valid data points over {chartData.timeframe}</p>
          <p>Data source: Finnhub Economic Calendar</p>
          {data.length !== validData.length && (
            <p style={{color: '#ffa500', fontSize: '12px'}}>
              ⚠️ Filtered out {data.length - validData.length} invalid data points
            </p>
          )}
        </div>
      </div>
    );
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
          <label>Timeframe:</label>
          <select 
            value={selectedTimeframe} 
            onChange={(e) => setSelectedTimeframe(parseInt(e.target.value))}
          >
            <option value={6}>6 months</option>
            <option value={12}>12 months</option>
            <option value={24}>24 months</option>
          </select>
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
