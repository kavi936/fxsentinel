import React, { useState, useEffect } from 'react';
import { getUserTimezone, formatNewsTime, getTimezoneAbbreviation } from '../utils/timezoneUtils';

const TimezoneDebug = () => {
  const [currentTimezone, setCurrentTimezone] = useState(getUserTimezone());
  const [testTimestamp] = useState(new Date().toISOString());
  const [formattedTime, setFormattedTime] = useState('');

  useEffect(() => {
    const updateTime = () => {
      const tz = getUserTimezone();
      setCurrentTimezone(tz);
      setFormattedTime(formatNewsTime(testTimestamp, tz));
    };

    updateTime();
    const interval = setInterval(updateTime, 1000);

    return () => clearInterval(interval);
  }, [testTimestamp]);

  const testTimezones = [
    'UTC',
    'America/New_York',
    'Europe/London',
    'Asia/Tokyo',
    'Australia/Sydney',
    'Asia/Dubai' // GST timezone
  ];

  return (
    <div style={{
      position: 'fixed',
      top: '10px',
      right: '10px',
      background: 'rgba(0, 0, 0, 0.9)',
      color: 'white',
      padding: '15px',
      borderRadius: '8px',
      fontSize: '12px',
      zIndex: 10000,
      maxWidth: '300px',
      fontFamily: 'monospace'
    }}>
      <h4 style={{ margin: '0 0 10px 0', color: '#22c55e' }}>🌍 Timezone Debug</h4>
      
      <div style={{ marginBottom: '10px' }}>
        <strong>Current Timezone:</strong> {currentTimezone}
      </div>
      
      <div style={{ marginBottom: '10px' }}>
        <strong>Abbreviation:</strong> {getTimezoneAbbreviation(currentTimezone)}
      </div>
      
      <div style={{ marginBottom: '10px' }}>
        <strong>Test Time:</strong> {formattedTime}
      </div>
      
      <div style={{ marginBottom: '10px' }}>
        <strong>Raw Timestamp:</strong> {testTimestamp}
      </div>
      
      <div style={{ marginTop: '15px' }}>
        <strong>Test Different Timezones:</strong>
        {testTimezones.map(tz => (
          <div key={tz} style={{ marginTop: '5px' }}>
            {tz}: {formatNewsTime(testTimestamp, tz)}
          </div>
        ))}
      </div>
      
      <div style={{ marginTop: '15px', fontSize: '10px', color: '#888' }}>
        This debug panel will help you verify timezone conversion is working.
        Remove this component when testing is complete.
      </div>
      
      <div style={{ marginTop: '10px', padding: '10px', background: 'rgba(255,255,255,0.1)', borderRadius: '4px' }}>
        <strong>Manual Test:</strong>
        <button 
          onClick={() => {
            const testTime = new Date().toISOString();
            console.log('=== TIMEZONE TEST ===');
            console.log('Test timestamp:', testTime);
            console.log('Current timezone:', getUserTimezone());
            console.log('Formatted time:', formatNewsTime(testTime, getUserTimezone()));
            console.log('===================');
          }}
          style={{ 
            background: '#22c55e', 
            color: 'white', 
            border: 'none', 
            padding: '5px 10px', 
            borderRadius: '4px', 
            marginTop: '5px',
            cursor: 'pointer'
          }}
        >
          Test Timezone Conversion
        </button>
      </div>
    </div>
  );
};

export default TimezoneDebug;
