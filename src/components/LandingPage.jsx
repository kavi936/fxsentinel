import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import './LandingPage.css';
import logoPng from '../assets/fxsentinel_logo_nobg.png';
import logoWebp from '../assets/fxsentinel_logo_nobg.webp';
import LiveTicker from './LiveTicker';

const LandingPage = () => {
  const [isScrolled, setIsScrolled] = useState(false);



  useEffect(() => {
    const handleScroll = () => {
      const scrollPosition = window.scrollY;
      // Change navbar style when scrolled more than 50px
      setIsScrolled(scrollPosition > 50);
    };

    // Add scroll event listener
    window.addEventListener('scroll', handleScroll);
    
    // Cleanup function to remove event listener
    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, []);

  useEffect(() => {
    const counters = document.querySelectorAll('.counter');
    
    const animateCounter = (counter) => {
      const target = parseFloat(counter.getAttribute('data-target'));
      const duration = 2000; // 2 seconds
      const step = target / (duration / 16); // 60fps
      let current = 0;
      
      const timer = setInterval(() => {
        current += step;
        if (current >= target) {
          current = target;
          clearInterval(timer);
        }
        
        // Format the number based on the target
        if (target === 99.9) {
          counter.textContent = current.toFixed(1) + '%';
        } else if (target === 24) {
          counter.textContent = Math.floor(current) + '/7';
        } else {
          counter.textContent = Math.floor(current) + '+';
        }
      }, 16);
    };

    // Intersection Observer to trigger animation when section is visible
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const counters = entry.target.querySelectorAll('.counter');
          counters.forEach((counter, index) => {
            setTimeout(() => animateCounter(counter), index * 200);
          });
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.5 });

    const aboutSection = document.getElementById('about');
    if (aboutSection) {
      observer.observe(aboutSection);
    }

    return () => {
      if (aboutSection) {
        observer.unobserve(aboutSection);
      }
    };
  }, []);

  const scrollToTop = () => {
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  };

  return (
    <div className="landing-page">
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
          <div className="nav-links">
            <a href="#features">Features</a>
            <a href="#about">About</a>
            <a href="#pricing">Pricing</a>
          </div>
          <div className="nav-auth">
            <Link to="/login" className="login-button">Login</Link>
            <Link to="/signup" className="signup-button">Sign Up</Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="hero">
        {/* Ticker lines for background animation */}
        <div className="ticker-line-1"></div>
        <div className="ticker-line-2"></div>
        <div className="ticker-line-3"></div>
        <div className="ticker-line-4"></div>
        <div className="ticker-line-5"></div>
        <div className="ticker-line-6"></div>
        <div className="ticker-line-7"></div>
        <div className="ticker-line-8"></div>
        <div className="ticker-line-9"></div>
        <div className="ticker-line-10"></div>
        
        {/* Floating FX News Headlines */}
        <div className="news-headline-1">EUR/USD: Fed Rate Decision Impact Analysis</div>
        <div className="news-headline-2">CPI Data Shows Inflation Cooling - USD Weakens</div>
        <div className="news-headline-3">ECB Policy Meeting: Euro Zone Economic Outlook</div>
        <div className="news-headline-4">Gold Surges on Safe Haven Demand</div>
        <div className="news-headline-5">BoE Interest Rate Decision: GBP Volatility Expected</div>
        <div className="news-headline-6">USD/JPY: Bank of Japan Policy Shift Analysis</div>
        <div className="news-headline-7">AUD/USD: RBA Monetary Policy Statement Released</div>
        <div className="news-headline-8">CAD/JPY: Oil Price Volatility Impacts Loonie</div>
        <div className="news-headline-9">NZD/USD: New Zealand Employment Data Surprises</div>
        <div className="news-headline-10">EUR/GBP: Brexit Trade Deal Negotiations Update</div>
        <div className="news-headline-11">USD/CHF: Swiss National Bank Policy Review</div>
        <div className="news-headline-12">GBP/JPY: UK GDP Growth Exceeds Expectations</div>
        
        <div className="hero-inner">
          <div className="hero-content">
            {/* Badge */}
            <div className="hero-badge-container">
              <div className="hero-badge">
                <span className="badge-dot"></span>
                AI-Powered • Real-Time • Trusted by 10K+ Traders
              </div>
            </div>
            
            <h1 className="hero-title">
              Turning <span className="highlight">Macro News</span> into <span className="highlight">Market Moves</span>
            </h1>
            
            <p className="hero-subtitle">
              We simplify complex trading news, making it accessible
              and usable for every trader
            </p>
            
            {/* Live Market Ticker */}
            <LiveTicker />
            
            <div className="hero-buttons">
              <Link to="/login" className="primary-button">
                Explore FXSentinel
              </Link>
              <button className="secondary-button">
                How it works
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="features">
        <div className="features-inner">
          <h2 className="section-title">What FXSentinel Does</h2>
          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon">📰</div>
              <h3>Daily News Aggregation</h3>
              <p>Curated macroeconomic events from TradingEconomics and ForexFactory - CPI, FOMC, GDP, and more key releases that move markets.</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">🤖</div>
              <h3>AI-Powered Analysis</h3>
              <p>GPT-4 generated insights explaining how each economic event impacts EUR/USD, USD/JPY, and Gold with actionable trading context.</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">⚡</div>
              <h3>Real-Time Alerts</h3>
              <p>Get instant Telegram notifications for high-impact events with AI summaries and pair-specific market reactions before the news breaks.</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">🎯</div>
              <h3>Instrument-Specific Insights</h3>
              <p>Tailored analysis for major forex pairs and commodities, helping you understand which instruments will be most affected by each event.</p>
            </div>
          </div>
        </div>
      </section>

      {/* About Section */}
      <section id="about" className="about">
        <div className="about-inner">
          <div className="about-content">
            <div className="about-text">
              <h2 className="about-title">About FXSentinel</h2>
              <div className="about-text-background">
                <p>
                  FXSentinel is a cutting-edge platform designed specifically for forex traders 
                  who need to stay informed about macroeconomic events and their potential impact 
                  on currency markets.
                </p>
                <p>
                  Our AI system processes thousands of news sources, economic indicators, and 
                  market data to provide you with actionable insights that help you make better 
                  trading decisions.
                </p>
              </div>
            </div>
            <div className="about-stats">
              <div className="stat">
                <h3 className="counter" data-target="99.9">0</h3>
                <p>Uptime</p>
              </div>
              <div className="stat">
                <h3 className="counter" data-target="24">0</h3>
                <p>Monitoring</p>
              </div>
              <div className="stat">
                <h3 className="counter" data-target="1000">0</h3>
                <p>News Sources</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="pricing">
        <div className="pricing-inner">
          <h2 className="section-title">Simple, Transparent Pricing</h2>
          <div className="pricing-grid">
            <div className="pricing-card">
              <h3>Starter</h3>
              <div className="price">FREE<span></span></div>
              <ul>
                <li>Basic news analysis</li>
                <li>5 currency pairs</li>
                <li>Email alerts</li>
                <li>Basic dashboard</li>
              </ul>
              <Link to="/signup" className="pricing-button">Start Free Trial</Link>
            </div>
            <div className="pricing-card featured">
              <h3>Professional</h3>
              <div className="price">$20<span>/month</span></div>
              <ul>
                <li>Advanced AI analysis</li>
                <li>All currency pairs</li>
                <li>Real-time alerts</li>
                <li>Advanced dashboard</li>
                <li>Trading recommendations</li>
              </ul>
              <Link to="/signup" className="pricing-button">Start Free Trial</Link>
            </div>
            <div className="pricing-card coming-soon">
              <h3>Enterprise</h3>
              <div className="price">Custom</div>
              <ul>
                <li>Custom integrations</li>
                <li>API access</li>
                <li>Dedicated support</li>
                <li>White-label options</li>
              </ul>
              <button className="pricing-button">Contact Sales</button>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="footer">
        <div className="footer-inner">
          <div className="footer-content">
            <div className="footer-section">
              <div className="footer-logo">
                <picture>
                  <source srcSet={logoWebp} type="image/webp" />
                  <img src={logoPng} alt="FXSentinel Logo" className="logo" />
                </picture>
                <span>FXSentinel</span>
              </div>
              <p>AI-powered forex news analysis for professional traders.</p>
            </div>
            <div className="footer-section">
              <h4>Product</h4>
              <a href="#features">Features</a>
              <a href="#pricing">Pricing</a>
              <Link to="/dashboard">Dashboard</Link>
            </div>
            <div className="footer-section">
              <h4>Company</h4>
              <a href="#about">About</a>
              <a href="#">Blog</a>
              <a href="#">Contact</a>
            </div>
            <div className="footer-section">
              <h4>Support</h4>
              <a href="#">Help Center</a>
              <a href="#">Documentation</a>
              <a href="#">API</a>
            </div>
          </div>
          
          {/* Disclaimer Section */}
          <div className="disclaimer-section">
            <div className="disclaimer-content">
              <h4>Disclaimer</h4>
              <p>
                FXSentinel is a market intelligence and data analytics platform. We are not a brokerage, 
                investment advisor, or financial institution. The platform provides AI-powered analysis 
                of forex market events and economic data for informational purposes only. We do not 
                provide financial advice, investment recommendations, or trading signals. The insights 
                and analysis provided through our platform should not be considered as certified 
                financial education or professional trading advice. Users should conduct their own 
                research and consult with qualified financial professionals before making any investment 
                decisions. All platform features and analysis are provided "as is" without any guarantees 
                of accuracy or specific trading outcomes. All sales are final, and we do not offer refunds.
              </p>
            </div>
          </div>
          
          <div className="footer-bottom">
            <p>&copy; 2024 FXSentinel. All rights reserved.</p>
            <p className="attribution">
              <a href="https://unirateapi.com" target="_blank" rel="noopener noreferrer">
                Exchange Rates By UniRateAPI
              </a>
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage; 