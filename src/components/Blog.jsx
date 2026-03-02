import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import logoPng from '../assets/fxsentinel_logo_nobg.png';
import logoWebp from '../assets/fxsentinel_logo_nobg.webp';
import analyticsTracker, { trackBlogPostEngagement } from '../utils/analytics';
import { useMeta } from '../hooks/useMeta';
import './Blog.css';

const Blog = () => {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  useMeta(
    'FXSentinel Blog - Trading Insights & Market Analysis',
    'Expert insights on forex trading, market analysis, and AI-powered trading tools. Learn how to trade economic news, understand market sentiment, and make better trading decisions.'
  );

  useEffect(() => {
    analyticsTracker.trackPageView('blog');

    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  const closeMobileMenu = () => {
    setIsMobileMenuOpen(false);
  };

  // Blog posts: trending 2025 topics + evergreen content
  const blogPosts = [
    {
      id: 7,
      slug: 'geopolitical-tensions-forex-trading-2025',
      title: "Navigating Forex Volatility Amid Geopolitical Tensions in 2025",
      excerpt: "Geopolitical risk has emerged as a dominant theme in forex markets. Learn how trade disputes, safe-haven flows, and political instability affect currency pairs.",
      author: "FXSentinel Team",
      date: "March 1, 2025",
      readTime: "10 min read",
      category: "Market Analysis",
      image: logoPng
    },
    {
      id: 8,
      slug: 'fed-ecb-rate-divergence-currency-markets',
      title: "Fed vs ECB: Central Bank Divergence and Currency Markets in 2025",
      excerpt: "The Fed and ECB have diverged sharply on interest rates. Explore how this 150–200 basis point differential is driving EUR/USD and creating trading opportunities.",
      author: "FXSentinel Team",
      date: "March 1, 2025",
      readTime: "9 min read",
      category: "Market Analysis",
      image: logoPng
    },
    {
      id: 9,
      slug: 'gold-rally-safe-haven-inflation-hedge',
      title: "Gold's Meteoric Rise: Safe Haven and Inflation Hedge for Forex Traders",
      excerpt: "Gold has shattered records in 2025, surging 50–60% as a debasement hedge. Learn how forex traders can use XAU/USD and gold correlations.",
      author: "FXSentinel Team",
      date: "March 1, 2025",
      readTime: "9 min read",
      category: "Market Analysis",
      image: logoPng
    },
    {
      id: 10,
      slug: 'bitcoin-institutional-adoption-forex-traders',
      title: "Bitcoin and Forex: Institutional Adoption Reshapes Markets in 2025",
      excerpt: "Institutions accumulated over 800,000 BTC in 2025. Explore how Bitcoin's mainstream adoption affects forex traders and correlation patterns.",
      author: "FXSentinel Team",
      date: "March 1, 2025",
      readTime: "8 min read",
      category: "Technology",
      image: logoPng
    },
    {
      id: 1,
      slug: 'ai-powered-news-analysis-future-of-trading',
      title: "AI-Powered News Analysis: The Future of Trading",
      excerpt: "Discover how artificial intelligence is revolutionizing the way traders process and react to market news, providing real-time insights and predictive analytics.",
      author: "FXSentinel Team",
      date: "August 15, 2025",
      readTime: "8 min read",
      category: "Technology",
      image: logoPng
    },
    {
      id: 2,
      slug: 'central-bank-decisions-currency-pairs',
      title: "The Impact of Central Bank Decisions on Currency Pairs",
      excerpt: "Explore how central bank policies and interest rate decisions affect currency movements and create trading opportunities across major pairs.",
      author: "FXSentinel Team",
      date: "August 12, 2025",
      readTime: "10 min read",
      category: "Market Analysis",
      image: logoPng
    },
    {
      id: 3,
      slug: 'understanding-forex-market-sentiment',
      title: "Understanding Forex Market Sentiment: A Complete Guide",
      excerpt: "Learn how to analyze and interpret market sentiment to make better trading decisions in the forex market using advanced tools and techniques.",
      author: "FXSentinel Team",
      date: "August 10, 2025",
      readTime: "12 min read",
      category: "Trading Education",
      image: logoPng
    },
    {
      id: 4,
      slug: 'turning-news-actionable-signals',
      title: "Turning News into Actionable Signals",
      excerpt: "Master the art of converting breaking news and economic events into profitable trading signals with systematic analysis approaches.",
      author: "FXSentinel Team",
      date: "August 8, 2025",
      readTime: "9 min read",
      category: "Trading Education",
      image: logoPng
    },
    {
      id: 5,
      slug: 'traders-guide-decoding-market-volatility',
      title: "A Trader's Guide to Decoding Market Volatility",
      excerpt: "Navigate through market volatility with confidence using proven strategies and tools to identify opportunities during turbulent times.",
      author: "FXSentinel Team",
      date: "August 5, 2025",
      readTime: "11 min read",
      category: "Market Analysis",
      image: logoPng
    },
    {
      id: 6,
      slug: 'ai-detects-hidden-patterns-macroeconomic-news',
      title: "How AI Detects Hidden Patterns in Macroeconomic News",
      excerpt: "Explore the cutting-edge AI technologies that uncover hidden correlations and patterns in economic data for superior trading insights.",
      author: "FXSentinel Team",
      date: "August 3, 2025",
      readTime: "7 min read",
      category: "Technology",
      image: logoPng
    }
  ];

  return (
    <div className="blog-page">
      {/* Navigation */}
      <nav className={`navbar ${isScrolled ? 'navbar-scrolled' : ''}`}>
        <div className="nav-container">
          <div className="nav-logo">
            <Link to="/">
              <picture>
                <source srcSet={logoWebp} type="image/webp" />
                <img 
                  src={logoPng} 
                  alt="FXSentinel Logo" 
                  className="logo"
                  style={{ height: '50px', width: 'auto' }}
                />
              </picture>
            </Link>
          </div>
          
          {/* Desktop Navigation Links */}
          <div className="nav-links desktop-only">
            <Link to="/#features" className="nav-link-button">Features</Link>
            <Link to="/#about" className="nav-link-button">About</Link>
            <Link to="/#pricing" className="nav-link-button">Pricing</Link>
            <Link to="/#faq" className="nav-link-button">FAQ</Link>
            <span className="nav-link-button active">Blog</span>
            <Link to="/#contact" className="nav-link-button">Contact</Link>
          </div>
          
          {/* Desktop Auth Buttons */}
          <div className="nav-auth desktop-only">
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
            <Link to="/#features" className="mobile-nav-link" onClick={closeMobileMenu}>Features</Link>
            <Link to="/#about" className="mobile-nav-link" onClick={closeMobileMenu}>About</Link>
            <Link to="/#pricing" className="mobile-nav-link" onClick={closeMobileMenu}>Pricing</Link>
            <Link to="/#faq" className="mobile-nav-link" onClick={closeMobileMenu}>FAQ</Link>
            <span className="mobile-nav-link active">Blog</span>
            <Link to="/#contact" className="mobile-nav-link" onClick={closeMobileMenu}>Contact</Link>
          </div>
          <div className="mobile-menu-auth">
            <Link to="/login" className="mobile-login-button" onClick={closeMobileMenu}>Login</Link>
            <Link to="/signup" className="mobile-signup-button" onClick={closeMobileMenu}>Sign Up</Link>
          </div>
        </div>
      </nav>

      {/* Blog Header */}
      <section className="blog-header">
        <div className="blog-header-inner">
          <h1 className="blog-title">FXSentinel Blog</h1>
          <p className="blog-subtitle">
            Expert insights on forex trading, market analysis, and AI-powered trading tools. 
            Learn how to trade economic news, understand market sentiment, and make better trading decisions.
          </p>
        </div>
      </section>

      {/* Blog Content */}
      <section className="blog-content">
        <div className="blog-content-inner">
          <div className="blog-grid">
            {blogPosts.map((post) => (
              <article key={post.id} className="blog-card">
                <Link 
                  to={`/blog/${post.slug}`} 
                  className="blog-card-link"
                  onClick={() => trackBlogPostEngagement(post.slug, 'click', { title: post.title, category: post.category })}
                >
                  <div className="blog-card-image">
                    <img src={post.image} alt={post.title} loading="lazy" />
                    <div className="blog-card-category">{post.category}</div>
                  </div>
                  <div className="blog-card-content">
                    <div className="blog-card-meta">
                      <span className="blog-card-date">{post.date}</span>
                      <span className="blog-card-read-time">{post.readTime}</span>
                    </div>
                    <h2 className="blog-card-title">{post.title}</h2>
                    <p className="blog-card-excerpt">{post.excerpt}</p>
                    <div className="blog-card-author">
                      <span>By {post.author}</span>
                    </div>
                    <span className="blog-card-read-more">Read More</span>
                  </div>
                </Link>
              </article>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
};

export default Blog;
