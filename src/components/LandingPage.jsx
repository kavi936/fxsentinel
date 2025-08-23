import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import './LandingPage.css';
import logoPng from '../assets/fxsentinel_logo_nobg.png';
import logoWebp from '../assets/fxsentinel_logo_nobg.webp';
import tradingviewLogo from '../assets/tradingview-nobg.png';
import finnhubLogo from '../assets/finnhub-nobg.png';
import fxstreetLogo from '../assets/fxstreet-nobg.png';
import cnbcLogo from '../assets/CNBC.png';
import telegramLogo from '../assets/telegram.png';
import phoneImage from '../assets/IMG_8110-portrait.png';
import LiveTicker from './LiveTicker';

const LandingPage = () => {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);


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
    const handleClickOutside = (event) => {
      if (isMobileMenuOpen && !event.target.closest('.mobile-menu') && !event.target.closest('.mobile-menu-button')) {
        setIsMobileMenuOpen(false);
      }
    };

    if (isMobileMenuOpen) {
      document.addEventListener('click', handleClickOutside);
      // Add class to body when mobile menu is open
      document.body.classList.add('mobile-menu-open');
    } else {
      // Remove class and ensure scrolling is always enabled
      document.body.classList.remove('mobile-menu-open');
      document.body.style.overflow = '';
    }

    return () => {
      document.removeEventListener('click', handleClickOutside);
      // Always restore scrolling on cleanup
      document.body.classList.remove('mobile-menu-open');
      document.body.style.overflow = '';
    };
  }, [isMobileMenuOpen]);

  // Additional cleanup effect to ensure scrolling is restored
  useEffect(() => {
    // Force enable scrolling when component mounts
    document.body.style.overflow = '';
    document.documentElement.style.overflow = '';
    
    return () => {
      // Cleanup function to restore scrolling when component unmounts
      document.body.style.overflow = '';
      document.documentElement.style.overflow = '';
      document.body.classList.remove('mobile-menu-open');
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

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  const closeMobileMenu = () => {
    setIsMobileMenuOpen(false);
    // Force restore scrolling and remove mobile menu class
    document.body.style.overflow = '';
    document.body.classList.remove('mobile-menu-open');
  };

  const scrollToSection = (sectionId) => {
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
    closeMobileMenu();
  };



  // Handle escape key to close mobile menu
  useEffect(() => {
    const handleEscapeKey = (event) => {
      if (event.key === 'Escape' && isMobileMenuOpen) {
        setIsMobileMenuOpen(false);
      }
    };

    if (isMobileMenuOpen) {
      document.addEventListener('keydown', handleEscapeKey);
      // Focus the first mobile menu link for better accessibility
      const firstMobileLink = document.querySelector('.mobile-nav-link');
      if (firstMobileLink) {
        firstMobileLink.focus();
      }
    }

    return () => {
      document.removeEventListener('keydown', handleEscapeKey);
    };
  }, [isMobileMenuOpen]);

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
          
          {/* Desktop Navigation Links */}
          <div className="nav-links desktop-only">
            <button onClick={() => scrollToSection('features')} className="nav-link-button">Features</button>
            <button onClick={() => scrollToSection('about')} className="nav-link-button">About</button>
            <button onClick={() => scrollToSection('pricing')} className="nav-link-button">Pricing</button>
            <button onClick={() => scrollToSection('faq')} className="nav-link-button">FAQ</button>
            <Link to="/blog" className="nav-link-button">Blog</Link>
            <button onClick={() => scrollToSection('contact')} className="nav-link-button">Contact</button>
          </div>
          
          {/* Desktop Auth Buttons */}
          <div className="nav-auth desktop-only">
            <Link to="/login" className="login-button">Login</Link>
            <Link to="/signup" className="signup-button">Sign Up</Link>
          </div>
          
          {/* Mobile Auth Buttons */}
          <div className="nav-auth mobile-only">
            <Link to="/login" className="login-button">Login</Link>
            <Link to="/signup" className="signup-button">Sign Up</Link>
          </div>
          
          {/* Mobile Menu Button */}
          <button 
            className={`mobile-menu-button ${isMobileMenuOpen ? 'active' : ''}`}
            onClick={toggleMobileMenu}
            aria-label="Toggle mobile menu"
          >
            <span></span>
            <span></span>
            <span></span>
          </button>
        </div>
        
        {/* Mobile Navigation Menu */}
        <div className={`mobile-menu ${isMobileMenuOpen ? 'open' : ''}`}>
          <div className="mobile-menu-links">
            <button onClick={() => scrollToSection('features')} className="mobile-nav-link">Features</button>
            <button onClick={() => scrollToSection('about')} className="mobile-nav-link">About</button>
            <button onClick={() => scrollToSection('pricing')} className="mobile-nav-link">Pricing</button>
            <button onClick={() => scrollToSection('faq')} className="mobile-nav-link">FAQ</button>
            <Link to="/blog" className="mobile-nav-link" onClick={closeMobileMenu}>Blog</Link>
            <button onClick={() => scrollToSection('contact')} className="mobile-nav-link">Contact</button>
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
                AI-Powered • Real-Time • Built for Professional Traders
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
                Start Free Trial
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Data Powered By Section */}
      <section className="data-powered">
        <div className="data-powered-inner">
          <h2 className="data-powered-title">DATA DRIVEN BY</h2>
          <div className="data-powered-logos">
            <div className="logo-scroll">
              <div className="logo-item">
                <img 
                  src={tradingviewLogo} 
                  alt="TradingView" 
                  className="data-logo"
                />
              </div>
              <div className="logo-item">
                <img 
                  src={finnhubLogo} 
                  alt="Finnhub" 
                  className="data-logo"
                />
              </div>
              <div className="logo-item">
                <img 
                  src={fxstreetLogo} 
                  alt="FXStreet" 
                  className="data-logo"
                />
              </div>
              <div className="logo-item">
                <img 
                  src={cnbcLogo} 
                  alt="CNBC" 
                  className="data-logo"
                />
              </div>
              {/* Duplicate logos for seamless scrolling */}
              <div className="logo-item">
                <img 
                  src={tradingviewLogo} 
                  alt="TradingView" 
                  className="data-logo"
                />
              </div>
              <div className="logo-item">
                <img 
                  src={finnhubLogo} 
                  alt="Finnhub" 
                  className="data-logo"
                />
              </div>
              <div className="logo-item">
                <img 
                  src={fxstreetLogo} 
                  alt="FXStreet" 
                  className="data-logo"
                />
              </div>
              <div className="logo-item">
                <img 
                  src={cnbcLogo} 
                  alt="CNBC" 
                  className="data-logo"
                />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="features">
        <div className="features-inner">
          <h2 className="section-title">Why Professional Traders Choose FXSentinel</h2>
          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M14 2H6C4.9 2 4 2.9 4 4V20C4 21.1 4.9 22 6 22H18C19.1 22 20 21.1 20 20V8L14 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <polyline points="14,2 14,8 20,8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <line x1="16" y1="13" x2="8" y2="13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <line x1="16" y1="17" x2="8" y2="17" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <polyline points="10,9 9,9 8,9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
              <h3>Never Miss Market-Moving Events</h3>
              <p>Stop losing money because you missed the news. We monitor 100+ sources including premium financial data providers and global news feeds to catch every economic release that moves your trades - from major central bank decisions to key economic indicators.</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M9 11H15M9 15H15M9 7H15M5 3H19C20.1046 3 21 3.89543 21 5V19C21 20.1046 20.1046 21 19 21H5C3.89543 21 3 20.1046 3 19V5C3 3.89543 3.89543 3 5 3Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M7 7H17V9H7V7Z" fill="currentColor"/>
                  <path d="M7 11H17V13H7V11Z" fill="currentColor"/>
                  <path d="M7 15H17V17H7V15Z" fill="currentColor"/>
                </svg>
              </div>
              <h3>Understand the "Why" Behind Every Move</h3>
              <p>Don't just see the numbers - understand what they mean. Our AI analysis instantly explains how each economic event will impact EUR/USD, USD/JPY, and Gold, giving you the context to make smarter trading decisions.</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M13 2L3 14H12L11 22L21 10H12L13 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
              <h3>Get Alerts Before the Market Reacts</h3>
              <p>While others are still reading the news, you're already positioned. Receive instant Telegram notifications with AI-powered analysis and specific pair reactions within seconds of economic releases.</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
                  <circle cx="12" cy="12" r="6" stroke="currentColor" strokeWidth="2"/>
                  <circle cx="12" cy="12" r="2" stroke="currentColor" strokeWidth="2"/>
                </svg>
              </div>
              <h3>Focus on What Matters to Your Trades</h3>
              <p>Stop wasting time on irrelevant news. Get targeted analysis for your specific currency pairs and commodities, so you know exactly which instruments will be most affected by each economic event.</p>
            </div>
          </div>
                      <div className="features-cta">
              <p className="features-cta-text"><span>Still don't believe us ?</span> 👉</p>
              <Link to="/signup" className="features-cta-button">Take our 3-day free trial</Link>
            </div>
        </div>
      </section>

      {/* Alerts Section */}
      <section className="alerts-showcase">
        <div className="alerts-showcase-inner">
          <div className="alerts-content">
            <div className="phone-mockup">
              <img 
                src={phoneImage} 
                alt="FXSentinel Alerts on iPhone" 
                className="phone-image"
              />
            </div>
            <div className="alerts-text">
              <h2 className="alerts-title">Never Miss Out.</h2>
              <p className="alerts-description">
                While other traders are still processing the news, you could be positioned for profit. 
                Get instant Telegram alerts with AI analysis that tells you exactly what to expect.
              </p>
              <div className="telegram-icon">
                <img 
                  src={telegramLogo} 
                  alt="Telegram" 
                  className="telegram-logo"
                />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* About Section */}
      <section id="about" className="about">
        <div className="about-inner">
          <div className="about-content">
            <div className="about-text">
              <h2 className="about-title">Built By Traders Who Know What You Need</h2>
              <div className="about-text-background">
                <p>
                  We are forex traders who've spent years in the markets, and it is arrogant for anyone to say 
                  they know exactly what moves the market, but it is undeniable that news plays a major role in 
                  the market. That's why we built FXSentinel - to solve the exact problem we faced. We know that 
                  in today's markets, not being able to instantly understand news can cost you thousands.
                </p>
                <p>
                  Our advanced AI analysis system processes thousands of data points from premium 
                  financial sources to give you the edge you need. Stop losing money to missed opportunities 
                  and start trading with confidence. We're building the best tool for what we do.
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
                <h3 className="counter" data-target="100">0</h3>
                <p>News Sources</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="pricing">
        <div className="pricing-inner">
          <h2 className="section-title">Start Trading Smarter Today</h2>
          <p className="pricing-description">One powerful plan that gives you everything you need to understand market moves.</p>
          <div className="pricing-single">
            <div className="pricing-card featured">
              <h3>Premium</h3>
              <div className="price">$19.99<span>/month</span></div>
              <ul>
                <li>Understand the market with instant AI analysis</li>
                <li>Monitor all major currency pairs</li>
                <li>Get alerts before news breaks</li>
                <li>Professional trading dashboard</li>
                <li>Understand every market move</li>
                <li>Priority customer support</li>
                <li>Customize alerts for your strategy</li>
                <li>Learn from historical patterns</li>
              </ul>
              <Link to="/signup" className="pricing-button">Start Understanding the Market</Link>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section id="faq" className="faq">
        <div className="faq-inner">
          <h2 className="section-title">Frequently Asked Questions</h2>
          <div className="faq-grid">
            <div className="faq-item">
              <h3>How accurate is the AI analysis?</h3>
              <p>Our advanced AI analysis system analyzes historical patterns, market correlations, and economic relationships to provide insights into market movements. While no analysis is 100% certain, our AI identifies market-moving events and their potential impact based on historical data.</p>
            </div>
            <div className="faq-item">
              <h3>What data sources do you use?</h3>
              <p>We aggregate data from premium financial data providers, economic calendars, and global news sources. All sources are verified and trusted by professional traders worldwide.</p>
            </div>
            <div className="faq-item">
              <h3>How fast are the alerts delivered?</h3>
              <p>Our system delivers alerts within seconds of economic releases. Telegram notifications are instant, and our AI analysis is typically available within 30-60 seconds of the data release.</p>
            </div>
            <div className="faq-item">
              <h3>Can I customize which events I receive alerts for?</h3>
              <p>Yes! Professional subscribers can customize their alert preferences by currency pair, impact level, and specific economic indicators. You'll only receive alerts for events that matter to your trading strategy.</p>
            </div>
            <div className="faq-item">
              <h3>Is my trading data secure?</h3>
              <p>Absolutely. We use bank-level encryption and never store your trading positions or account information. We only process market data and economic events to provide analysis.</p>
            </div>
            <div className="faq-item">
              <h3>Can I cancel my subscription anytime?</h3>
              <p>Yes, you can cancel your subscription at any time with no questions asked. Your access will continue until the end of your current billing period.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Contact Section */}
      <section id="contact" className="contact">
        <div className="contact-inner">
          <h2 className="section-title">Get in Touch</h2>
          <p className="section-subtitle">
            Have questions? We're here to help you.
          </p>
          <div className="contact-single">
            <div className="contact-header">
              <svg className="email-icon" width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M4 4H20C21.1 4 22 4.9 22 6V18C22 19.1 21.1 20 20 20H4C2.9 20 2 19.1 2 18V6C2 4.9 2.9 4 4 4Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <polyline points="22,6 12,13 2,6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              <h3>Contact Us</h3>
            </div>
            <p>fxsentinelapp@gmail.com</p>
            <span>We guarantee to respond within 24 hours</span>
            <a 
              href="mailto:fxsentinelapp@gmail.com" 
              className="email-button"
              target="_blank"
              rel="noopener noreferrer"
            >
              Email Us
            </a>
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
              <p>Advanced AI analysis system for forex news and professional traders.</p>
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
              <a href="#faq">FAQ</a>
              <a href="#contact">Contact</a>
            </div>
            <div className="footer-section">
              <h4>Legal</h4>
              <Link to="/disclaimer">Disclaimer</Link>
              <Link to="/privacy">Privacy Policy</Link>
            </div>
          </div>
          
          {/* Disclaimer Section */}
          <div className="disclaimer-section">
            <div className="disclaimer-content">
              <h4>Disclaimer</h4>
              <p>
                FXSentinel is a market intelligence and data analytics platform. We are not a brokerage, 
                investment advisor, or financial institution.                 The platform provides advanced AI analysis system 
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
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage; 