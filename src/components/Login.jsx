import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useMeta } from '../hooks/useMeta';
import './Auth.css';
import logoPng from '../assets/fxsentinel_logo_nobg.png';
import logoWebp from '../assets/fxsentinel_logo_nobg.webp';
import { isGoogleOAuthBlockedError } from '../utils/browserDetection';
import EmbeddedBrowserWarning from './EmbeddedBrowserWarning';

const Login = () => {
  useMeta('Login - FXSentinel', 'Sign in to your FXSentinel account to access your dashboard, alerts, and AI-powered market analysis.');
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

    try {
      await login(formData.email, formData.password);
      navigate('/auth-redirect');
    } catch (err) {
      setError('Invalid email or password. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <EmbeddedBrowserWarning />
      <div className="auth-background">
        {/* Data stream background effect */}
      </div>
      
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
          <h1>Welcome Back</h1>
          <p>Sign in to your FXSentinel account</p>
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
              <>
                <span className="spinner"></span>
                Signing in...
              </>
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
              } else {
                setError('Failed to sign in with Google. Please try again.');
              }
            } finally {
              setIsLoading(false);
            }
          }}
        >
          {isLoading ? (
            <>
              <span className="spinner"></span>
              Signing in...
            </>
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
    </div>
  );
};

export default Login; 