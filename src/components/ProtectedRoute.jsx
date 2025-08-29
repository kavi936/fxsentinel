import React, { useState, useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { config } from '../config';

const ProtectedRoute = ({ children }) => {
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
        const response = await fetch(`${config.API_BASE_URL}/api/subscription-status/${currentUser.uid}?email=${encodeURIComponent(currentUser.email)}`);
        if (response.ok) {
          const data = await response.json();
          setSubscriptionStatus(data);
          
          // Check if user has valid access
          const hasValidAccess = data.status === 'trial' || 
                                data.status === 'active' || 
                                data.status === 'developer' ||
                                data.status === 'beta_tester';
          
          setHasAccess(hasValidAccess);
        } else {
          // No subscription found - redirect to trial welcome
          setHasAccess(false);
        }
      } catch (error) {
        console.error('Error checking subscription status:', error);
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

  // Redirect to trial welcome if no valid subscription
  if (!hasAccess) {
    return <Navigate to="/trial-welcome" replace />;
  }

  return children;
};

export default ProtectedRoute; 