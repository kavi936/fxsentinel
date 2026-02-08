import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { config } from '../config';
import { trackAuthRedirect } from '../utils/analytics';

const AuthRedirect = () => {
  const { currentUser, isDeveloper, hasCheckedDeveloperStatus } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const planPremium = searchParams.get('plan') === 'premium';

  const [checkoutState, setCheckoutState] = useState('idle'); // 'idle' | 'creating' | 'error'
  const [checkoutError, setCheckoutError] = useState(null);

  useEffect(() => {
    console.log('🔍 AuthRedirect Debug:', {
      currentUser: currentUser ? { uid: currentUser.uid, email: currentUser.email } : null,
      isDeveloper,
      hasCheckedDeveloperStatus,
      planPremium
    });

    if (!hasCheckedDeveloperStatus) {
      console.log('⏳ Still checking developer status...');
      return;
    }

    if (!currentUser) {
      console.log('❌ No current user, redirecting to login');
      navigate('/login');
      return;
    }

    const authMethod = currentUser.providerData?.[0]?.providerId === 'google.com' ? 'google' : 'email';
    trackAuthRedirect(authMethod);

    // If user came from "Start Premium", create checkout session and redirect to Stripe
    if (planPremium) {
      setCheckoutState('creating');
      fetch(`${config.API_BASE_URL}/api/create-checkout-session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: currentUser.uid,
          email: currentUser.email,
          name: currentUser.displayName || currentUser.email
        })
      })
        .then(async (res) => {
          const data = await res.json();
          if (res.ok && data.session_url) {
            window.location.href = data.session_url;
            return;
          }
          setCheckoutError(data.error || data.message || 'Could not start checkout');
          setCheckoutState('error');
        })
        .catch((err) => {
          console.error('Checkout session error:', err);
          setCheckoutError(err.message || 'Something went wrong. You can use the dashboard and upgrade later.');
          setCheckoutState('error');
        });
      return;
    }

    if (isDeveloper) {
      console.log('🔧 Developer detected, going to dashboard');
    } else {
      console.log('👤 Free tier user, going to dashboard');
    }
    navigate('/dashboard');
  }, [currentUser, isDeveloper, hasCheckedDeveloperStatus, planPremium, navigate]);

  if (!hasCheckedDeveloperStatus) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        flexDirection: 'column',
        gap: '1rem'
      }}>
        <div className="spinner"></div>
        <p>Checking access...</p>
      </div>
    );
  }

  if (checkoutState === 'creating') {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        flexDirection: 'column',
        gap: '1rem',
        background: 'linear-gradient(135deg, #0f0f0f 0%, #1a0a0a 100%)',
        color: 'white'
      }}>
        <div className="spinner"></div>
        <p>Taking you to checkout...</p>
      </div>
    );
  }

  if (checkoutState === 'error') {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        flexDirection: 'column',
        gap: '1rem',
        background: 'linear-gradient(135deg, #0f0f0f 0%, #1a0a0a 100%)',
        color: 'white',
        padding: '2rem',
        textAlign: 'center'
      }}>
        <p>{checkoutError}</p>
        <button
          type="button"
          onClick={() => navigate('/dashboard')}
          style={{
            padding: '0.75rem 1.5rem',
            background: '#ff4444',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            fontWeight: 600,
            cursor: 'pointer'
          }}
        >
          Go to Dashboard
        </button>
      </div>
    );
  }

  return null;
};

export default AuthRedirect;
