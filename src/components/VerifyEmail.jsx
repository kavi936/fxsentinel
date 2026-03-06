import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useMeta } from '../hooks/useMeta';
import './Auth.css';
import logoPng from '../assets/fxsentinel_logo_nobg.png';
import logoWebp from '../assets/fxsentinel_logo_nobg.webp';

/**
 * Shown after email/password signup until the user verifies their email.
 * When they click the link in the email, Firebase redirects here (our branded page).
 * Google signups skip this (provider already verifies).
 */
const VerifyEmail = () => {
  useMeta('Verify your email - FXSentinel', 'Check your inbox to verify your email and access your FXSentinel account.');
  const { currentUser, resendVerificationEmail, reloadUser } = useAuth();
  const navigate = useNavigate();
  const [resendStatus, setResendStatus] = useState('idle');
  const [resendError, setResendError] = useState('');
  const [checkingVerified, setCheckingVerified] = useState(false);
  const [showVerifiedSuccess, setShowVerifiedSuccess] = useState(false);
  const redirectedRef = useRef(false);

  const isEmailProvider = currentUser?.providerData?.[0]?.providerId === 'password';
  const needsVerification = isEmailProvider && currentUser && !currentUser.emailVerified;
  const isVerifiedAndSignedIn = currentUser && !needsVerification;

  // Verified and signed in (same session): show branded success then redirect to dashboard
  useEffect(() => {
    if (!isVerifiedAndSignedIn || redirectedRef.current) return;
    setShowVerifiedSuccess(true);
    redirectedRef.current = true;
    const t = setTimeout(() => navigate('/auth-redirect', { replace: true }), 2200);
    return () => clearTimeout(t);
  }, [isVerifiedAndSignedIn, navigate]);

  const handleResend = async () => {
    setResendError('');
    setResendStatus('sending');
    try {
      await resendVerificationEmail();
      setResendStatus('sent');
      // Cooldown: Firebase rate-limits; hide "Resend" for 60s to avoid spam
      setTimeout(() => setResendStatus('idle'), 60000);
    } catch (err) {
      setResendError(err.message || 'Failed to resend. Try again later.');
      setResendStatus('error');
      setTimeout(() => setResendStatus('idle'), 5000);
    }
  };

  const handleCheckVerified = async () => {
    setCheckingVerified(true);
    setResendError('');
    try {
      const updated = await reloadUser();
      if (updated?.emailVerified) {
        navigate('/auth-redirect', { replace: true });
        return;
      }
      setResendError('Not verified yet. Click the link in the email we sent you, then try again.');
    } catch (err) {
      setResendError(err.message || 'Could not refresh. Try again.');
    } finally {
      setCheckingVerified(false);
    }
  };

  // Branded success: just verified (same session) – show message then redirect
  if (showVerifiedSuccess && currentUser) {
    return (
      <div className="auth-container">
        <div className="auth-background" />
        <div className="auth-card auth-card--success">
          <div className="auth-header">
            <Link to="/" className="auth-logo">
              <picture>
                <source srcSet={logoWebp} type="image/webp" />
                <img src={logoPng} alt="FXSentinel Logo" style={{ height: '40px', width: 'auto' }} />
              </picture>
            </Link>
            <div className="verify-success-icon">✓</div>
            <h1>Email verified</h1>
            <p style={{ color: 'rgba(255,255,255,0.9)', marginBottom: '1rem' }}>
              Taking you to your dashboard...
            </p>
            <div className="spinner" style={{ margin: '0 auto' }} />
          </div>
        </div>
      </div>
    );
  }

  // No session: they landed from the link in another device/tab – branded "Sign in to continue"
  if (!currentUser) {
    return (
      <div className="auth-container">
        <div className="auth-background" />
        <div className="auth-card auth-card--success">
          <div className="auth-header">
            <Link to="/" className="auth-logo">
              <picture>
                <source srcSet={logoWebp} type="image/webp" />
                <img src={logoPng} alt="FXSentinel Logo" style={{ height: '40px', width: 'auto' }} />
              </picture>
            </Link>
            <div className="verify-success-icon">✓</div>
            <h1>Email verified</h1>
            <p style={{ color: 'rgba(255,255,255,0.9)', marginBottom: '1.5rem' }}>
              Your email is confirmed. Sign in to access your FXSentinel account.
            </p>
            <Link to="/login" className="auth-button" style={{ display: 'inline-block', textAlign: 'center', textDecoration: 'none' }}>
              Sign in
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // Still loading (auth resolving)
  if (!needsVerification) {
    return (
      <div className="auth-container">
        <div className="auth-background" />
        <div className="auth-card" style={{ textAlign: 'center' }}>
          <div className="spinner" style={{ margin: '0 auto 1rem' }} />
          <p>Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-container">
      <div className="auth-background" />
      <div className="auth-card">
        <div className="auth-header">
          <Link to="/" className="auth-logo">
            <picture>
              <source srcSet={logoWebp} type="image/webp" />
              <img src={logoPng} alt="FXSentinel Logo" style={{ height: '40px', width: 'auto' }} />
            </picture>
          </Link>
          <h1>Verify your email</h1>
          <p>We sent a verification link to <strong>{currentUser.email}</strong></p>
        </div>

        <div className="auth-form" style={{ gap: '1rem' }}>
          <p style={{ color: 'rgba(255,255,255,0.8)', fontSize: '0.95rem', margin: 0 }}>
            Click the link in that email to verify your account. If you don&apos;t see it, check your spam folder.
          </p>

          {resendError && (
            <div className="auth-error">
              <span className="error-icon">⚠️</span>
              {resendError}
            </div>
          )}

          <button
            type="button"
            className="auth-button"
            onClick={handleCheckVerified}
            disabled={checkingVerified}
          >
            {checkingVerified ? (
              <>
                <span className="spinner" />
                Checking...
              </>
            ) : (
              "I've verified my email"
            )}
          </button>

          <div style={{ marginTop: '0.5rem' }}>
            {resendStatus === 'sent' ? (
              <p style={{ color: 'rgba(76, 175, 80, 0.9)', fontSize: '0.9rem' }}>
                New email sent. Check your inbox (and spam).
              </p>
            ) : (
              <button
                type="button"
                className="auth-link"
                onClick={handleResend}
                disabled={resendStatus === 'sending'}
                style={{
                  background: 'none',
                  border: 'none',
                  padding: 0,
                  cursor: resendStatus === 'sending' ? 'not-allowed' : 'pointer',
                  fontSize: 'inherit',
                  textDecoration: 'underline'
                }}
              >
                {resendStatus === 'sending' ? 'Sending...' : "Resend verification email"}
              </button>
            )}
          </div>

          <div className="auth-footer" style={{ marginTop: '1rem' }}>
            <p>
              <Link to="/login" className="auth-link">Sign in</Link> with a different account
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VerifyEmail;
