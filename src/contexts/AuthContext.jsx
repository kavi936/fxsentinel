import React, { createContext, useContext, useState, useEffect } from 'react';
import { auth } from '../config/firebase';
import { config } from '../config';
import { 
  createUserWithEmailAndPassword, 
  signInWithEmailAndPassword, 
  signOut, 
  onAuthStateChanged,
  GoogleAuthProvider,
  signInWithPopup,
  updateProfile,
  sendPasswordResetEmail,
  fetchSignInMethodsForEmail
} from 'firebase/auth';
import { isGoogleOAuthBlockedError, detectEmbeddedBrowser } from '../utils/browserDetection';

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

  // Send branded verification email via backend (Resend + Firebase Admin link generation)
  const sendVerificationEmailViaBackend = async (user) => {
    const token = await user.getIdToken();
    const res = await fetch(`${config.API_BASE_URL}/api/send-verification-email`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      }
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const msg = data?.message || data?.error || `Request failed (${res.status})`;
      throw new Error(msg);
    }
    return data;
  };

  // Request welcome email for any signed-in user (Google or email/password). Backend sends only once per user on first dashboard visit.
  const requestWelcomeEmail = async () => {
    const user = auth.currentUser;
    if (!user) return;
    try {
      const token = await user.getIdToken();
      await fetch(`${config.API_BASE_URL}/api/send-welcome-email`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      });
    } catch (err) {
      console.warn('Welcome email request failed (non-blocking):', err);
    }
  };

  // Sign up function (email/password only; Google accounts are already verified by the provider)
  const signup = async (email, password, firstName, lastName) => {
    try {
      const result = await createUserWithEmailAndPassword(auth, email, password);
      await updateProfile(result.user, {
        displayName: `${firstName} ${lastName}`
      });
      // Send branded verification email via backend (Resend) instead of Firebase's plain email
      await sendVerificationEmailViaBackend(result.user);

      // Welcome email is sent when they first land on /dashboard (not here)

      // Check developer status after signup
      await checkDeveloperStatus(result.user);

      return result;
    } catch (error) {
      // Enrich duplicate-email errors so UI can suggest the correct sign-in method.
      if (error?.code === 'auth/email-already-in-use' && email) {
        try {
          error.signInMethods = await fetchSignInMethodsForEmail(auth, email);
        } catch (lookupError) {
          console.warn('Could not fetch sign-in methods for duplicate email:', lookupError);
        }
      }
      throw error;
    }
  };

  // Resend verification email (for VerifyEmail page; uses backend, rate-limited to 3/min)
  const resendVerificationEmail = async () => {
    const user = auth.currentUser;
    if (!user) throw new Error('Not signed in');
    return sendVerificationEmailViaBackend(user);
  };

  // Reload current user from Firebase (updates emailVerified after they click the link)
  const reloadUser = async () => {
    const user = auth.currentUser;
    if (!user) return null;
    await user.reload();
    // Must keep the real Firebase User instance — spreading loses getIdToken and other methods.
    setCurrentUser(auth.currentUser);
    return auth.currentUser;
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

  // Google sign in
  const signInWithGoogle = async () => {
    try {
      // Check if we're in an embedded browser before attempting sign-in
      const browserInfo = detectEmbeddedBrowser();
      if (browserInfo.isEmbedded) {
        // Create a custom error with helpful information
        const embeddedBrowserError = new Error(
          `Google sign-in is not available in ${browserInfo.browserName}. ${browserInfo.instructions || 'Please open this link in Safari or Chrome.'}`
        );
        embeddedBrowserError.code = 'auth/embedded-browser-blocked';
        embeddedBrowserError.browserInfo = browserInfo;
        throw embeddedBrowserError;
      }

      const provider = new GoogleAuthProvider();
      const result = await signInWithPopup(auth, provider);
      
      // Check developer status after Google sign in
      await checkDeveloperStatus(result.user);
      
      return result;
    } catch (error) {
      // Check if this is the Google OAuth blocked error
      if (isGoogleOAuthBlockedError(error)) {
        const browserInfo = detectEmbeddedBrowser();
        // Enhance the error with helpful information
        const enhancedError = new Error(
          `Google sign-in is blocked in this browser. ${browserInfo.isEmbedded ? browserInfo.instructions : 'Please try opening this link in Safari or Chrome instead.'}`
        );
        enhancedError.code = error.code || 'auth/google-oauth-blocked';
        enhancedError.originalError = error;
        enhancedError.browserInfo = browserInfo;
        throw enhancedError;
      }
      throw error;
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
    const unsubscribe = onAuthStateChanged(auth, async (user) => {
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
    updateUserProfile,
    resendVerificationEmail,
    reloadUser,
    requestWelcomeEmail
  };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
}; 