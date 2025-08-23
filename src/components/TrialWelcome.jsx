import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import './TrialWelcome.css';
import logoPng from '../assets/fxsentinel_logo_nobg.png';
import logoWebp from '../assets/fxsentinel_logo_nobg.webp';

const TrialWelcome = () => {
  const navigate = useNavigate();
  const { currentUser } = useAuth();
  
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [acceptedTerms, setAcceptedTerms] = useState(false);
  const [activePlan, setActivePlan] = useState('trial');

  // Debug logging
  console.log('🔍 TrialWelcome - Component rendered');
  console.log('🔍 TrialWelcome - Current user:', currentUser ? { uid: currentUser.uid, email: currentUser.email } : null);

  const handleStartTrial = async () => {
    if (!acceptedTerms) {
      setError('You must accept the terms and conditions to continue.');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      // Create Stripe Checkout Session
      const response = await fetch('/api/create-checkout-session', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: currentUser.uid,
          email: currentUser.email,
          name: currentUser.displayName || currentUser.email,
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Failed to create checkout session');
      }

      const { session_url } = await response.json();
      
      // Redirect to Stripe's hosted checkout page
      window.location.href = session_url;
    } catch (error) {
      console.error('Error starting trial:', error);
      setError(error.message || 'Failed to start trial. Please try again.');
      setIsLoading(false);
    }
  };

  const handleSkipTrial = () => {
    navigate('/');
  };

  return (
    <div className="trial-welcome">
      {/* Hero Section */}
      <div className="hero-section">
        <div className="hero-background">
          <div className="hero-particles"></div>
          <div className="hero-gradient"></div>
        </div>
        
        <div className="hero-content">
          <div className="hero-logo">
            <picture>
              <source srcSet={logoWebp} type="image/webp" />
              <img src={logoPng} alt="FXSentinel Logo" />
            </picture>
          </div>
          
          <h1 className="hero-title">
            Welcome to <span className="highlight">FXSentinel</span>
          </h1>
          <p className="hero-subtitle">
            Your AI-powered forex trading companion is ready to revolutionize your trading strategy
          </p>
          
          {error && (
            <div className="error-banner">
              <span className="error-icon">⚠️</span>
              {error}
            </div>
          )}
        </div>
      </div>

      {/* Plans Toggle Section */}
      <div className="plans-section">
        <div className="container">
          <div className="section-header">
            <h2>Choose Your Plan</h2>
            <p>Experience the power of AI-driven forex analysis</p>
          </div>
          
          {/* Toggle Tabs */}
          <div className="plans-toggle">
            <button 
              className={`toggle-tab ${activePlan === 'trial' ? 'active' : ''}`}
              onClick={() => setActivePlan('trial')}
            >
              Free Trial
            </button>
            <button 
              className={`toggle-tab ${activePlan === 'premium' ? 'active' : ''}`}
              onClick={() => setActivePlan('premium')}
            >
              Premium
            </button>
          </div>
          
          {/* Plans Content */}
          <div className="plans-content">
            {activePlan === 'trial' && (
              <div className="plan-card trial">
                <div className="plan-badge">Free Trial</div>
                <h3>3-Day Free Trial</h3>
                <div className="price">$0<span>/3 days</span></div>
                <div className="features-list">
                  <div className="feature-item">
                    <div className="feature-icon">✓</div>
                    <div className="feature-text">
                      <h4>15 AI Analyses Daily</h4>
                      <p>Get intelligent insights on market movements</p>
                    </div>
                  </div>
                  <div className="feature-item">
                    <div className="feature-icon">✓</div>
                    <div className="feature-text">
                      <h4>Real-time Market Data</h4>
                      <p>Live forex prices and economic indicators</p>
                    </div>
                  </div>
                  <div className="feature-item">
                    <div className="feature-icon">✓</div>
                    <div className="feature-text">
                      <h4>Economic Calendar</h4>
                      <p>Track important market events</p>
                    </div>
                  </div>
                  <div className="feature-item">
                    <div className="feature-icon">✓</div>
                    <div className="feature-text">
                      <h4>Smart Alerts</h4>
                      <p>Get notified of market changes</p>
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            {activePlan === 'premium' && (
              <div className="plan-card premium">
                <div className="plan-badge premium">Premium</div>
                <h3>Premium Plan</h3>
                <div className="price">$20<span>/month</span></div>
                <div className="features-list">
                  <div className="feature-item">
                    <div className="feature-icon">🚀</div>
                    <div className="feature-text">
                      <h4>100 AI Analyses Per Day</h4>
                      <p>Unlimited access to our advanced AI analysis</p>
                    </div>
                  </div>
                  <div className="feature-item">
                    <div className="feature-icon">🎯</div>
                    <div className="feature-text">
                      <h4>Advanced Analytics</h4>
                      <p>Deep market insights and predictive analytics</p>
                    </div>
                  </div>
                  <div className="feature-item">
                    <div className="feature-icon">⚡</div>
                    <div className="feature-text">
                      <h4>Priority Support</h4>
                      <p>24/7 dedicated customer support</p>
                    </div>
                  </div>
                  <div className="feature-item">
                    <div className="feature-icon">🔧</div>
                    <div className="feature-text">
                      <h4>Custom Alerts</h4>
                      <p>Personalized notification settings</p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="cta-section">
        <div className="container">
          <div className="cta-content">
            <h2>Ready to Start Your Trading Journey?</h2>
            <p>Join thousands of traders using FXSentinel to make informed decisions</p>
            
            {/* Terms and Conditions */}
            <div className="terms-section">
              <div className="terms-content">
                <h3>Terms & Conditions</h3>
                <div className="terms-text">
                  <p><strong>Trial Period:</strong> 3-day free trial with limited usage (15 AI analyses/day)</p>
                  <p><strong>Automatic Billing:</strong> $20/month will be charged after trial unless cancelled</p>
                  <p><strong>Usage Limits:</strong> Trial users are heavily limited; upgrade for full access</p>
                  <p><strong>Cancellation:</strong> Cancel anytime through your Stripe dashboard</p>
                  <p><strong>Payment Method:</strong> Required to start trial (no charge during trial period)</p>
                </div>
                
                <div className="terms-checkbox">
                  <label>
                    <input
                      type="checkbox"
                      checked={acceptedTerms}
                      onChange={(e) => setAcceptedTerms(e.target.checked)}
                    />
                    <span>I accept the terms and conditions and understand I will be charged $20/month after the trial unless I cancel</span>
                  </label>
                </div>
              </div>
            </div>

            <div className="cta-buttons">
              <button 
                onClick={handleStartTrial} 
                className="cta-primary"
                disabled={!acceptedTerms || isLoading}
              >
                {isLoading ? (
                  <>
                    <span className="loading-spinner"></span>
                    Redirecting to Payment...
                  </>
                ) : (
                  'Start Free Trial'
                )}
              </button>
              
              <button 
                onClick={handleSkipTrial} 
                className="cta-secondary"
                disabled={isLoading}
              >
                Skip for Now
              </button>
            </div>
            
            <div className="trial-guarantee">
              <div className="guarantee-item">
                <span className="guarantee-icon">🔒</span>
                <span>Secure payment processing</span>
              </div>
              <div className="guarantee-item">
                <span className="guarantee-icon">⏰</span>
                <span>3-day free trial</span>
              </div>
              <div className="guarantee-item">
                <span className="guarantee-icon">❌</span>
                <span>Cancel anytime</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TrialWelcome;
