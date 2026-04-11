import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { config } from '../config';

/**
 * After auth, users with no completed/skipped onboarding must see the survey first.
 * Stripe checkout returns to /dashboard — this gate redirects them to /onboarding-survey when needed.
 */
const TraderProfileGate = ({ children }) => {
  const { currentUser } = useAuth();
  const navigate = useNavigate();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!currentUser) {
      setReady(false);
      return;
    }

    let cancelled = false;

    (async () => {
      try {
        const token = await currentUser.getIdToken();
        const res = await fetch(`${config.API_BASE_URL}/api/user/trader-profile`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        const data = await res.json().catch(() => ({}));
        if (cancelled) return;
        // Match OnboardingSurvey: only treat explicit true as "must complete survey"
        if (data.needs_survey === true) {
          navigate('/onboarding-survey', { replace: true });
          return;
        }
      } catch (e) {
        console.warn('Trader profile gate:', e);
      }
      if (!cancelled) setReady(true);
    })();

    return () => {
      cancelled = true;
    };
  }, [currentUser, navigate]);

  if (!currentUser) {
    return null;
  }

  if (!ready) {
    return (
      <div
        style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '100vh',
          flexDirection: 'column',
          gap: '1rem',
          background: 'linear-gradient(135deg, #0f0f0f 0%, #1a0a0a 100%)',
          color: 'white',
        }}
      >
        <div
          style={{
            width: '40px',
            height: '40px',
            border: '3px solid rgba(255, 68, 68, 0.3)',
            borderTop: '3px solid #ff4444',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
          }}
        />
        <p>Loading your workspace…</p>
        <style>{`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }

  return children;
};

export default TraderProfileGate;
