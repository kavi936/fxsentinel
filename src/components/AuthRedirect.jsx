import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const AuthRedirect = () => {
  const { currentUser, isDeveloper, hasCheckedDeveloperStatus } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    console.log('🔍 AuthRedirect Debug:', {
      currentUser: currentUser ? { uid: currentUser.uid, email: currentUser.email } : null,
      isDeveloper,
      hasCheckedDeveloperStatus
    });

    if (!hasCheckedDeveloperStatus) {
      console.log('⏳ Still checking developer status...');
      return; // Still checking developer status
    }

    if (!currentUser) {
      console.log('❌ No current user, redirecting to login');
      navigate('/login');
      return;
    }

    // If user is a developer, go directly to dashboard
    if (isDeveloper) {
      console.log('🔧 Developer detected, bypassing trial welcome');
      navigate('/dashboard');
      return;
    }

    // For regular users, go to trial welcome
    console.log('👤 Regular user, showing trial welcome');
    navigate('/trial-welcome');
  }, [currentUser, isDeveloper, hasCheckedDeveloperStatus, navigate]);

  // Show loading while checking developer status
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

  return null;
};

export default AuthRedirect;
