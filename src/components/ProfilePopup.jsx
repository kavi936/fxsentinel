import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import './ProfilePopup.css';

const ProfilePopup = ({ isOpen, onClose }) => {
  const { currentUser, logout } = useAuth();
  const [activeTab, setActiveTab] = useState('profile');
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    displayName: currentUser?.displayName || '',
    email: currentUser?.email || '',
    timezone: 'UTC',
    notifications: {
      email: true,
      telegram: true,
      push: false
    }
  });

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleNotificationChange = (type, value) => {
    setFormData(prev => ({
      ...prev,
      notifications: {
        ...prev.notifications,
        [type]: value
      }
    }));
  };

  const handleSave = () => {
    // Here you would typically save to backend
    console.log('Saving profile data:', formData);
    setIsEditing(false);
  };

  const handleCancel = () => {
    setFormData({
      displayName: currentUser?.displayName || '',
      email: currentUser?.email || '',
      timezone: 'UTC',
      notifications: {
        email: true,
        telegram: true,
        push: false
      }
    });
    setIsEditing(false);
  };

  const handleLogout = async () => {
    try {
      await logout();
      onClose();
    } catch (error) {
      console.error('Failed to log out:', error);
    }
  };

  const getUserDisplayName = () => {
    if (!currentUser) return 'Guest';
    
    if (currentUser.displayName) {
      return currentUser.displayName;
    }
    
    if (currentUser.email) {
      const emailName = currentUser.email.split('@')[0];
      const nameParts = emailName.split('.');
      if (nameParts.length > 0) {
        return nameParts[0].charAt(0).toUpperCase() + nameParts[0].slice(1);
      }
      return emailName;
    }
    
    return 'User';
  };

  const getUserInitials = () => {
    const name = getUserDisplayName();
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  };

  if (!isOpen) return null;

  return (
    <div className="profile-popup-overlay" onClick={onClose}>
      <div className="profile-popup" onClick={(e) => e.stopPropagation()}>
        <div className="profile-popup-header">
          <h2>User Profile</h2>
          <button className="close-button" onClick={onClose}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        <div className="profile-popup-tabs">
          <button 
            className={`tab-btn ${activeTab === 'profile' ? 'active' : ''}`}
            onClick={() => setActiveTab('profile')}
          >
            Profile
          </button>
          <button 
            className={`tab-btn ${activeTab === 'settings' ? 'active' : ''}`}
            onClick={() => setActiveTab('settings')}
          >
            Settings
          </button>
          <button 
            className={`tab-btn ${activeTab === 'security' ? 'active' : ''}`}
            onClick={() => setActiveTab('security')}
          >
            Security
          </button>
        </div>

        <div className="profile-popup-content">
          {activeTab === 'profile' && (
            <div className="profile-section">
              <div className="profile-avatar-section">
                <div className="profile-avatar">
                  <span className="avatar-initials">{getUserInitials()}</span>
                </div>
                <div className="profile-info">
                  <h3>{getUserDisplayName()}</h3>
                  <p className="user-email">{currentUser?.email || 'No email'}</p>
                  <p className="user-status">Active</p>
                </div>
              </div>

              <div className="profile-form">
                <div className="form-group">
                  <label>Display Name</label>
                  <input
                    type="text"
                    value={formData.displayName}
                    onChange={(e) => handleInputChange('displayName', e.target.value)}
                    disabled={!isEditing}
                    placeholder="Enter display name"
                  />
                </div>

                <div className="form-group">
                  <label>Email</label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => handleInputChange('email', e.target.value)}
                    disabled={!isEditing}
                    placeholder="Enter email"
                  />
                </div>

                <div className="form-group">
                  <label>Timezone</label>
                  <select
                    value={formData.timezone}
                    onChange={(e) => handleInputChange('timezone', e.target.value)}
                    disabled={!isEditing}
                  >
                    <option value="UTC">UTC</option>
                    <option value="EST">Eastern Time</option>
                    <option value="PST">Pacific Time</option>
                    <option value="GMT">GMT</option>
                    <option value="CET">Central European Time</option>
                  </select>
                </div>

                <div className="profile-actions">
                  {!isEditing ? (
                    <button 
                      className="edit-btn"
                      onClick={() => setIsEditing(true)}
                    >
                      Edit Profile
                    </button>
                  ) : (
                    <div className="edit-actions">
                      <button 
                        className="save-btn"
                        onClick={handleSave}
                      >
                        Save Changes
                      </button>
                      <button 
                        className="cancel-btn"
                        onClick={handleCancel}
                      >
                        Cancel
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'settings' && (
            <div className="settings-section">
              <h3>Notification Preferences</h3>
              
              <div className="settings-group">
                <div className="setting-item">
                  <div className="setting-info">
                    <h4>Email Notifications</h4>
                    <p>Receive important updates via email</p>
                  </div>
                  <label className="toggle-switch">
                    <input
                      type="checkbox"
                      checked={formData.notifications.email}
                      onChange={(e) => handleNotificationChange('email', e.target.checked)}
                    />
                    <span className="toggle-slider"></span>
                  </label>
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <h4>Telegram Alerts</h4>
                    <p>Get instant alerts on Telegram</p>
                  </div>
                  <label className="toggle-switch">
                    <input
                      type="checkbox"
                      checked={formData.notifications.telegram}
                      onChange={(e) => handleNotificationChange('telegram', e.target.checked)}
                    />
                    <span className="toggle-slider"></span>
                  </label>
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <h4>Push Notifications</h4>
                    <p>Browser push notifications</p>
                  </div>
                  <label className="toggle-switch">
                    <input
                      type="checkbox"
                      checked={formData.notifications.push}
                      onChange={(e) => handleNotificationChange('push', e.target.checked)}
                    />
                    <span className="toggle-slider"></span>
                  </label>
                </div>
              </div>

              <div className="settings-group">
                <h4>Data & Privacy</h4>
                <div className="setting-item">
                  <div className="setting-info">
                    <h4>Data Export</h4>
                    <p>Download your data</p>
                  </div>
                  <button className="secondary-btn">Export</button>
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <h4>Delete Account</h4>
                    <p>Permanently delete your account</p>
                  </div>
                  <button className="danger-btn">Delete</button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'security' && (
            <div className="security-section">
              <h3>Security Settings</h3>
              
              <div className="settings-group">
                <div className="setting-item">
                  <div className="setting-info">
                    <h4>Change Password</h4>
                    <p>Update your account password</p>
                  </div>
                  <button className="secondary-btn">Change</button>
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <h4>Two-Factor Authentication</h4>
                    <p>Add an extra layer of security</p>
                  </div>
                  <button className="secondary-btn">Enable</button>
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <h4>Active Sessions</h4>
                    <p>Manage your active sessions</p>
                  </div>
                  <button className="secondary-btn">View</button>
                </div>
              </div>

              <div className="settings-group">
                <h4>Account Actions</h4>
                <div className="setting-item">
                  <div className="setting-info">
                    <h4>Logout</h4>
                    <p>Sign out of your account</p>
                  </div>
                  <button className="logout-btn" onClick={handleLogout}>
                    Logout
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProfilePopup;
