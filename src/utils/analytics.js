import { analytics } from '../config/firebase';
import { logEvent } from 'firebase/analytics';

// Analytics utility for comprehensive tracking
class AnalyticsTracker {
  constructor() {
    this.utmParams = this.extractUTMParams();
    this.sessionId = this.generateSessionId();
    this.userJourney = [];
    this.funnelSteps = {
      landing_page_view: 1,
      feature_exploration: 2,
      signup_click: 3,
      signup_completion: 4,
      trial_start: 5,
      payment_attempt: 6,
      payment_success: 7
    };
  }

  // Extract UTM parameters from URL
  extractUTMParams() {
    const urlParams = new URLSearchParams(window.location.search);
    
    // Handle short source parameter
    const shortSource = urlParams.get('s');
    let utm_source = urlParams.get('utm_source') || 'direct';
    let utm_medium = urlParams.get('utm_medium') || 'none';
    
    // Map short sources to full UTM parameters
    if (shortSource) {
      switch (shortSource) {
        case 'ig':
          utm_source = 'instagram';
          utm_medium = 'social';
          break;
        case 'tw':
          utm_source = 'twitter';
          utm_medium = 'social';
          break;
        case 'tk':
          utm_source = 'tiktok';
          utm_medium = 'social';
          break;
        case 'fb':
          utm_source = 'facebook';
          utm_medium = 'social';
          break;
        case 'li':
          utm_source = 'linkedin';
          utm_medium = 'social';
          break;
        case 'yt':
          utm_source = 'youtube';
          utm_medium = 'social';
          break;
      }
    }
    
    return {
      utm_source: utm_source,
      utm_medium: utm_medium,
      utm_campaign: urlParams.get('utm_campaign') || 'bio',
      utm_content: urlParams.get('utm_content') || 'profile',
      utm_term: urlParams.get('utm_term') || 'forex'
    };
  }

  // Generate unique session ID
  generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }

  // Track page view with enhanced data
  trackPageView(pageName, additionalData = {}) {
    const eventData = {
      page_name: pageName,
      page_url: window.location.href,
      page_title: document.title,
      session_id: this.sessionId,
      timestamp: new Date().toISOString(),
      ...this.utmParams,
      ...additionalData
    };

    // Firebase Analytics
    logEvent(analytics, 'page_view', eventData);

    // Google Analytics 4
    if (window.gtag) {
      gtag('event', 'page_view', {
        page_title: pageName,
        page_location: window.location.href,
        custom_parameter_1: this.utmParams.utm_source,
        custom_parameter_2: this.utmParams.utm_medium,
        custom_parameter_3: this.utmParams.utm_campaign,
        custom_parameter_4: this.utmParams.utm_content,
        custom_parameter_5: this.utmParams.utm_term
      });
    }

    // Store in user journey
    this.userJourney.push({
      type: 'page_view',
      page: pageName,
      timestamp: new Date().toISOString(),
      ...eventData
    });

    console.log('📊 Analytics: Page view tracked', eventData);
  }

  // Track funnel step progression
  trackFunnelStep(stepName, stepData = {}) {
    const stepNumber = this.funnelSteps[stepName] || 0;
    const eventData = {
      funnel_step: stepName,
      funnel_step_number: stepNumber,
      session_id: this.sessionId,
      timestamp: new Date().toISOString(),
      ...this.utmParams,
      ...stepData
    };

    // Firebase Analytics
    logEvent(analytics, 'funnel_step', eventData);

    // Google Analytics 4
    if (window.gtag) {
      gtag('event', 'funnel_step', {
        funnel_step: stepName,
        funnel_step_number: stepNumber,
        custom_parameter_1: this.utmParams.utm_source,
        custom_parameter_2: this.utmParams.utm_medium,
        custom_parameter_3: this.utmParams.utm_campaign
      });
    }

    // Store in user journey
    this.userJourney.push({
      type: 'funnel_step',
      step: stepName,
      stepNumber: stepNumber,
      timestamp: new Date().toISOString(),
      ...eventData
    });

    console.log('📊 Analytics: Funnel step tracked', eventData);
  }

  // Track user engagement events
  trackEngagement(eventName, eventData = {}) {
    const enhancedData = {
      event_name: eventName,
      session_id: this.sessionId,
      timestamp: new Date().toISOString(),
      ...this.utmParams,
      ...eventData
    };

    // Firebase Analytics
    logEvent(analytics, eventName, enhancedData);

    // Google Analytics 4
    if (window.gtag) {
      gtag('event', eventName, {
        custom_parameter_1: this.utmParams.utm_source,
        custom_parameter_2: this.utmParams.utm_medium,
        custom_parameter_3: this.utmParams.utm_campaign
      });
    }

    // Store in user journey
    this.userJourney.push({
      type: 'engagement',
      event: eventName,
      timestamp: new Date().toISOString(),
      ...enhancedData
    });

    console.log('📊 Analytics: Engagement tracked', enhancedData);
  }

  // Track conversion events
  trackConversion(conversionType, conversionData = {}) {
    const eventData = {
      conversion_type: conversionType,
      conversion_value: conversionData.value || 0,
      currency: conversionData.currency || 'USD',
      session_id: this.sessionId,
      timestamp: new Date().toISOString(),
      ...this.utmParams,
      ...conversionData
    };

    // Firebase Analytics
    logEvent(analytics, 'conversion', eventData);

    // Google Analytics 4
    if (window.gtag) {
      gtag('event', 'conversion', {
        conversion_type: conversionType,
        value: conversionData.value || 0,
        currency: conversionData.currency || 'USD',
        custom_parameter_1: this.utmParams.utm_source,
        custom_parameter_2: this.utmParams.utm_medium,
        custom_parameter_3: this.utmParams.utm_campaign
      });
    }

    // Store in user journey
    this.userJourney.push({
      type: 'conversion',
      conversionType: conversionType,
      timestamp: new Date().toISOString(),
      ...eventData
    });

    console.log('📊 Analytics: Conversion tracked', eventData);
  }

  // Track feature usage
  trackFeatureUsage(featureName, usageData = {}) {
    const eventData = {
      feature_name: featureName,
      session_id: this.sessionId,
      timestamp: new Date().toISOString(),
      ...this.utmParams,
      ...usageData
    };

    // Firebase Analytics
    logEvent(analytics, 'feature_usage', eventData);

    // Google Analytics 4
    if (window.gtag) {
      gtag('event', 'feature_usage', {
        feature_name: featureName,
        custom_parameter_1: this.utmParams.utm_source,
        custom_parameter_2: this.utmParams.utm_medium,
        custom_parameter_3: this.utmParams.utm_campaign
      });
    }

    console.log('📊 Analytics: Feature usage tracked', eventData);
  }

  // Track error events
  trackError(errorType, errorData = {}) {
    const eventData = {
      error_type: errorType,
      error_message: errorData.message || 'Unknown error',
      session_id: this.sessionId,
      timestamp: new Date().toISOString(),
      ...this.utmParams,
      ...errorData
    };

    // Firebase Analytics
    logEvent(analytics, 'error', eventData);

    // Google Analytics 4
    if (window.gtag) {
      gtag('event', 'error', {
        error_type: errorType,
        custom_parameter_1: this.utmParams.utm_source,
        custom_parameter_2: this.utmParams.utm_medium,
        custom_parameter_3: this.utmParams.utm_campaign
      });
    }

    console.log('📊 Analytics: Error tracked', eventData);
  }

  // Get current user journey
  getUserJourney() {
    return this.userJourney;
  }

  // Get UTM parameters
  getUTMParams() {
    return this.utmParams;
  }

  // Get session ID
  getSessionId() {
    return this.sessionId;
  }
}

// Create singleton instance
const analyticsTracker = new AnalyticsTracker();

// Export the tracker instance and helper functions
export default analyticsTracker;

// Helper functions for common tracking scenarios
export const trackLandingPageView = () => {
  analyticsTracker.trackPageView('landing_page');
  analyticsTracker.trackFunnelStep('landing_page_view');
};

export const trackSignupClick = (source = 'unknown') => {
  analyticsTracker.trackFunnelStep('signup_click', { source });
  analyticsTracker.trackEngagement('signup_button_click', { source });
};

export const trackSignupCompletion = (method = 'unknown') => {
  analyticsTracker.trackFunnelStep('signup_completion', { method });
  analyticsTracker.trackConversion('signup', { value: 0, method });
};

export const trackTrialStart = () => {
  analyticsTracker.trackFunnelStep('trial_start');
  analyticsTracker.trackConversion('trial_start', { value: 0 });
};

export const trackPaymentAttempt = (amount = 0) => {
  analyticsTracker.trackFunnelStep('payment_attempt', { amount });
  analyticsTracker.trackEngagement('payment_attempt', { amount });
};

export const trackPaymentSuccess = (amount = 0) => {
  analyticsTracker.trackFunnelStep('payment_success', { amount });
  analyticsTracker.trackConversion('payment_success', { value: amount });
};

export const trackFeatureUsage = (featureName, usageData = {}) => {
  analyticsTracker.trackFeatureUsage(featureName, usageData);
};

export const trackError = (errorType, errorData = {}) => {
  analyticsTracker.trackError(errorType, errorData);
};

export const trackEngagement = (eventName, eventData = {}) => {
  analyticsTracker.trackEngagement(eventName, eventData);
};
