import React, { useState, useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { config } from '../config';

const ProtectedRoute = ({ children }) => {
  const { currentUser } = useAuth();
  const [subscriptionStatus, setSubscriptionStatus] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [hasAccess, setHasAccess] = useState(false);

  // Check if user is developer (for immediate access, but backend will validate)
  const isDeveloper = currentUser?.email === 'kavi.cf412@gmail.com';

  useEffect(() => {
    const checkAccess = async () => {
      if (!currentUser) {
        setHasAccess(false);
        setIsLoading(false);
        return;
      }

      // Developer accounts get immediate access (backend will validate)
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
          
          // Handle null response gracefully
          if (data && typeof data === 'object' && data.status) {
            setSubscriptionStatus(data);
            
            // Check if user has valid access (freemium model)
            const hasValidAccess = data.status === 'free' || 
                                  data.status === 'premium' || 
                                  data.status === 'developer';
            
            setHasAccess(hasValidAccess);
            
            // Log for debugging
            console.log('🔍 ProtectedRoute - User:', currentUser.email, 'Status:', data.status, 'Access:', hasValidAccess);
          } else {
            // Invalid response - default to free tier access
            console.warn('⚠️ Invalid subscription status response in ProtectedRoute, allowing access');
            setHasAccess(true);  // Allow access, backend will set to free tier
          }
        } else {
          // No subscription found - default to free tier access
          setHasAccess(true);  // Allow access, backend will set to free tier
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

  // Email/password users must verify before accessing protected pages (reduces fake accounts)
  const isEmailProvider = currentUser.providerData?.[0]?.providerId === 'password';
  if (isEmailProvider && !currentUser.emailVerified) {
    return <Navigate to="/verify-email" replace />;
  }

  // Redirect to login if no valid access
  if (!hasAccess) {
    return <Navigate to="/login" replace />;
  }

  return children;
};

export default ProtectedRoute; 