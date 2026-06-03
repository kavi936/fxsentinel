import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import logoPng from '../assets/fxsentinel_logo_nobg.png';
import logoWebp from '../assets/fxsentinel_logo_nobg.webp';
import analyticsTracker, { trackBlogPostEngagement } from '../utils/analytics';
import { useMeta } from '../hooks/useMeta';
import { blogCrawlerPosts } from '../data/blogCrawlerManifest';
import './Blog.css';

const Blog = () => {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  useMeta(
    'Forex & Macro Education | FXSentinel Blog',
    'In-depth articles on central banks, FX volatility, safe-haven flows, gold and EUR/USD themes, and how AI helps interpret headlines. For retail traders seeking context—not financial advice.'
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

  // Cards from blogCrawlerManifest (same source as crawler static HTML — docs/BLOG_SEO_GEO_WORKFLOW.md)
  const blogPosts = blogCrawlerPosts.map((post) => ({ ...post, image: logoPng }));

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
          <h1 className="blog-title">FXSentinel Blog — macro &amp; FX education</h1>
          <p className="blog-subtitle">
            Long-form guides on central bank policy, cross-border risk, volatility, and how headlines move major pairs and gold.
            We focus on context and mechanics so you can build your own view—FXSentinel is not a broker and does not provide personalised financial advice.
          </p>
          <p className="blog-subtitle blog-subtitle-secondary">
            Browse articles below on geopolitical risk, Fed–ECB divergence, safe havens, institutional flows into digital assets,
            and practical ways to read economic releases alongside an AI-assisted research workflow.
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
