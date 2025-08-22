import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import './SubscriptionStatus.css';

const SubscriptionStatus = () => {
  const { currentUser } = useAuth();
  const [subscriptionStatus, setSubscriptionStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);

  useEffect(() => {
    if (currentUser) {
      fetchSubscriptionStatus();
    }
  }, [currentUser]);

  const fetchSubscriptionStatus = async () => {
    try {
      const response = await fetch(`/api/subscription-status/${currentUser.uid}`);
      if (response.ok) {
        const data = await response.json();
        setSubscriptionStatus(data);
      }
    } catch (error) {
      console.error('Error fetching subscription status:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="subscription-status">
        <div className="status-loading">Loading...</div>
      </div>
    );
  }

  if (!subscriptionStatus) {
    return null;
  }

  const { status, daily_analysis_count, analysis_limit, trial_end_date } = subscriptionStatus;
  const usagePercentage = Math.min((daily_analysis_count / analysis_limit) * 100, 100);

  const getStatusDisplay = () => {
    switch (status) {
      case 'trial':
        const daysLeft = trial_end_date ? 
          Math.ceil((new Date(trial_end_date) - new Date()) / (1000 * 60 * 60 * 24)) : 3;
        return {
          type: 'trial',
          title: 'Free Trial',
          subtitle: `${daysLeft} days remaining`,
          color: '#f59e0b',
          bgColor: 'rgba(245, 158, 11, 0.1)'
        };
      
      case 'active':
        return {
          type: 'active',
          title: 'Premium',
          subtitle: 'Active subscription',
          color: '#10b981',
          bgColor: 'rgba(16, 185, 129, 0.1)'
        };
      
      case 'expired':
        return {
          type: 'expired',
          title: 'Trial Expired',
          subtitle: 'Upgrade to continue',
          color: '#ef4444',
          bgColor: 'rgba(239, 68, 68, 0.1)'
        };
      
      case 'past_due':
        return {
          type: 'past_due',
          title: 'Payment Due',
          subtitle: 'Update payment method',
          color: '#f97316',
          bgColor: 'rgba(249, 115, 22, 0.1)'
        };
      
      default:
        return {
          type: 'unknown',
          title: 'Unknown',
          subtitle: 'Contact support',
          color: '#6b7280',
          bgColor: 'rgba(107, 114, 128, 0.1)'
        };
    }
  };

  const statusInfo = getStatusDisplay();

  return (
    <>
      <div className="subscription-status" style={{ backgroundColor: statusInfo.bgColor }}>
        <div className="status-info">
          <div className="status-header">
            <span className="status-title" style={{ color: statusInfo.color }}>
              {statusInfo.title}
            </span>
            <span className="status-subtitle">{statusInfo.subtitle}</span>
          </div>
          
          <div className="usage-info">
            <div className="usage-text">
              {daily_analysis_count} / {analysis_limit} analyses
            </div>
            <div className="usage-bar">
              <div 
                className="usage-fill" 
                style={{ 
                  width: `${usagePercentage}%`,
                  backgroundColor: usagePercentage > 80 ? '#ef4444' : statusInfo.color
                }}
              ></div>
            </div>
          </div>
        </div>
        
        {(status === 'trial' || status === 'expired') && (
          <button 
            className="upgrade-btn"
            onClick={() => setShowUpgradeModal(true)}
          >
            Upgrade
          </button>
        )}
      </div>

      {showUpgradeModal && (
        <div className="upgrade-modal-overlay" onClick={() => setShowUpgradeModal(false)}>
          <div className="upgrade-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Upgrade to Premium</h3>
              <button 
                className="close-btn"
                onClick={() => setShowUpgradeModal(false)}
              >
                ×
              </button>
            </div>
            
            <div className="modal-content">
              <div className="upgrade-benefits">
                <div className="benefit-item">
                  <div className="benefit-icon">🚀</div>
                  <div className="benefit-text">
                    <h4>100 AI Analyses Per Day</h4>
                    <p>Unlimited access to advanced AI analysis</p>
                  </div>
                </div>
                
                <div className="benefit-item">
                  <div className="benefit-icon">🎯</div>
                  <div className="benefit-text">
                    <h4>Advanced Analytics</h4>
                    <p>Deep market insights and predictive analytics</p>
                  </div>
                </div>
                
                <div className="benefit-item">
                  <div className="benefit-icon">⚡</div>
                  <div className="benefit-text">
                    <h4>Priority Support</h4>
                    <p>24/7 dedicated customer support</p>
                  </div>
                </div>
              </div>
              
              <div className="pricing">
                <div className="price-tag">
                  <span className="price">$20</span>
                  <span className="period">/month</span>
                </div>
                <p className="pricing-note">Cancel anytime through your Stripe dashboard</p>
              </div>
              
              <div className="modal-actions">
                <button 
                  className="upgrade-action-btn"
                  onClick={() => {
                    setShowUpgradeModal(false);
                    window.location.href = '/trial-welcome';
                  }}
                >
                  Upgrade Now
                </button>
                <button 
                  className="cancel-btn"
                  onClick={() => setShowUpgradeModal(false)}
                >
                  Maybe Later
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default SubscriptionStatus;
