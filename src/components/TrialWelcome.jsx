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

      {/* Trial Benefits Section */}
      <div className="trial-section">
        <div className="container">
          <div className="section-header">
            <h2>Your 3-Day Free Trial</h2>
            <p>Experience the full power of AI-driven forex analysis</p>
          </div>
          
          <div className="benefits-grid">
            <div className="benefit-card">
              <div className="benefit-icon">
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                </svg>
              </div>
              <h3>15 AI Analyses Daily</h3>
              <p>Get intelligent insights on market movements with our advanced AI algorithms</p>
            </div>
            
            <div className="benefit-card">
              <div className="benefit-icon">
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path d="M3.5 18.49l6-6.01 4 4L22 6.92l-1.41-1.41-7.09 7.97-4-4L2 16.99z"/>
                </svg>
              </div>
              <h3>Real-time Market Data</h3>
              <p>Live forex prices, economic indicators, and market sentiment analysis</p>
            </div>
            
            <div className="benefit-card">
              <div className="benefit-icon">
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path d="M19 3h-1V1h-2v2H8V1H6v2H5c-1.11 0-1.99.9-1.99 2L3 19c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V8h14v11zM7 10h5v5H7z"/>
                </svg>
              </div>
              <h3>Economic Calendar</h3>
              <p>Track important market events and news that impact currency movements</p>
            </div>
            
            <div className="benefit-card">
              <div className="benefit-icon">
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 22c1.1 0 2-.9 2-2h-4c0 1.1.89 2 2 2zm6-6v-5c0-3.07-1.64-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5v.68C7.63 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2z"/>
                </svg>
              </div>
              <h3>Smart Alerts</h3>
              <p>Get notified of significant market changes and trading opportunities</p>
            </div>
          </div>
        </div>
      </div>

      {/* Premium Upgrade Section */}
      <div className="premium-section">
        <div className="container">
          <div className="premium-content">
            <div className="premium-header">
              <h2>Upgrade to Premium</h2>
              <div className="price-tag">
                <span className="price">$20</span>
                <span className="period">/month</span>
              </div>
            </div>
            
            <div className="premium-features">
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
