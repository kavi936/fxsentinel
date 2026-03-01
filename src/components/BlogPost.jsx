import React, { useState, useEffect, useRef } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import logoPng from '../assets/fxsentinel_logo_nobg.png';
import logoWebp from '../assets/fxsentinel_logo_nobg.webp';
import { useMeta } from '../hooks/useMeta';
import './BlogPost.css';

const BASE_URL = 'https://fxsentinel.io';

/** Parse "August 15, 2025" -> "2025-08-15" for schema datePublished */
function parseDateToISO(dateStr) {
  if (!dateStr) return undefined;
  const d = new Date(dateStr);
  return isNaN(d.getTime()) ? undefined : d.toISOString().split('T')[0];
}

const BlogPost = ({ postData }) => {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const schemaScriptId = useRef('blog-posting-schema');

  useMeta(
    postData?.title ? `${postData.title} | FXSentinel Blog` : 'FXSentinel Blog',
    postData?.excerpt ?? undefined
  );

  // Inject BlogPosting JSON-LD for rich results and GEO (one script per post, keyed by headline)
  useEffect(() => {
    if (!postData?.title) return;
    const url = `${BASE_URL}${location.pathname}`;
    const datePublished = parseDateToISO(postData.date);
    const schema = {
      '@context': 'https://schema.org',
      '@type': 'BlogPosting',
      headline: postData.title,
      description: postData.excerpt || postData.title,
      datePublished: datePublished || undefined,
      author: { '@type': 'Organization', name: postData.author || 'FXSentinel Team' },
      mainEntityOfPage: { '@type': 'WebPage', '@id': url },
      url,
      articleSection: postData.category || undefined,
      keywords: ['forex trading', 'economic news', 'AI market analysis', 'FXSentinel', postData.category].filter(Boolean).join(', ')
    };
    let script = document.getElementById(schemaScriptId.current);
    if (script) script.remove();
    script = document.createElement('script');
    script.id = schemaScriptId.current;
    script.type = 'application/ld+json';
    script.textContent = JSON.stringify(schema);
    document.head.appendChild(script);
    return () => {
      const s = document.getElementById(schemaScriptId.current);
      if (s) s.remove();
    };
  }, [postData?.title, postData?.excerpt, postData?.date, postData?.author, postData?.category, location.pathname]);

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

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="blog-post-page">
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
            <Link to="/blog" className="nav-link-button active">Blog</Link>
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
            <Link to="/blog" className="mobile-nav-link active" onClick={closeMobileMenu}>Blog</Link>
            <Link to="/#contact" className="mobile-nav-link" onClick={closeMobileMenu}>Contact</Link>
          </div>
          <div className="mobile-menu-auth">
            <Link to="/login" className="mobile-login-button" onClick={closeMobileMenu}>Login</Link>
            <Link to="/signup" className="mobile-signup-button" onClick={closeMobileMenu}>Sign Up</Link>
          </div>
        </div>
      </nav>

      {/* Blog Post Header */}
      <section className="blog-post-header">
        <div className="blog-post-header-inner">
          <div className="blog-post-meta">
            <span className="blog-post-category">{postData.category}</span>
            <span className="blog-post-date">{postData.date}</span>
            <span className="blog-post-read-time">{postData.readTime}</span>
          </div>
          <h1 className="blog-post-title">{postData.title}</h1>
          <p className="blog-post-excerpt">{postData.excerpt}</p>
          <div className="blog-post-author">
            <span>By {postData.author}</span>
          </div>
        </div>
      </section>

      {/* Blog Post Content */}
      <section className="blog-post-content">
        <div className="blog-post-content-inner">
          <div className="blog-post-body">
            {postData.content}
          </div>
          
          {/* Back to Blog Button */}
          <div className="blog-post-navigation">
            <button onClick={() => navigate('/blog')} className="back-to-blog-button">
              ← Back to Blog
            </button>
          </div>
        </div>
      </section>
    </div>
  );
};

export default BlogPost;
