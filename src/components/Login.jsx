import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useMeta } from '../hooks/useMeta';
import './Auth.css';
import logoPng from '../assets/fxsentinel_logo_nobg.png';
import logoWebp from '../assets/fxsentinel_logo_nobg.webp';
import { isGoogleOAuthBlockedError } from '../utils/browserDetection';
import EmbeddedBrowserWarning from './EmbeddedBrowserWarning';
import { BackgroundBeams } from './BackgroundBeams';
import { getLoginErrorMessage } from '../utils/authErrorMessages';

const Login = () => {
  useMeta(
    'Sign In to Your Account | FXSentinel',
    'Secure sign-in for returning FXSentinel members: your economic calendar, AI news breakdowns, alert settings, and Telegram notifications. New? Create a free account to start.'
  );
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const { login, signInWithGoogle } = useAuth();

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
    setError(''); // Clear error when user starts typing
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    const normalizedEmail = formData.email.trim().toLowerCase();

    try {
      await login(normalizedEmail, formData.password);
      navigate('/auth-redirect');
    } catch (err) {
      setError(getLoginErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <EmbeddedBrowserWarning />
      <div className="auth-background">
        <BackgroundBeams />
      </div>

      <div className="auth-main-stack">
      <div className="auth-card">
        <div className="auth-header">
          <Link to="/" className="auth-logo">
            <picture>
              <source srcSet={logoWebp} type="image/webp" />
              <img 
                src={logoPng} 
                alt="FXSentinel Logo"
                style={{ height: '40px', width: 'auto' }}
              />
            </picture>
          </Link>
          <h1>Sign in to FXSentinel</h1>
          <p>Welcome back—access your macro dashboard, alerts, and AI-assisted news context.</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          {error && (
            <div className="auth-error">
              <span className="error-icon">⚠️</span>
              {error}
            </div>
          )}

          <div className="form-group">
            <label htmlFor="email">Email Address</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="Enter your email"
              required
              className="auth-input"
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="Enter your password"
              required
              className="auth-input"
            />
          </div>

          <div className="form-options">
            <label className="checkbox-container">
              <input type="checkbox" />
              <span className="checkmark"></span>
              Remember me
            </label>
            <Link to="/forgot-password" className="forgot-password">
              Forgot password?
            </Link>
          </div>

          <button 
            type="submit" 
            className={`auth-button ${isLoading ? 'loading' : ''}`}
            disabled={isLoading}
          >
            {isLoading ? (
              <span className="spinner" aria-label="Signing in" />
            ) : (
              'Sign In'
            )}
          </button>
        </form>

        <div className="auth-divider">
          <span>or</span>
        </div>

        <button 
          className="auth-social-button"
          onClick={async () => {
            setIsLoading(true);
            setError('');
            try {
              await signInWithGoogle();
              navigate('/auth-redirect');
            } catch (err) {
              if (err.code === 'auth/embedded-browser-blocked' || isGoogleOAuthBlockedError(err)) {
                const errorMessage = err.message || 'Google sign-in is not available in this browser. Please open this link in Safari or Chrome.';
                setError(errorMessage);
              } else if (err.code === 'auth/popup-blocked') {
                setError('Sign-in popup was blocked. Please allow popups for this site and try again.');
              } else if (err.code === 'auth/popup-closed-by-user') {
                setError('Sign-in was cancelled. Please try again if you want to continue with Google.');
              } else if (err.code === 'auth/account-exists-with-different-credential') {
                setError('An account with this email already exists using a different sign-in method. Try your email/password instead.');
              } else {
                setError('Failed to sign in with Google. Please try again.');
              }
            } finally {
              setIsLoading(false);
            }
          }}
        >
          {isLoading ? (
            <span className="spinner" aria-label="Signing in with Google" />
          ) : (
            <>
              <img src="https://www.google.com/favicon.ico" alt="Google" />
              Continue with Google
            </>
          )}
        </button>

        <div className="auth-footer">
          <p>
            Don't have an account?{' '}
            <Link to="/signup" className="auth-link">
              Sign up for free
            </Link>
          </p>
        </div>
      </div>

      <section
        className="auth-page-copy--seo-only"
        aria-hidden="true"
      >
        <h2>About your FXSentinel account</h2>
        <p>
          Signing in connects you to the same macro toolkit described on our homepage: a live economic calendar,
          AI-generated context on market-moving headlines, optional Telegram notifications, and dashboards built for
          fundamentals-first research rather than price-only charts.
        </p>
        <p>
          FXSentinel does not execute trades, hold client funds, or sell trade-by-trade instructions.
          We provide software, alerts, and educational analysis so you can make your own decisions. If you are new,
          create an account from the sign-up page to explore the free tier before upgrading.
        </p>
      </section>
      </div>
    </div>
  );
};

export default Login; 