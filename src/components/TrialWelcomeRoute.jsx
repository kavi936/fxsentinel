import React, { useState, useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { config } from '../config';
import TrialWelcome from './TrialWelcome';

const TrialWelcomeRoute = () => {
  const { currentUser } = useAuth();
  const [subscriptionStatus, setSubscriptionStatus] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [hasAccess, setHasAccess] = useState(false);

  // Check if user is developer
  const isDeveloper = currentUser?.email === 'kavi.cf412@gmail.com';

  useEffect(() => {
    const checkAccess = async () => {
      if (!currentUser) {
        setHasAccess(false);
        setIsLoading(false);
        return;
      }

      // Developer accounts always have access
      if (isDeveloper) {
        setHasAccess(true);
        setIsLoading(false);
        return;
      }

      try {
        // Check subscription status
        const response = await fetch(`${config.API_BASE_URL}/api/subscription-status/${currentUser.uid}`);
        if (response.ok) {
          const data = await response.json();
          console.log('🔍 TrialWelcomeRoute - Subscription data:', data);
          setSubscriptionStatus(data);
          
          // Check if user has valid access
          // Only users with 'active' or 'developer' status should bypass trial welcome
          // Users with 'trial' status should see the trial welcome page
          const hasValidAccess = data.status === 'active' || 
                                data.status === 'developer';
          
          console.log('🔍 TrialWelcomeRoute - User status:', data.status, 'Has access:', hasValidAccess);
          setHasAccess(hasValidAccess);
        } else {
          // No subscription found - show trial welcome
          setHasAccess(false);
        }
              } catch (error) {
          console.error('Error checking subscription status:', error);
          
          // If it's a JSON parsing error, the backend might be down
          if (error.message && error.message.includes('Unexpected token')) {
            console.error('❌ Backend server might be down or returning HTML instead of JSON');
            console.error('💡 Please ensure the backend server is running on port 5001');
          }
          
          setHasAccess(false);
        } finally {
          setIsLoading(false);
        }
    };

    checkAccess();
  }, [currentUser, isDeveloper]);

  // Show loading state
  if (isLoading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        background: 'linear-gradient(135deg, #0f0f0f 0%, #1a0a0a 100%)',
        color: 'white'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{
            width: '40px',
            height: '40px',
            border: '3px solid rgba(255, 68, 68, 0.3)',
            borderTop: '3px solid #ff4444',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto 20px'
          }}></div>
          <p>Checking access...</p>
        </div>
        <style>{`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!currentUser) {
    return <Navigate to="/login" replace />;
  }

  // Redirect to dashboard if user already has access
  if (hasAccess) {
    console.log('🔍 TrialWelcomeRoute - Redirecting to dashboard');
    return <Navigate to="/dashboard" replace />;
  }

  // Show trial welcome if user doesn't have access
  console.log('🔍 TrialWelcomeRoute - Showing trial welcome page');
  return <TrialWelcome />;
};

export default TrialWelcomeRoute;
