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
import featuresGlanceImage from '../assets/FXSentinelFeaturesGlance.png';
import LiveTicker from './LiveTicker';
import { useMeta } from '../hooks/useMeta';
import { 
  trackLandingPageView, 
  trackSignupClick, 
  trackEngagement, 
  trackFeatureUsage,
  trackCTAClick,
  trackTestimonialView,
  trackFeatureCardInteraction
} from '../utils/analytics';

/** Renders star rating (4, 4.5, 5) with optional half star for 4.5. */
const StarRating = ({ rating }) => {
  const full = Math.floor(rating);
  const half = rating % 1 >= 0.5;
  return (
    <div className="testimonial-rating">
      {[...Array(full)].map((_, i) => (
        <span key={i} className="star">★</span>
      ))}
      {half && (
        <span className="star star-half" aria-hidden="true">★</span>
      )}
    </div>
  );
};

const LandingPage = () => {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  useMeta(
    'FXSentinel - Smarter Market Dashboard | Powered with AI',
    'Fundamentals and macroeconomics, simplified for retail traders. Get real-time alerts, AI-powered news analysis, and actionable market insights in one place.'
  );

  useEffect(() => {
    trackLandingPageView();
  }, []);


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

  // Scroll-triggered animations for sections
  useEffect(() => {
    const observerOptions = {
      threshold: 0.15,
      rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('animate-in');
          
          // Stagger animations for child elements
          const children = entry.target.querySelectorAll('.animate-on-scroll');
          children.forEach((child, index) => {
            setTimeout(() => {
              child.classList.add('animate-in');
            }, index * 100);
          });
          
          observer.unobserve(entry.target);
        }
      });
    }, observerOptions);

    // Observe all sections
    const sections = document.querySelectorAll('section[id], .data-powered, .alerts-showcase');
    sections.forEach(section => {
      observer.observe(section);
    });

    return () => {
      sections.forEach(section => {
        observer.unobserve(section);
      });
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
      const offset = 80; // Account for navbar height
      const elementPosition = element.getBoundingClientRect().top;
      const offsetPosition = elementPosition + window.pageYOffset - offset;

      window.scrollTo({
        top: offsetPosition,
        behavior: 'smooth'
      });
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
            <Link 
              to="/signup" 
              className="signup-button"
              onClick={() => {
                trackSignupClick('nav_desktop');
                trackEngagement('nav_signup_click');
              }}
            >
              Sign Up
            </Link>
          </div>
          
          {/* Mobile Auth Buttons */}
          <div className="nav-auth mobile-only">
            <Link to="/login" className="login-button">Login</Link>
            <Link 
              to="/signup" 
              className="signup-button"
              onClick={() => {
                trackSignupClick('nav_mobile');
                trackEngagement('nav_signup_click');
              }}
            >
              Sign Up
            </Link>
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
        <div className="news-headline-1">Japan issues sternest intervention warning as yen weakness persists</div>
        <div className="news-headline-2">Yen strengthens in thin holiday trade amid intervention threat</div>
        <div className="news-headline-3">Global markets rise; yen on intervention watch as gold and stocks gain</div>
        <div className="news-headline-4">IMF data shows global FX reserves stabilizing in Q3 2025</div>
        <div className="news-headline-5">Japan finance minister warns on excessive forex volatility</div>
        <div className="news-headline-6">Asia FX firms as dollar dips ahead of key data; yen surges on intervention threat</div>
        <div className="news-headline-7">USD/JPY extends losses as Japan officials caution on one-sided currency moves</div>
        <div className="news-headline-8">Japanese yen rises versus weaker US dollar on intervention fears</div>
        <div className="news-headline-9">EUR/JPY retraces from record highs as yen rebounds on intervention hopes</div>
        <div className="news-headline-10">EUR/USD advances on US dollar weakness and broad risk sentiment</div>
        <div className="news-headline-11">Dollar rises amid mixed jobs data and soft inflation prints</div>
        <div className="news-headline-12">Sterling finds support while yen weakens despite BoJ action, dollar drifts</div>
        
        <div className="hero-inner">
          <div className="hero-content">
            {/* Badge */}
            <div className="hero-badge-container">
              <div className="hero-badge">
                <span className="badge-dot"></span>
                AI-Powered • Real-Time • Built for Traders
              </div>
            </div>
            
            <h1 className="hero-title">
              Turning <span className="highlight">Macro News</span> into <span className="highlight">Market Moves</span>
            </h1>
            
            <p className="hero-subtitle">
              FXSentinel simplifies complex trading news, making it accessible
              and usable for every trader
            </p>
            
            {/* Live Market Ticker */}
            <LiveTicker />
            
            <div className="hero-buttons">
              <Link 
                to="/signup" 
                className="primary-button"
                onClick={() => {
                  trackCTAClick('start_for_free', 'hero_section');
                  trackSignupClick('hero_button');
                  trackEngagement('hero_signup_button_click');
                }}
              >
                Start for Free
              </Link>
            </div>
          </div>
        </div>

        {/* Features at a Glance - Merged into Hero Section (same load-time fadeInUp as hero-content) */}
        <div className="hero-features-section">
          <div className="hero-features-inner">
            <div className="hero-features-content">
              <h2 className="hero-features-title">Features at a Glance</h2>
              <p className="hero-features-description">
                Get a comprehensive view of everything FXSentinel offers. From real-time economic indicators 
                to AI-powered analysis, prediction markets, and live news feeds - all in one powerful dashboard 
                designed for serious traders.
              </p>
              <Link 
                to="/signup" 
                className="hero-features-button primary-button"
                onClick={() => {
                  trackCTAClick('explore_all_features', 'hero_features_section');
                  trackSignupClick('features_at_glance');
                  trackEngagement('features_at_glance_cta_click');
                }}
              >
                Explore All Features
              </Link>
            </div>
            <div className="hero-features-image-container">
              <img 
                src={featuresGlanceImage} 
                alt="FXSentinel dashboard with real-time economic calendar, AI analysis, and macro alerts" 
                className="hero-features-image"
                loading="lazy"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Data Powered By Section */}
      <section className="data-powered">
        <div className="data-powered-inner">
          <h2 className="data-powered-title animate-on-scroll">DATA DRIVEN BY</h2>
          <div className="data-powered-logos">
            <div className="logo-scroll">
              <div className="logo-item">
                <img 
                  src={tradingviewLogo} 
                  alt="TradingView" 
                  className="data-logo"
                  loading="lazy"
                />
              </div>
              <div className="logo-item">
                <img 
                  src={finnhubLogo} 
                  alt="Finnhub" 
                  className="data-logo"
                  loading="lazy"
                />
              </div>
              <div className="logo-item">
                <img 
                  src={fxstreetLogo} 
                  alt="FXStreet" 
                  className="data-logo"
                  loading="lazy"
                />
              </div>
              <div className="logo-item">
                <img 
                  src={cnbcLogo} 
                  alt="CNBC" 
                  className="data-logo"
                  loading="lazy"
                />
              </div>
              {/* Duplicate logos for seamless scrolling */}
              <div className="logo-item">
                <img 
                  src={tradingviewLogo} 
                  alt="TradingView" 
                  className="data-logo"
                  loading="lazy"
                />
              </div>
              <div className="logo-item">
                <img 
                  src={finnhubLogo} 
                  alt="Finnhub" 
                  className="data-logo"
                  loading="lazy"
                />
              </div>
              <div className="logo-item">
                <img 
                  src={fxstreetLogo} 
                  alt="FXStreet" 
                  className="data-logo"
                  loading="lazy"
                />
              </div>
              <div className="logo-item">
                <img 
                  src={cnbcLogo} 
                  alt="CNBC" 
                  className="data-logo"
                  loading="lazy"
                />
              </div>
              {/* Additional duplicates for longer loop */}
              <div className="logo-item">
                <img 
                  src={tradingviewLogo} 
                  alt="TradingView" 
                  className="data-logo"
                  loading="lazy"
                />
              </div>
              <div className="logo-item">
                <img 
                  src={finnhubLogo} 
                  alt="Finnhub" 
                  className="data-logo"
                  loading="lazy"
                />
              </div>
              <div className="logo-item">
                <img 
                  src={fxstreetLogo} 
                  alt="FXStreet" 
                  className="data-logo"
                  loading="lazy"
                />
              </div>
              <div className="logo-item">
                <img 
                  src={cnbcLogo} 
                  alt="CNBC" 
                  className="data-logo"
                  loading="lazy"
                />
              </div>
              <div className="logo-item">
                <img 
                  src={tradingviewLogo} 
                  alt="TradingView" 
                  className="data-logo"
                  loading="lazy"
                />
              </div>
              <div className="logo-item">
                <img 
                  src={finnhubLogo} 
                  alt="Finnhub" 
                  className="data-logo"
                  loading="lazy"
                />
              </div>
              <div className="logo-item">
                <img 
                  src={fxstreetLogo} 
                  alt="FXStreet" 
                  className="data-logo"
                  loading="lazy"
                />
              </div>
              <div className="logo-item">
                <img 
                  src={cnbcLogo} 
                  alt="CNBC" 
                  className="data-logo"
                  loading="lazy"
                />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="features">
        <div className="features-inner">
          <h2 className="section-title animate-on-scroll">Why Traders Choose FXSentinel</h2>
          <div className="features-grid">
            <div 
              className="feature-card animate-on-scroll"
              onMouseEnter={() => trackFeatureCardInteraction('never_miss_events', 'hover')}
              onClick={() => trackFeatureCardInteraction('never_miss_events', 'click')}
            >
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
              <p>Stop losing money because you missed the news. We monitor 100+ sources so you see the macro-economic releases that move your trades—from central bank decisions and policy signals to key indicators like CPI, NFP, and GDP.</p>
              <Link to="/blog/central-bank-decisions-currency-pairs" className="feature-read-more">Read more →</Link>
            </div>
            <div 
              className="feature-card animate-on-scroll"
              onMouseEnter={() => trackFeatureCardInteraction('understand_why', 'hover')}
              onClick={() => trackFeatureCardInteraction('understand_why', 'click')}
            >
              <div className="feature-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M9 11H15M9 15H15M9 7H15M5 3H19C20.1046 3 21 3.89543 21 5V19C21 20.1046 20.1046 21 19 21H5C3.89543 21 3 20.1046 3 19V5C3 3.89543 3.89543 3 5 3Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M7 7H17V9H7V7Z" fill="currentColor"/>
                  <path d="M7 11H17V13H7V11Z" fill="currentColor"/>
                  <path d="M7 15H17V17H7V15Z" fill="currentColor"/>
                </svg>
              </div>
              <h3>Understand the "Why" Behind Every Move</h3>
              <p>Macro moves markets, but it can feel overwhelming. We're built to help beginner and experienced traders alike: our AI explains how each economic release and central bank decision affects major pairs and Gold in plain language—so you can build your macro intuition and make smarter trades.</p>
              <Link to="/blog/ai-powered-news-analysis-future-of-trading" className="feature-read-more">Read more →</Link>
            </div>
            <div 
              className="feature-card animate-on-scroll"
              onMouseEnter={() => trackFeatureCardInteraction('alerts_before_market', 'hover')}
              onClick={() => trackFeatureCardInteraction('alerts_before_market', 'click')}
            >
              <div className="feature-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M13 2L3 14H12L11 22L21 10H12L13 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
              <h3>Get Alerts the Moment the News Drops</h3>
              <p>While others are still reading the news, you're already positioned. Instant Telegram alerts with AI-powered macro analysis and pair-by-pair impact—delivered within seconds of each economic release.</p>
              <Link to="/blog/turning-news-actionable-signals" className="feature-read-more">Read more →</Link>
            </div>
            <div 
              className="feature-card animate-on-scroll"
              onMouseEnter={() => trackFeatureCardInteraction('focus_on_trades', 'hover')}
              onClick={() => trackFeatureCardInteraction('focus_on_trades', 'click')}
            >
              <div className="feature-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
                  <circle cx="12" cy="12" r="6" stroke="currentColor" strokeWidth="2"/>
                  <circle cx="12" cy="12" r="2" stroke="currentColor" strokeWidth="2"/>
                </svg>
              </div>
              <h3>Focus on What Matters to Your Trades</h3>
              <p>Cut through the noise. We surface only the macro events that matter to your currency pairs and commodities—so you see which instruments are most affected by each release without wasting time on the rest.</p>
              <Link to="/blog/understanding-forex-market-sentiment" className="feature-read-more">Read more →</Link>
            </div>
          </div>
                      <div className="features-cta">
              <p className="features-cta-text"><span>Ready to get started?</span> 👉</p>
              <Link 
                to="/signup" 
                className="features-cta-button"
                onClick={() => {
                  trackCTAClick('start_free_today', 'features_section');
                  trackSignupClick('features_cta');
                }}
              >
                Start Free Today
              </Link>
            </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section id="testimonials" className="testimonials">
        <div className="testimonials-inner">
          <h2 className="section-title animate-on-scroll">Trusted by Traders Worldwide</h2>
          <p className="testimonials-subtitle animate-on-scroll"></p>
          <div className="testimonials-grid">
            <div 
              className="testimonial-card animate-on-scroll"
              onMouseEnter={() => trackTestimonialView(0)}
            >
              <StarRating rating={5} />
              <p className="testimonial-text">
                "FXSentinel helped me understand why EUR/USD moved 200 pips after the ECB announcement. I was positioned before the move and made my biggest profit of the month. The AI analysis is incredibly accurate."
              </p>
              <div className="testimonial-author">
                <div className="testimonial-avatar">
                  <span>MJ</span>
                </div>
                <div className="testimonial-info">
                  <h4>Michael Johnson</h4>
                  <p>Professional Forex Trader</p>
                </div>
              </div>
            </div>

            <div className="testimonial-card animate-on-scroll">
              <StarRating rating={4.5} />
              <p className="testimonial-text">
                "I used to spend hours reading news and still miss important events. Now I get instant Telegram alerts with analysis that tells me exactly what to expect. This tool has completely changed my trading workflow."
              </p>
              <div className="testimonial-author">
                <div className="testimonial-avatar">
                  <span>SC</span>
                </div>
                <div className="testimonial-info">
                  <h4>Sarah Chen</h4>
                  <p>Day Trader</p>
                </div>
              </div>
            </div>

            <div className="testimonial-card animate-on-scroll">
              <StarRating rating={5} />
              <p className="testimonial-text">
                "The AI analysis is incredible. It explains market moves in a way that makes sense, not just technical jargon. I've avoided several bad trades thanks to the insights provided. Worth every penny."
              </p>
              <div className="testimonial-author">
                <div className="testimonial-avatar">
                  <span>DR</span>
                </div>
                <div className="testimonial-info">
                  <h4>David Rodriguez</h4>
                  <p>Swing Trader</p>
                </div>
              </div>
            </div>

            <div className="testimonial-card animate-on-scroll">
              <StarRating rating={4} />
              <p className="testimonial-text">
                "As someone new to forex trading, FXSentinel's explanations help me understand the 'why' behind market movements. The economic calendar with AI analysis is a game-changer for learning."
              </p>
              <div className="testimonial-author">
                <div className="testimonial-avatar">
                  <span>EW</span>
                </div>
                <div className="testimonial-info">
                  <h4>Emma Williams</h4>
                  <p>Beginner Trader</p>
                </div>
              </div>
            </div>

            <div className="testimonial-card animate-on-scroll">
              <StarRating rating={4.5} />
              <p className="testimonial-text">
                "The prediction markets feature is brilliant. Seeing how the market is pricing central bank decisions helps me position my trades better. This is the most comprehensive trading tool I've used."
              </p>
              <div className="testimonial-author">
                <div className="testimonial-avatar">
                  <span>AK</span>
                </div>
                <div className="testimonial-info">
                  <h4>Alex Kumar</h4>
                  <p>Institutional Trader</p>
                </div>
              </div>
            </div>

            <div className="testimonial-card animate-on-scroll">
              <StarRating rating={5} />
              <p className="testimonial-text">
                "I've tried multiple news aggregation tools, but none compare to FXSentinel. The real-time alerts and market sentiment analysis have improved my win rate significantly. Highly recommend!"
              </p>
              <div className="testimonial-author">
                <div className="testimonial-avatar">
                  <span>LT</span>
                </div>
                <div className="testimonial-info">
                  <h4>Lisa Thompson</h4>
                  <p>Professional Trader</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Alerts Section */}
      <section className="alerts-showcase">
        <div className="alerts-showcase-inner">
          <div className="alerts-content">
            <div className="phone-mockup animate-on-scroll">
              <img 
                src={phoneImage} 
                alt="FXSentinel instant Telegram alerts with AI analysis on iPhone" 
                className="phone-image"
                loading="lazy"
              />
            </div>
            <div className="alerts-text animate-on-scroll">
              <h2 className="alerts-title">Never Miss The 'Why'.</h2>
              <p className="alerts-description">
                While other traders are still processing the news, you could be positioned for profit. 
                Get instant Telegram alerts with AI analysis that tells you exactly what to expect.
              </p>
              <div className="telegram-icon">
                <img 
                  src={telegramLogo} 
                  alt="Telegram" 
                  className="telegram-logo"
                  loading="lazy"
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
              <h2 className="about-title animate-on-scroll">Built By Traders Who Know What You Need</h2>
              <div className="about-text-background animate-on-scroll">
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

      {/* What is FXSentinel? – canonical definition for SEO and GEO */}
      <section id="what-is-fxsentinel" className="what-is-section">
        <div className="what-is-inner">
          <h2 className="what-is-title animate-on-scroll">What is FXSentinel?</h2>
          <p className="what-is-lead animate-on-scroll">
            A <strong>market intelligence platform</strong> for forex traders: <strong>real-time alerts</strong>, <strong>AI-powered news analysis</strong>, and actionable macro insights in one place. We focus on the <strong>fundamentals</strong> behind market moves rather than <strong>technicals</strong>—for traders who want to trade the <strong>real reason markets move</strong>.
          </p>
          <div className="what-is-grid animate-on-scroll">
            <div className="what-is-card what-is-features">
              <h3 className="what-is-card-title">What you get</h3>
              <ul className="what-is-list">
                <li>AI news analysis and macro impact on currency pairs</li>
                <li>Economic calendar and high-impact event alerts</li>
                <li>Instant Telegram alerts with pair-by-pair impact</li>
                <li>Dashboard with live news and prediction-style data</li>
              </ul>
            </div>
            <div className="what-is-card">
              <h3 className="what-is-card-title">Who it&apos;s for</h3>
              <p>Beginner to experienced retail forex traders who want to understand the &quot;why&quot; behind market moves without spending hours on news.</p>
            </div>
            <div className="what-is-card what-is-not">
              <h3 className="what-is-card-title">What we&apos;re not</h3>
              <p>We provide analysis and tools, not trading signals or financial advice. We are not a broker or a copy-trading or signals provider, and we do not guarantee any trading results.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="pricing">
        <div className="pricing-inner">
          <h2 className="section-title animate-on-scroll">Start Trading Smarter Today</h2>
          <p className="pricing-description animate-on-scroll">Choose the plan that fits your trading style. Start free, upgrade anytime.</p>
          <div className="pricing-grid">
            <div className="pricing-card animate-on-scroll">
              <h3>Free</h3>
              <div className="price">$0<span>/month</span></div>
              <p className="pricing-subtitle">Perfect for getting started</p>
              <ul>
                <li>15 AI analyses per month</li>
                <li>Real-time market alerts</li>
                <li>Economic calendar access</li>
                <li>Live news feed</li>
                <li>All major currency pairs</li>
                <li>Telegram notifications</li>
                <li>Professional dashboard</li>
              </ul>
              <Link to="/signup" className="pricing-button">Get Started Free</Link>
            </div>
            <div className="pricing-card featured animate-on-scroll">
              <div className="popular-badge">Most Popular</div>
              <h3>Premium</h3>
              <div className="price">$14.99<span>/month</span></div>
              <p className="pricing-subtitle">For serious traders</p>
              <ul>
                <li>50 AI analyses per day (~1,500/month)</li>
                <li>Everything in Free plan</li>
                <li>Priority support</li>
                <li>Advanced alert customization</li>
                <li>Historical pattern analysis</li>
                <li>Custom currency pair filters</li>
                <li>Impact level filtering</li>
                <li>Quiet hours configuration</li>
              </ul>
              <Link to="/signup?plan=premium" className="pricing-button">Start Premium</Link>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section id="faq" className="faq">
        <div className="faq-inner">
          <h2 className="section-title animate-on-scroll">Frequently Asked Questions</h2>
          <div className="faq-grid">
            <div className="faq-item animate-on-scroll">
              <h3>How accurate is the AI analysis?</h3>
              <p>Our advanced AI analysis system analyzes historical patterns, market correlations, and economic relationships to provide insights into market movements. While no analysis is 100% certain, our AI identifies market-moving events and their potential impact based on historical data.</p>
            </div>
            <div className="faq-item animate-on-scroll">
              <h3>What data sources do you use?</h3>
              <p>We aggregate data from premium financial data providers, economic calendars, and global news sources. All sources are verified and trusted by professional traders worldwide.</p>
            </div>
            <div className="faq-item animate-on-scroll">
              <h3>How fast are the alerts delivered?</h3>
              <p>Our system delivers alerts within seconds of economic releases. Telegram notifications are instant, and our AI analysis is typically available within 30-60 seconds of the data release.</p>
            </div>
            <div className="faq-item animate-on-scroll">
              <h3>Can I customize which events I receive alerts for?</h3>
              <p>Yes! Professional subscribers can customize their alert preferences by currency pair, impact level, and specific economic indicators. You'll only receive alerts for events that matter to your trading strategy.</p>
            </div>
            <div className="faq-item animate-on-scroll">
              <h3>Is my trading data secure?</h3>
              <p>Absolutely. We use bank-level encryption and never store your trading positions or account information. We only process market data and economic events to provide analysis.</p>
            </div>
            <div className="faq-item animate-on-scroll">
              <h3>Can I cancel my subscription anytime?</h3>
              <p>Yes, you can cancel your subscription at any time with no questions asked. Your access will continue until the end of your current billing period.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Contact Section */}
      <section id="contact" className="contact">
        <div className="contact-inner">
          <h2 className="section-title animate-on-scroll">Get in Touch</h2>
          <p className="section-subtitle animate-on-scroll">
            Have questions? We're here to help you.
          </p>
          <div className="contact-single animate-on-scroll">
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
              
              {/* Social Media Buttons */}
              <div className="social-media-buttons">
                <a 
                  href="https://x.com/fxsentinel?s=21" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="social-button x-button"
                  aria-label="Follow us on X (Twitter)"
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
                  </svg>
                </a>
                <a 
                  href="https://www.instagram.com/fxsentinel_" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="social-button instagram-button"
                  aria-label="Follow us on Instagram"
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/>
                  </svg>
                </a>
                <a 
                  href="https://www.tiktok.com/@fxsentinel_" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="social-button tiktok-button"
                  aria-label="Follow us on TikTok"
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5 20.1a6.34 6.34 0 0 0 10.86-4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1-.1z"/>
                  </svg>
                </a>
                <a 
                  href="https://t.me/fxsentinel_channel" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="social-button telegram-button"
                  aria-label="Join our Telegram community"
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/>
                  </svg>
                </a>
              </div>
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
            <p>&copy; 2025 FXSentinel. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage; 