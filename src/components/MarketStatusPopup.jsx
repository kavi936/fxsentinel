import React, { useState, useEffect } from 'react';
import './MarketStatusPopup.css';

const MarketStatusPopup = ({ isOpen, onClose, marketStatus }) => {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [tradingSessions, setTradingSessions] = useState([]);

  useEffect(() => {
    if (isOpen) {
      updateTradingSessions();
      const interval = setInterval(() => {
        setCurrentTime(new Date());
        updateTradingSessions();
      }, 1000);
      return () => clearInterval(interval);
    }
  }, [isOpen]);

  const updateTradingSessions = () => {
    const now = new Date();
    const utcHour = now.getUTCHours();
    const utcDay = now.getUTCDay();
    
    // Check if it's weekend
    const isWeekend = utcDay === 0 || utcDay === 6;
    
    // Check for major holidays
    const utcMonth = now.getUTCMonth();
    const utcDate = now.getUTCDate();
    
    const isHoliday = (
      (utcMonth === 0 && utcDate === 1) || // New Year's Day
      (utcMonth === 11 && utcDate === 25) || // Christmas Day
      (utcMonth === 11 && utcDate === 26) // Boxing Day
    );
    
    if (isWeekend || isHoliday) {
      setTradingSessions([]);
      return;
    }
    
    const sessions = [
      { 
        name: 'Sydney', 
        start: 22, 
        end: 7, 
        timezone: 'AEST', 
        color: '#4CAF50', 
        localStart: 22, 
        localEnd: 7,
        description: 'Australian & Asian markets'
      },
      { 
        name: 'Tokyo', 
        start: 0, 
        end: 9, 
        timezone: 'JST', 
        color: '#2196F3', 
        localStart: 0, 
        localEnd: 9,
        description: 'Japanese & Asian markets'
      },
      { 
        name: 'London', 
        start: 8, 
        end: 17, 
        timezone: 'GMT', 
        color: '#FF9800', 
        localStart: 8, 
        localEnd: 17,
        description: 'European markets'
      },
      { 
        name: 'New York', 
        start: 13, 
        end: 22, 
        timezone: 'EST', 
        color: '#9C27B0', 
        localStart: 13, 
        localEnd: 22,
        description: 'US markets'
      }
    ];
    
    const activeSessions = [];
    
    sessions.forEach(session => {
      let isActive = false;
      
      if (session.start <= session.end) {
        // Same day session (e.g., London 8-17)
        isActive = utcHour >= session.start && utcHour < session.end;
      } else {
        // Overnight session (e.g., Sydney 22-7)
        isActive = utcHour >= session.start || utcHour < session.end;
      }
      
      if (isActive) {
        activeSessions.push(session);
      }
    });
    
    setTradingSessions(activeSessions);
  };

  const formatTime = (date) => {
    return date.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const formatDate = (date) => {
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const getNextSession = () => {
    const now = new Date();
    const utcHour = now.getUTCHours();
    
    const sessions = [
      { name: 'Sydney', start: 22, end: 7 },
      { name: 'Tokyo', start: 0, end: 9 },
      { name: 'London', start: 8, end: 17 },
      { name: 'New York', start: 13, end: 22 }
    ];
    
    // Find the next session
    for (let session of sessions) {
      if (session.start <= session.end) {
        if (utcHour < session.start) {
          return { session, hoursUntil: session.start - utcHour };
        }
      } else {
        // Overnight session
        if (utcHour >= session.end && utcHour < session.start) {
          return { session, hoursUntil: session.start - utcHour };
        }
      }
    }
    
    // If no next session today, return first session tomorrow
    return { session: sessions[0], hoursUntil: 24 - utcHour + sessions[0].start };
  };

  const getMarketStatusText = () => {
    if (tradingSessions.length === 0) {
      return 'Markets Closed';
    } else if (tradingSessions.length === 1) {
      return `${tradingSessions[0].name} Session`;
    } else {
      return 'Multiple Sessions Active';
    }
  };

  const getMarketStatusColor = () => {
    if (tradingSessions.length === 0) {
      return '#ff4444';
    } else if (tradingSessions.length === 1) {
      return '#00cc44';
    } else {
      return '#ffaa00';
    }
  };

  if (!isOpen) return null;

  const nextSession = getNextSession();

  return (
    <div className="market-status-popup-overlay" onClick={onClose}>
      <div className="market-status-popup" onClick={(e) => e.stopPropagation()}>
        <div className="market-status-popup-header">
          <h2>Market Status</h2>
          <button className="close-button" onClick={onClose}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        <div className="market-status-popup-content">
          {/* Current Status */}
          <div className="status-overview">
            <div className="market-status-indicator" style={{ backgroundColor: getMarketStatusColor() }}>
              <div className="status-dot"></div>
            </div>
            <div className="status-info">
              <h3>{getMarketStatusText()}</h3>
              <p className="status-description">
                {tradingSessions.length === 0 
                  ? 'Forex markets are currently closed for the weekend or holiday'
                  : `${tradingSessions.length} trading session${tradingSessions.length > 1 ? 's' : ''} currently active`
                }
              </p>
            </div>
          </div>

          {/* Current Time */}
          <div className="time-display">
            <div className="time-item">
              <span className="time-label">Current Time (UTC)</span>
              <span className="time-value">{formatTime(currentTime)}</span>
            </div>
            <div className="time-item">
              <span className="time-label">Date</span>
              <span className="time-value">{formatDate(currentTime)}</span>
            </div>
          </div>

          {/* Active Sessions */}
          {tradingSessions.length > 0 && (
            <div className="active-sessions">
              <h4>Active Trading Sessions</h4>
              <div className="sessions-grid">
                {tradingSessions.map((session, index) => (
                  <div key={index} className="session-card" style={{ borderColor: session.color }}>
                    <div className="session-header">
                      <div className="session-indicator" style={{ backgroundColor: session.color }}></div>
                      <h5>{session.name}</h5>
                    </div>
                    <div className="session-details">
                      <p className="session-time">
                        {session.localStart}:00 - {session.localEnd}:00 {session.timezone}
                      </p>
                      <p className="session-description">{session.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Next Session */}
          <div className="next-session">
            <h4>Next Trading Session</h4>
            <div className="next-session-info">
              <div className="next-session-name">{nextSession.session.name}</div>
              <div className="next-session-time">
                Opens in {nextSession.hoursUntil} hour{nextSession.hoursUntil !== 1 ? 's' : ''}
              </div>
            </div>
          </div>

          {/* Market Hours Info */}
          <div className="market-hours-info">
            <h4>Trading Hours (UTC)</h4>
            <div className="hours-table">
              <div className="hours-header">
                <span>Session</span>
                <span>Hours</span>
                <span>Timezone</span>
              </div>
              <div className="hours-row">
                <span>Sydney</span>
                <span>22:00 - 07:00</span>
                <span>AEST</span>
              </div>
              <div className="hours-row">
                <span>Tokyo</span>
                <span>00:00 - 09:00</span>
                <span>JST</span>
              </div>
              <div className="hours-row">
                <span>London</span>
                <span>08:00 - 17:00</span>
                <span>GMT</span>
              </div>
              <div className="hours-row">
                <span>New York</span>
                <span>13:00 - 22:00</span>
                <span>EST</span>
              </div>
            </div>
          </div>

          {/* Market Status Note */}
          <div className="market-note">
            <div className="note-icon"></div>
            <div className="note-content">
              <p><strong>Note:</strong> Forex markets are closed on weekends and major holidays. 
              During active sessions, you can trade 24/5 with high liquidity and tight spreads.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MarketStatusPopup;
