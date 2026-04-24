const sanitizeAuthErrorCode = (code) => (typeof code === 'string' ? code.toLowerCase() : '');

export const getSignupErrorMessage = (error) => {
  const code = sanitizeAuthErrorCode(error?.code);

  if (code === 'auth/email-already-in-use') {
    const methods = Array.isArray(error?.signInMethods) ? error.signInMethods : [];
    if (methods.includes('google.com')) {
      return 'That email is already linked to Google sign-in. Use "Continue with Google" instead.';
    }
    if (methods.includes('password')) {
      return 'That email is already registered. Try signing in instead, or reset your password if you forgot it.';
    }
    return 'That email is already registered. Try signing in instead, or reset your password if you forgot it.';
  }
  if (code === 'auth/invalid-email') {
    return 'That email address format looks invalid. Check for typos and try again.';
  }
  if (code === 'auth/weak-password') {
    return 'Your password is too weak. Use at least 8 characters with upper/lowercase letters, a number, and a symbol.';
  }
  if (code === 'auth/network-request-failed') {
    return 'Network error while creating your account. Check your connection and try again.';
  }
  if (code === 'auth/too-many-requests') {
    return 'Too many attempts were detected. Wait a moment, then try again.';
  }
  if (code === 'auth/operation-not-allowed') {
    return 'Email/password signup is currently unavailable. Please try Google sign-in or contact support.';
  }
  return 'Failed to create account. Please try again.';
};

export const getLoginErrorMessage = (error) => {
  const code = sanitizeAuthErrorCode(error?.code);

  if (code === 'auth/invalid-credential' || code === 'auth/user-not-found' || code === 'auth/wrong-password') {
    return 'No matching account was found for those credentials. Check your email/password or reset your password.';
  }
  if (code === 'auth/user-disabled') {
    return 'This account has been disabled. Please contact support.';
  }
  if (code === 'auth/invalid-email') {
    return 'That email address format looks invalid. Check for typos and try again.';
  }
  if (code === 'auth/network-request-failed') {
    return 'Network error while signing in. Check your connection and try again.';
  }
  if (code === 'auth/too-many-requests') {
    return 'Too many login attempts were detected. Reset your password or wait a moment before trying again.';
  }
  return 'Invalid email or password. Please try again.';
};
