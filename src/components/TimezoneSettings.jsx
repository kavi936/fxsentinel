import React, { useState, useEffect } from 'react';
import './TimezoneSettings.css';

const TimezoneSettings = ({ isOpen, onClose, onTimezoneChange }) => {
  const [selectedTimezone, setSelectedTimezone] = useState('');
  const [currentLocalTime, setCurrentLocalTime] = useState('');

  // Common timezones for forex traders
  const timezones = [
    { value: 'UTC', label: 'UTC (Coordinated Universal Time)' },
    { value: 'America/New_York', label: 'EST/EDT (Eastern Time)' },
    { value: 'America/Chicago', label: 'CST/CDT (Central Time)' },
    { value: 'America/Denver', label: 'MST/MDT (Mountain Time)' },
    { value: 'America/Los_Angeles', label: 'PST/PDT (Pacific Time)' },
    { value: 'Europe/London', label: 'GMT/BST (London)' },
    { value: 'Europe/Paris', label: 'CET/CEST (Central European)' },
    { value: 'Europe/Berlin', label: 'CET/CEST (Berlin)' },
    { value: 'Asia/Tokyo', label: 'JST (Japan Standard Time)' },
    { value: 'Asia/Shanghai', label: 'CST (China Standard Time)' },
    { value: 'Asia/Singapore', label: 'SGT (Singapore Time)' },
    { value: 'Australia/Sydney', label: 'AEST/AEDT (Sydney)' },
    { value: 'Australia/Melbourne', label: 'AEST/AEDT (Melbourne)' },
    { value: 'Pacific/Auckland', label: 'NZST/NZDT (New Zealand)' },
    { value: 'Asia/Dubai', label: 'GST (Gulf Standard Time)' },
    { value: 'Asia/Kolkata', label: 'IST (India Standard Time)' },
    { value: 'Asia/Seoul', label: 'KST (Korea Standard Time)' },
    { value: 'Asia/Bangkok', label: 'ICT (Indochina Time)' },
    { value: 'Europe/Moscow', label: 'MSK (Moscow Time)' },
    { value: 'Africa/Johannesburg', label: 'SAST (South Africa)' }
  ];

  useEffect(() => {
    // Load saved timezone on component mount
    const savedTimezone = localStorage.getItem('fxSentinel_userTimezone') || 'UTC';
    setSelectedTimezone(savedTimezone);
    
    // Update current local time every second
    const updateTime = () => {
      try {
        const now = new Date();
        const timeString = now.toLocaleTimeString('en-US', {
          timeZone: savedTimezone,
          hour12: false,
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit'
        });
        const dateString = now.toLocaleDateString('en-US', {
          timeZone: savedTimezone,
          weekday: 'short',
          year: 'numeric',
          month: 'short',
          day: 'numeric'
        });
        setCurrentLocalTime(`${dateString} ${timeString}`);
      } catch (error) {
        console.error('Error formatting time:', error);
        setCurrentLocalTime('Error displaying time');
      }
    };
    
    updateTime();
    const interval = setInterval(updateTime, 1000);
    
    return () => clearInterval(interval);
  }, []);

  const handleTimezoneChange = (timezone) => {
    setSelectedTimezone(timezone);
    localStorage.setItem('fxSentinel_userTimezone', timezone);
    
    if (onTimezoneChange) {
      onTimezoneChange(timezone);
    }
  };

  const detectUserTimezone = () => {
    try {
      const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
      if (userTimezone && timezones.some(tz => tz.value === userTimezone)) {
        handleTimezoneChange(userTimezone);
      } else {
        // If exact match not found, try to find a similar one
        const userOffset = new Date().getTimezoneOffset();
        const utcOffset = -userOffset / 60;
        
        // Find timezone with similar offset
        const similarTimezone = timezones.find(tz => {
          try {
            const tzDate = new Date().toLocaleString('en-US', { timeZone: tz.value });
            const tzOffset = new Date(tzDate).getTimezoneOffset();
            return Math.abs(tzOffset - userOffset) < 60; // Within 1 hour
          } catch {
            return false;
          }
        });
        
        if (similarTimezone) {
          handleTimezoneChange(similarTimezone.value);
        }
      }
    } catch (error) {
      console.error('Error detecting timezone:', error);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="timezone-settings-overlay" onClick={onClose}>
      <div className="timezone-settings-modal" onClick={(e) => e.stopPropagation()}>
        <div className="timezone-settings-header">
          <h3>Timezone Settings</h3>
          <button className="close-btn" onClick={onClose}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        
        <div className="timezone-settings-content">
          <div className="current-time-display">
            <h4>Current Local Time</h4>
            <div className="time-display">{currentLocalTime}</div>
            <div className="timezone-info">
              Selected: <strong>{selectedTimezone}</strong>
            </div>
          </div>
          
          <div className="timezone-selection">
            <div className="selection-header">
              <h4>Select Your Timezone</h4>
              <button className="detect-btn" onClick={detectUserTimezone}>
                Detect My Timezone
              </button>
            </div>
            
            <div className="timezone-list">
              {timezones.map((timezone) => (
                <label key={timezone.value} className="timezone-option">
                  <input
                    type="radio"
                    name="timezone"
                    value={timezone.value}
                    checked={selectedTimezone === timezone.value}
                    onChange={(e) => handleTimezoneChange(e.target.value)}
                  />
                  <span className="timezone-label">{timezone.label}</span>
                </label>
              ))}
            </div>
          </div>
          
          <div className="timezone-info-section">
            <h4>About Timezone Display</h4>
            <p>
              This setting will convert all news timestamps from UTC to your selected timezone. 
              News times will be displayed in your local time for easier reading.
            </p>
            <div className="example">
              <strong>Example:</strong> A news item published at "14:30 UTC" will show as 
              "09:30 EST" if you're in Eastern Time.
            </div>
          </div>
        </div>
        
        <div className="timezone-settings-footer">
          <button className="save-btn" onClick={onClose}>
            Save & Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default TimezoneSettings;
