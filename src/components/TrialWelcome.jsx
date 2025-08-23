import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { config } from '../config';
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
      const response = await fetch(`${config.API_BASE_URL}/api/create-checkout-session`, {
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
            We dont want to bullsh#t you, take our free trial and help us make a better product. Thank you.
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
              <div className="trial-welcome-plan-card trial">
                <div className="trial-welcome-plan-badge">Free Trial</div>
                <h3>3-Day Free Trial</h3>
                <div className="trial-welcome-price">$0<span>/3 days</span></div>
                <div className="trial-welcome-plan-description">
                  <p>Experience the power of AI-driven forex analysis with our comprehensive trial package</p>
                </div>
                <div className="trial-welcome-features-list">
                  <div className="trial-welcome-feature-item">
                    <div className="trial-welcome-feature-icon">🤖</div>
                    <div className="trial-welcome-feature-text">
                      <h4>15 AI Analyses Daily</h4>
                      <p>Advanced AI analysis of economic events and news with trading insights and market impact assessment</p>
                    </div>
                  </div>
                  <div className="trial-welcome-feature-item">
                    <div className="trial-welcome-feature-icon">📊</div>
                    <div className="trial-welcome-feature-text">
                      <h4>Live Market Data</h4>
                      <p>Real-time forex prices from TradingView API with 15 major currency pairs and price change indicators</p>
                    </div>
                  </div>
                  <div className="trial-welcome-feature-item">
                    <div className="trial-welcome-feature-icon">📅</div>
                    <div className="trial-welcome-feature-text">
                      <h4>Economic Calendar</h4>
                      <p>Track high-impact economic events with AI analysis of expected vs actual data and market implications</p>
                    </div>
                  </div>
                  <div className="trial-welcome-feature-item">
                    <div className="trial-welcome-feature-icon">🔔</div>
                    <div className="trial-welcome-feature-text">
                      <h4>Smart Alerts</h4>
                      <p>Telegram alerts for breaking news and economic events with AI analysis and currency pair identification</p>
                    </div>
                  </div>
                  <div className="trial-welcome-feature-item">
                    <div className="trial-welcome-feature-icon">📰</div>
                    <div className="trial-welcome-feature-text">
                      <h4>Live News Feed</h4>
                      <p>Real-time news from Reuters, Bloomberg, CNBC with AI-powered sentiment analysis and forex impact</p>
                    </div>
                  </div>
                  <div className="trial-welcome-feature-item">
                    <div className="trial-welcome-feature-icon">📱</div>
                    <div className="trial-welcome-feature-text">
                      <h4>Mobile Responsive</h4>
                      <p>Access your trading insights anywhere with our fully responsive web application</p>
                    </div>
                  </div>
                </div>
                <div className="trial-welcome-trial-limitations">
                  <h4>Trial Limitations</h4>
                  <ul>
                    <li>Limited to 15 AI analyses per day</li>
                    <li>Basic alert functionality</li>
                    <li>Standard support response time</li>
                  </ul>
                </div>
              </div>
            )}
            
            {activePlan === 'premium' && (
              <div className="trial-welcome-plan-card premium">
                <div className="trial-welcome-plan-badge premium">Premium</div>
                <h3>Premium Plan</h3>
                <div className="trial-welcome-price">$20<span>/month</span></div>
                <div className="trial-welcome-plan-description">
                  <p>Unlock unlimited access to our most advanced AI analysis tools and premium features</p>
                </div>
                <div className="trial-welcome-features-list">
                  <div className="trial-welcome-feature-item">
                    <div className="trial-welcome-feature-icon">🚀</div>
                    <div className="trial-welcome-feature-text">
                      <h4>100 AI Analyses Per Day</h4>
                      <p>Unlimited access to our most advanced AI models with enhanced accuracy and deeper market insights</p>
                    </div>
                  </div>
                  <div className="trial-welcome-feature-item">
                    <div className="trial-welcome-feature-icon">🎯</div>
                    <div className="trial-welcome-feature-text">
                      <h4>Advanced Analytics</h4>
                      <p>Deep market insights, predictive analytics, risk assessment, and portfolio optimization recommendations</p>
                    </div>
                  </div>
                  <div className="trial-welcome-feature-item">
                    <div className="trial-welcome-feature-icon">⚡</div>
                    <div className="trial-welcome-feature-text">
                      <h4>Priority Support</h4>
                      <p>24/7 dedicated customer support with priority response times and personalized assistance</p>
                    </div>
                  </div>
                  <div className="trial-welcome-feature-item">
                    <div className="trial-welcome-feature-icon">🔧</div>
                    <div className="trial-welcome-feature-text">
                      <h4>Custom Alerts</h4>
                      <p>Personalized notification settings, custom price targets, and advanced alert filtering options</p>
                    </div>
                  </div>
                  <div className="trial-welcome-feature-item">
                    <div className="trial-welcome-feature-icon">📊</div>
                    <div className="trial-welcome-feature-text">
                      <h4>Enhanced Charting</h4>
                      <p>Professional-grade charting with multiple timeframes, technical indicators, and advanced drawing tools</p>
                    </div>
                  </div>
                  <div className="trial-welcome-feature-item">
                    <div className="trial-welcome-feature-icon">📈</div>
                    <div className="trial-welcome-feature-text">
                      <h4>Performance Tracking</h4>
                      <p>Track your trading performance, analyze risk metrics, and get detailed performance reports</p>
                    </div>
                  </div>
                  <div className="trial-welcome-feature-item">
                    <div className="trial-welcome-feature-icon">🔍</div>
                    <div className="trial-welcome-feature-text">
                      <h4>Market Scanner</h4>
                      <p>Advanced market scanner to identify trading opportunities across multiple currency pairs simultaneously</p>
                    </div>
                  </div>
                  <div className="trial-welcome-feature-item">
                    <div className="trial-welcome-feature-icon">📱</div>
                    <div className="trial-welcome-feature-text">
                      <h4>API Access</h4>
                      <p>Access our data and analysis through API for integration with your existing trading systems</p>
                    </div>
                  </div>
                </div>
                <div className="trial-welcome-premium-benefits">
                  <h4>Premium Benefits</h4>
                  <ul>
                    <li>Unlimited AI analyses (100/day)</li>
                    <li>Advanced risk management tools</li>
                    <li>Priority customer support</li>
                    <li>Exclusive market insights</li>
                  </ul>
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
            <div className="trial-welcome-terms-section">
              <div className="trial-welcome-terms-content">
                <h3>Terms & Conditions</h3>
                <div className="trial-welcome-terms-text">
                  <div className="trial-welcome-terms-group">
                    <h4>Trial Period</h4>
                    <p>3-day free trial with 15 AI analyses/day. No charges during trial period.</p>
                  </div>
                  
                  <div className="trial-welcome-terms-group">
                    <h4>Automatic Billing</h4>
                    <p>$20/month charged after trial unless cancelled. Cancel anytime before trial ends.</p>
                  </div>
                  
                  <div className="trial-welcome-terms-group">
                    <h4>Usage Limits</h4>
                    <p>Trial users have basic features with daily limits. Upgrade for unlimited access.</p>
                  </div>
                  
                  <div className="trial-welcome-terms-group">
                    <h4>Cancellation Policy</h4>
                    <p>Cancel anytime through account settings. No cancellation fees or penalties.</p>
                  </div>
                  
                  <div className="trial-welcome-terms-group">
                    <h4>Payment Method</h4>
                    <p>Valid payment method required to start trial. Secure Stripe payment processing.</p>
                  </div>
                  
                  <div className="trial-welcome-terms-group">
                    <h4>Data & Privacy</h4>
                    <p>Bank-level security protection. We never share your data with third parties.</p>
                  </div>
                </div>
                
                <div className="trial-welcome-terms-checkbox">
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
                <div className="guarantee-text">
                  <h4>Secure Payment</h4>
                  <p>Bank-level encryption and secure Stripe processing</p>
                </div>
              </div>
              <div className="guarantee-item">
                <span className="guarantee-icon">⏰</span>
                <div className="guarantee-text">
                  <h4>3-Day Free Trial</h4>
                  <p>No charges during trial period</p>
                </div>
              </div>
              <div className="guarantee-item">
                <span className="guarantee-icon">❌</span>
                <div className="guarantee-text">
                  <h4>Cancel Anytime</h4>
                  <p>No cancellation fees or penalties</p>
                </div>
              </div>
              <div className="guarantee-item">
                <span className="guarantee-icon">💬</span>
                <div className="guarantee-text">
                  <h4>24/7 Support</h4>
                  <p>Get help whenever you need it</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TrialWelcome;
