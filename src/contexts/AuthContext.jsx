import React, { createContext, useContext, useState, useEffect, useRef } from 'react';
import { auth } from '../config/firebase';
import { config } from '../config';
import { 
  createUserWithEmailAndPassword, 
  signInWithEmailAndPassword, 
  signOut, 
  onAuthStateChanged,
  GoogleAuthProvider,
  signInWithPopup,
  signInWithRedirect,
  getRedirectResult,
  updateProfile,
  sendPasswordResetEmail
} from 'firebase/auth';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isDeveloper, setIsDeveloper] = useState(false);
  const [hasCheckedDeveloperStatus, setHasCheckedDeveloperStatus] = useState(false);
  const isProcessingRedirectRef = useRef(false);

  // Check if user is a developer
  const checkDeveloperStatus = async (user) => {
    console.log('🔍 Checking developer status for:', user ? user.email : 'no user');
    
    if (!user || !user.email) {
      console.log('❌ No user or email, setting developer to false');
      setIsDeveloper(false);
      setHasCheckedDeveloperStatus(true);
      return;
    }

    try {
      console.log('🌐 Making API request to check developer status...');
      const response = await fetch(`${config.API_BASE_URL}/api/subscription-status/${user.uid}?email=${user.email}`);
      console.log('📡 API Response status:', response.status);
      
      if (response.ok) {
        const data = await response.json();
        console.log('📊 API Response data:', data);
        // Handle null response gracefully - check if data exists before accessing properties
        if (data && typeof data === 'object') {
          const isDev = data.is_developer || false;
          console.log('🔧 Setting developer status to:', isDev);
          setIsDeveloper(isDev);
        } else {
          console.log('⚠️ Invalid response data, setting developer to false');
          setIsDeveloper(false);
        }
      } else {
        console.log('❌ API request failed, setting developer to false');
        setIsDeveloper(false);
      }
    } catch (error) {
      console.error('❌ Error checking developer status:', error);
      
      // If it's a JSON parsing error, the backend might be down
      if (error.message && error.message.includes('Unexpected token')) {
        console.error('❌ Backend server might be down or returning HTML instead of JSON');
        console.error('💡 Please ensure the backend server is running on port 5001');
      }
      
      setIsDeveloper(false);
    } finally {
      console.log('✅ Developer status check completed');
      setHasCheckedDeveloperStatus(true);
    }
  };

  // Sign up function
  const signup = async (email, password, firstName, lastName) => {
    try {
      const result = await createUserWithEmailAndPassword(auth, email, password);
      await updateProfile(result.user, {
        displayName: `${firstName} ${lastName}`
      });
      
      // Check developer status after signup
      await checkDeveloperStatus(result.user);
      
      return result;
    } catch (error) {
      throw error;
    }
  };

  // Login function
  const login = async (email, password) => {
    try {
      const result = await signInWithEmailAndPassword(auth, email, password);
      
      // Check developer status after login
      await checkDeveloperStatus(result.user);
      
      return result;
    } catch (error) {
      throw error;
    }
  };

  // Logout function
  const logout = async () => {
    try {
      setIsDeveloper(false);
      setHasCheckedDeveloperStatus(false);
      return await signOut(auth);
    } catch (error) {
      throw error;
    }
  };

  // Google sign in with popup fallback to redirect
  const signInWithGoogle = async () => {
    try {
      const provider = new GoogleAuthProvider();
      
      // Add custom parameters for better UX
      provider.setCustomParameters({
        prompt: 'select_account'
      });
      
      // Try popup first (better UX)
      try {
        const result = await signInWithPopup(auth, provider);
        console.log('✅ Google sign-in successful via popup');
        
        // Check developer status after Google sign in
        await checkDeveloperStatus(result.user);
        
        return result;
      } catch (popupError) {
        // Check if popup was blocked or closed
        if (popupError.code === 'auth/popup-blocked' || 
            popupError.code === 'auth/popup-closed-by-user' ||
            popupError.message?.includes('popup') ||
            popupError.message?.includes('blocked')) {
          console.warn('⚠️ Popup blocked or closed, falling back to redirect:', popupError.code);
          
          // Fallback to redirect method
          await signInWithRedirect(auth, provider);
          // Note: signInWithRedirect doesn't return a result immediately
          // The result will be handled by getRedirectResult in useEffect
          return null;
        } else {
          // Other errors, re-throw
          console.error('❌ Google sign-in error:', popupError.code, popupError.message);
          throw popupError;
        }
      }
    } catch (error) {
      // Log detailed error information
      console.error('❌ Google sign-in failed:', {
        code: error.code,
        message: error.message,
        email: error.email,
        credential: error.credential
      });
      
      // Provide more specific error messages
      let errorMessage = 'Failed to sign in with Google. Please try again.';
      
      if (error.code === 'auth/popup-blocked') {
        errorMessage = 'Popup was blocked. Please allow popups for this site and try again, or use email/password sign-in.';
      } else if (error.code === 'auth/popup-closed-by-user') {
        errorMessage = 'Sign-in was cancelled. Please try again.';
      } else if (error.code === 'auth/network-request-failed') {
        errorMessage = 'Network error. Please check your internet connection and try again.';
      } else if (error.code === 'auth/unauthorized-domain') {
        errorMessage = 'This domain is not authorized. Please contact support.';
      } else if (error.code === 'auth/operation-not-allowed') {
        errorMessage = 'Google sign-in is not enabled. Please contact support.';
      } else if (error.message) {
        errorMessage = `Sign-in failed: ${error.message}`;
      }
      
      // Create a new error with the user-friendly message
      const userFriendlyError = new Error(errorMessage);
      userFriendlyError.code = error.code;
      userFriendlyError.originalError = error;
      throw userFriendlyError;
    }
  };

  // Password reset function
  const resetPassword = async (email) => {
    try {
      return await sendPasswordResetEmail(auth, email);
    } catch (error) {
      throw error;
    }
  };

  // Update profile function
  const updateUserProfile = async (updates) => {
    try {
      return await updateProfile(auth.currentUser, updates);
    } catch (error) {
      throw error;
    }
  };

  useEffect(() => {
    // Handle redirect result from Google sign-in
    const handleRedirectResult = async () => {
      try {
        isProcessingRedirectRef.current = true;
        const result = await getRedirectResult(auth);
        if (result) {
          console.log('✅ Google sign-in successful via redirect');
          setCurrentUser(result.user);
          // Check developer status after redirect sign-in
          await checkDeveloperStatus(result.user);
        }
      } catch (error) {
        console.error('❌ Error handling redirect result:', error);
        // Don't set error state here, let onAuthStateChanged handle it
      } finally {
        isProcessingRedirectRef.current = false;
        setLoading(false);
      }
    };

    // Check for redirect result first
    handleRedirectResult();

    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      // Skip if we're already processing redirect result
      if (isProcessingRedirectRef.current) {
        return;
      }
      
      setCurrentUser(user);
      if (user) {
        await checkDeveloperStatus(user);
      } else {
        setIsDeveloper(false);
        setHasCheckedDeveloperStatus(true);
      }
      setLoading(false);
    });

    return () => unsubscribe();
  }, []);

  const value = {
    currentUser,
    isDeveloper,
    hasCheckedDeveloperStatus,
    signup,
    login,
    logout,
    signInWithGoogle,
    resetPassword,
    updateUserProfile
  };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
}; 