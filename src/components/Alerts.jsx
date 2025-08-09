import React from 'react';
import './Alerts.css';

function Alerts({ alerts, alertStats, alertSettings, updateAlertSettings }) {
  return (
    <div className="alerts-section">
      <div className="alerts-overview">
        <h2>🔔 Smart Alert System</h2>
        <p>Get instant notifications for important market events via Telegram and Email</p>
        
        <div className="alert-stats">
          <div className="stat-card">
            <span className="stat-number">{alertStats.telegramSubscribers}</span>
            <span className="stat-label">Telegram Subscribers</span>
          </div>
          <div className="stat-card">
            <span className="stat-number">{alertStats.emailSubscribers}</span>
            <span className="stat-label">Email Subscribers</span>
          </div>
          <div className="stat-card">
            <span className="stat-number">{alertStats.alertsThisWeek}</span>
            <span className="stat-label">Alerts This Week</span>
          </div>
        </div>
      </div>

      <div className="alerts-content">
        <div className="alert-settings">
          <h3>⚙️ Alert Preferences</h3>
          <div className="settings-grid">
            <div className="setting-group">
              <h4>Notification Channels</h4>
              <label className="setting-item">
                <input 
                  type="checkbox" 
                  checked={alertSettings.telegram}
                  onChange={(e) => updateAlertSettings('telegram', e.target.checked)}
                />
                <span>📱 Telegram Bot</span>
              </label>
              <label className="setting-item">
                <input 
                  type="checkbox" 
                  checked={alertSettings.email}
                  onChange={(e) => updateAlertSettings('email', e.target.checked)}
                />
                <span>📧 Email Alerts</span>
              </label>
            </div>
            
            <div className="setting-group">
              <h4>Impact Levels</h4>
              <label className="setting-item">
                <input 
                  type="checkbox" 
                  checked={alertSettings.highImpact}
                  onChange={(e) => updateAlertSettings('highImpact', e.target.checked)}
                />
                <span>🔴 High Impact Events</span>
              </label>
              <label className="setting-item">
                <input 
                  type="checkbox" 
                  checked={alertSettings.mediumImpact}
                  onChange={(e) => updateAlertSettings('mediumImpact', e.target.checked)}
                />
                <span>🟡 Medium Impact Events</span>
              </label>
              <label className="setting-item">
                <input 
                  type="checkbox" 
                  checked={alertSettings.lowImpact}
                  onChange={(e) => updateAlertSettings('lowImpact', e.target.checked)}
                />
                <span>🟢 Low Impact Events</span>
              </label>
            </div>
          </div>
        </div>

        <div className="recent-alerts">
          <h3>📋 Recent Alerts</h3>
          <div className="alerts-list">
            {alerts.map(alert => (
              <div key={alert.id} className="alert-item">
                <div className="alert-icon">
                  {alert.type === 'telegram' ? '📱' : '📧'}
                </div>
                <div className="alert-content">
                  <h4>{alert.event}</h4>
                  <p>{alert.status === 'sent' ? 'Delivered' : 'Scheduled'}</p>
                  <small>{new Date(alert.timestamp).toLocaleString()}</small>
                </div>
                <div className="alert-recipients">
                  {alert.recipients} recipients
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Alerts;
