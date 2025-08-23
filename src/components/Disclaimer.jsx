import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import './Disclaimer.css';
import logoPng from '../assets/fxsentinel_logo_nobg.png';
import logoWebp from '../assets/fxsentinel_logo_nobg.webp';

const Disclaimer = () => {
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      const scrollPosition = window.scrollY;
      setIsScrolled(scrollPosition > 50);
    };

    window.addEventListener('scroll', handleScroll);
    
    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, []);

  const scrollToTop = () => {
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  };

  return (
    <div className="disclaimer-page">
      {/* Navigation */}
      <nav className={`navbar ${isScrolled ? 'navbar-scrolled' : ''}`}>
        <div className="nav-container">
          <div className="nav-logo" onClick={scrollToTop} style={{ cursor: 'pointer' }}>
            <picture>
              <source srcSet={logoWebp} type="image/webp" />
              <img 
                src={logoPng} 
                alt="FXSentinel Logo" 
                className="logo"
                style={{ height: '50px', width: 'auto' }}
              />
            </picture>
          </div>
          
          {/* Desktop Navigation Links */}
          <div className="nav-links desktop-only">
            <Link to="/" className="nav-link-button">Home</Link>
            <Link to="/dashboard" className="nav-link-button">Dashboard</Link>
          </div>
          
          {/* Desktop Auth Buttons */}
          <div className="nav-auth desktop-only">
            <Link to="/login" className="login-button">Login</Link>
            <Link to="/signup" className="signup-button">Sign Up</Link>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="disclaimer-page-content">
        <div className="disclaimer-page-inner">
          <h1 className="disclaimer-page-title">Disclaimer</h1>
          
          <div className="disclaimer-page-section">
            <h2>General Disclaimer</h2>
            <p>
              FXSentinel is a market intelligence and data analytics platform designed to provide 
              information and analysis related to forex markets and economic events. This platform 
              is intended for informational and educational purposes only.
            </p>
          </div>

          <div className="disclaimer-page-section">
            <h2>Not Financial Advice</h2>
            <p>
              The information, analysis, and content provided through FXSentinel should not be 
              construed as financial advice, investment recommendations, or trading signals. We are 
              not a brokerage, investment advisor, or financial institution. The platform does not 
              provide certified financial education or professional trading advice.
            </p>
            <p>
              Users should conduct their own research, perform due diligence, and consult with 
              qualified financial professionals before making any investment decisions. Trading 
              forex involves substantial risk of loss and is not suitable for all investors.
            </p>
          </div>

          <div className="disclaimer-page-section">
            <h2>No Guarantees</h2>
            <p>
              All platform features, analysis, and insights are provided "as is" without any 
              guarantees of accuracy, completeness, or specific trading outcomes. Past performance 
              does not guarantee future results. Market conditions can change rapidly, and the 
              information provided may become outdated or inaccurate.
            </p>
            <p>
              We do not guarantee that the information provided will result in profitable trades 
              or prevent losses. Users are solely responsible for their trading decisions and 
              the outcomes of their trades.
            </p>
          </div>

          <div className="disclaimer-page-section">
            <h2>Data Sources and Accuracy</h2>
            <p>
              FXSentinel aggregates data from various sources including TradingEconomics, 
              ForexFactory, Finnhub, Alpha Vantage, and other financial data providers. While 
              we strive to provide accurate and timely information, we cannot guarantee the 
              accuracy, completeness, or timeliness of the data from these sources.
            </p>
            <p>
              AI-powered analysis is based on historical patterns and market correlations, but 
              should not be considered as definitive predictions of future market movements.
            </p>
          </div>

          <div className="disclaimer-page-section">
            <h2>Risk Disclosure</h2>
            <p>
              Forex trading involves substantial risk of loss and is not suitable for all 
              investors. The high degree of leverage can work against you as well as for you. 
              Before deciding to trade foreign exchange, you should carefully consider your 
              investment objectives, level of experience, and risk appetite.
            </p>
            <p>
              You could lose some or all of your initial investment and therefore you should 
              not invest money that you cannot afford to lose. You should be aware of all the 
              risks associated with foreign exchange trading.
            </p>
          </div>

          <div className="disclaimer-page-section">
            <h2>Subscription and Refunds</h2>
            <p>
              All sales are final. We do not offer refunds for subscription services. Users 
              may cancel their subscription at any time, and access will continue until the 
              end of the current billing period.
            </p>
          </div>

          <div className="disclaimer-page-section">
            <h2>Limitation of Liability</h2>
            <p>
              To the maximum extent permitted by law, FXSentinel and its affiliates shall not 
              be liable for any direct, indirect, incidental, special, consequential, or 
              punitive damages, including but not limited to loss of profits, data, or use, 
              arising out of or relating to the use of our platform or services.
            </p>
          </div>

          <div className="disclaimer-page-section">
            <h2>Contact Information</h2>
            <p>
              If you have any questions about this disclaimer, please contact us at 
              <a href="mailto:fxsentinelapp@gmail.com" className="disclaimer-page-contact-link"> fxsentinelapp@gmail.com</a>
            </p>
          </div>

          <div className="disclaimer-page-footer">
            <p><strong>Last updated:</strong> August 2025</p>
            <p>
              By using FXSentinel, you acknowledge that you have read, understood, and agree 
              to be bound by this disclaimer.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Disclaimer;
