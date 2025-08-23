import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import logoPng from '../assets/fxsentinel_logo_nobg.png';
import logoWebp from '../assets/fxsentinel_logo_nobg.webp';
import './Blog.css';

const Blog = () => {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  useEffect(() => {
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

  // Sample blog posts data
  const blogPosts = [
    {
      id: 1,
      title: "Understanding Forex Market Sentiment: A Complete Guide",
      excerpt: "Learn how to analyze and interpret market sentiment to make better trading decisions in the forex market.",
      author: "FXSentinel Team",
      date: "December 15, 2024",
      readTime: "8 min read",
      category: "Trading Education",
      image: "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=400&h=250&fit=crop"
    },
    {
      id: 2,
      title: "The Impact of Central Bank Decisions on Currency Pairs",
      excerpt: "Explore how central bank policies and interest rate decisions affect currency movements and trading opportunities.",
      author: "FXSentinel Team",
      date: "December 12, 2024",
      readTime: "10 min read",
      category: "Market Analysis",
      image: "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=400&h=250&fit=crop"
    },
    {
      id: 3,
      title: "AI-Powered News Analysis: The Future of Trading",
      excerpt: "Discover how artificial intelligence is revolutionizing the way traders process and react to market news.",
      author: "FXSentinel Team",
      date: "December 10, 2024",
      readTime: "6 min read",
      category: "Technology",
      image: "https://images.unsplash.com/photo-1677442136019-21780ecad995?w=400&h=250&fit=crop"
    },
    {
      id: 4,
      title: "Risk Management Strategies for Forex Traders",
      excerpt: "Essential risk management techniques that every forex trader should implement to protect their capital.",
      author: "FXSentinel Team",
      date: "December 8, 2024",
      readTime: "12 min read",
      category: "Trading Education",
      image: "https://images.unsplash.com/photo-1554224155-6726b3ff858f?w=400&h=250&fit=crop"
    },
    {
      id: 5,
      title: "Economic Indicators Every Trader Should Monitor",
      excerpt: "A comprehensive guide to the key economic indicators that drive currency movements and market volatility.",
      author: "FXSentinel Team",
      date: "December 5, 2024",
      readTime: "9 min read",
      category: "Market Analysis",
      image: "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=400&h=250&fit=crop"
    },
    {
      id: 6,
      title: "Building a Profitable Trading Routine",
      excerpt: "Learn how to develop and maintain a consistent trading routine that leads to long-term success.",
      author: "FXSentinel Team",
      date: "December 3, 2024",
      readTime: "7 min read",
      category: "Trading Education",
      image: "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=400&h=250&fit=crop"
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
        </div>
      </section>

      {/* Blog Content */}
      <section className="blog-content">
        <div className="blog-content-inner">
          <div className="blog-grid">
            {blogPosts.map((post) => (
              <article key={post.id} className="blog-card">
                <div className="blog-card-image">
                  <img src={post.image} alt={post.title} />
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
                  <button className="blog-card-read-more">Read More</button>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* Newsletter Signup */}
      <section className="blog-newsletter">
        <div className="newsletter-inner">
          <h2>Stay Updated</h2>
          <p>Get the latest trading insights and market analysis delivered to your inbox</p>
          <div className="newsletter-form">
            <input 
              type="email" 
              placeholder="Enter your email address" 
              className="newsletter-input"
            />
            <button className="newsletter-button">Subscribe</button>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Blog;
