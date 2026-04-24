import React, { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { getAdditionalUserInfo } from 'firebase/auth';
import { useMeta } from '../hooks/useMeta';
import './Auth.css';
import logoPng from '../assets/fxsentinel_logo_nobg.png';
import logoWebp from '../assets/fxsentinel_logo_nobg.webp';
import { trackSignupCompletion, trackError, trackEngagement } from '../utils/analytics';
import { isGoogleOAuthBlockedError } from '../utils/browserDetection';
import EmbeddedBrowserWarning from './EmbeddedBrowserWarning';
import { BackgroundBeams } from './BackgroundBeams';
import { getSignupErrorMessage } from '../utils/authErrorMessages';
import {
  getPasswordRuleStatus,
  getPasswordStrengthTier,
  isPasswordCompliant,
  PASSWORD_MIN_LENGTH,
} from '../utils/passwordPolicy';

const Signup = () => {
  useMeta(
    'Create Free Account | FXSentinel',
    'Join FXSentinel for a macro-focused forex workspace: economic calendar, AI news context for majors and gold, and alerts by Telegram or email. Analysis and tools only—we are not a broker.'
  );
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [passwordStrength, setPasswordStrength] = useState('');
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { signup, signInWithGoogle } = useAuth();
  const planPremium = searchParams.get('plan') === 'premium';

  // Track signup page view
  React.useEffect(() => {
    trackEngagement('signup_page_view');
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
    setError(''); // Clear error when user starts typing

    // Live strength + requirement checklist (rules live in ../utils/passwordPolicy.js)
    if (name === 'password') {
      setPasswordStrength(getPasswordStrengthTier(value));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    const normalizedEmail = formData.email.trim().toLowerCase();

    // Track signup attempt
    trackEngagement('signup_form_submit', {
      email: normalizedEmail,
      hasFirstName: !!formData.firstName,
      hasLastName: !!formData.lastName
    });

    // Basic validation
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      trackError('signup_validation_error', { error: 'password_mismatch' });
      setIsLoading(false);
      return;
    }

    if (!isPasswordCompliant(formData.password)) {
      setError(
        `Password must meet every requirement below (at least ${PASSWORD_MIN_LENGTH} characters, upper and lower case, a number, and a special character).`
      );
      trackError('signup_validation_error', { error: 'password_requirements_not_met' });
      setIsLoading(false);
      return;
    }

    try {
      await signup(normalizedEmail, formData.password, formData.firstName, formData.lastName);
      trackSignupCompletion('email', {
        email: normalizedEmail,
        hasFirstName: !!formData.firstName,
        hasLastName: !!formData.lastName
      });
      navigate(planPremium ? '/auth-redirect?plan=premium' : '/auth-redirect');
    } catch (err) {
      setError(getSignupErrorMessage(err));
      trackError('signup_failure', { 
        error: err.message || 'unknown_error',
        code: err.code || 'unknown',
        email: normalizedEmail
      });
    } finally {
      setIsLoading(false);
    }
  };

  const passwordRuleRows = (() => {
    const rules = getPasswordRuleStatus(formData.password);
    return [
      { key: 'minLength', met: rules.minLength, label: `At least ${PASSWORD_MIN_LENGTH} characters` },
      { key: 'hasUpper', met: rules.hasUpper, label: 'One uppercase letter' },
      { key: 'hasLower', met: rules.hasLower, label: 'One lowercase letter' },
      { key: 'hasDigit', met: rules.hasDigit, label: 'One number' },
      {
        key: 'hasSpecial',
        met: rules.hasSpecial,
        label: 'One symbol (!@#$…)',
      },
    ];
  })();

  const handleGoogleSignIn = async () => {
    try {
      setError('');
      setIsLoading(true);
      
      // Sign in with Google (popup method)
      const result = await signInWithGoogle();
      
      // Track conversion only for new signups (not returning logins)
      // Firebase v9+ requires getAdditionalUserInfo() to access isNewUser
      const additionalUserInfo = getAdditionalUserInfo(result);
      const isNewUser = additionalUserInfo?.isNewUser || 
        (result?.user?.metadata?.creationTime === result?.user?.metadata?.lastSignInTime);
      
      if (result?.user && isNewUser) {
        trackSignupCompletion('google', {
          email: result.user.email,
          provider: 'google.com',
          displayName: result.user.displayName
        });
      }
      navigate(planPremium ? '/auth-redirect?plan=premium' : '/auth-redirect');
    } catch (err) {
      // Check if this is the Google OAuth blocked error
      if (err.code === 'auth/embedded-browser-blocked' || isGoogleOAuthBlockedError(err)) {
        const errorMessage = err.message || 'Google sign-in is not available in this browser. Please open this link in Safari or Chrome.';
        setError(errorMessage);
        trackError('google_signup_failure_embedded_browser', {
          error: err.code || 'embedded-browser-blocked',
          browserInfo: err.browserInfo || 'unknown',
        });
      } else if (err.code === 'auth/popup-blocked') {
        setError('Sign-in popup was blocked. Please allow popups for this site and try again.');
        trackError('google_signup_failure_popup_blocked', { code: err.code });
      } else if (err.code === 'auth/popup-closed-by-user') {
        setError('Sign-in was cancelled. Please try again if you want to continue with Google.');
        trackError('google_signup_failure_popup_closed', { code: err.code });
      } else if (err.code === 'auth/account-exists-with-different-credential') {
        setError('An account with this email already exists using a different sign-in method. Try signing in with email/password first.');
        trackError('google_signup_failure_account_exists_different_credential', { code: err.code });
      } else {
        setError('Failed to sign in with Google. Please try again.');
        trackError('google_signup_failure', {
          error: err.message || 'unknown_error',
          code: err.code || 'unknown',
        });
      }
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
      
      <div className={`auth-card${showForm ? ' auth-card--signup-form' : ''}`}>
        <div className="auth-header">
          {showForm && (
            <button 
              className="auth-back-button"
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                setError('');
                setShowForm(false);
              }}
              type="button"
            >
              ← Back
            </button>
          )}
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
          <h1>Create Your Account</h1>
          <p>{showForm ? 'Fill in your details to get started' : 'Join FXSentinel and start trading smarter'}</p>
        </div>

        {/* Initial Options View */}
        {!showForm && (
          <>
            {error && (
              <div className="auth-error">
                <span className="error-icon">⚠️</span>
                {error}
              </div>
            )}

            <button 
              className={`auth-social-button ${isLoading ? 'loading' : ''}`}
              onClick={handleGoogleSignIn}
              disabled={isLoading}
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

            <div className="auth-divider">
              <span>or</span>
            </div>

            <button 
              className="auth-button"
              onClick={() => {
                setError('');
                setShowForm(true);
              }}
              type="button"
            >
              Create account with email & password
            </button>

            <div className="auth-footer">
              <p>
                Already have an account?{' '}
                <Link to="/login" className="auth-link">
                  Sign in
                </Link>
              </p>
            </div>
          </>
        )}

        {/* Form View */}
        {showForm && (
          <>
            <form onSubmit={handleSubmit} className="auth-form">
              {error && (
                <div className="auth-error">
                  <span className="error-icon">⚠️</span>
                  {error}
                </div>
              )}

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="firstName">First Name</label>
                  <input
                    type="text"
                    id="firstName"
                    name="firstName"
                    value={formData.firstName}
                    onChange={handleChange}
                    placeholder="Enter your first name"
                    required
                    className="auth-input"
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="lastName">Last Name</label>
                  <input
                    type="text"
                    id="lastName"
                    name="lastName"
                    value={formData.lastName}
                    onChange={handleChange}
                    placeholder="Enter your last name"
                    required
                    className="auth-input"
                  />
                </div>
              </div>

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
                <span className="auth-hint">
                  We&apos;ll send a verification link to this address
                </span>
              </div>

              <div className="form-group">
                <label htmlFor="password">Password</label>
                <input
                  type="password"
                  id="password"
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  placeholder="Create a strong password"
                  required
                  className="auth-input"
                  autoComplete="new-password"
                />
                {passwordStrength && (
                  <div className={`password-strength ${passwordStrength}`}>
                    Password strength: {passwordStrength}
                  </div>
                )}
                <ul className="password-requirements" aria-label="Password requirements">
                  {passwordRuleRows.map(({ key, met, label }) => (
                    <li key={key} className={`password-requirement ${met ? 'met' : 'unmet'}`}>
                      <span className="password-requirement-icon" aria-hidden="true">
                        {met ? '✓' : '○'}
                      </span>
                      {label}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="form-group">
                <label htmlFor="confirmPassword">Confirm Password</label>
                <input
                  type="password"
                  id="confirmPassword"
                  name="confirmPassword"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  placeholder="Confirm your password"
                  required
                  className="auth-input"
                />
              </div>

              <div className="form-options">
                <label className="checkbox-container">
                  <input type="checkbox" required />
                  <span className="checkmark"></span>
                  I agree to the{' '}
                  <Link to="/terms" className="auth-link">
                    Terms of Service
                  </Link>{' '}
                  and{' '}
                  <Link to="/privacy" className="auth-link">
                    Privacy Policy
                  </Link>
                </label>
              </div>

              <button 
                type="submit" 
                className={`auth-button ${isLoading ? 'loading' : ''}`}
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <span className="spinner"></span>
                    Creating account...
                  </>
                ) : (
                  'Create Account'
                )}
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  );
};

export default Signup; 