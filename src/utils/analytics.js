import { analytics } from '../config/firebase';
import { logEvent } from 'firebase/analytics';

// Analytics utility for comprehensive tracking
class AnalyticsTracker {
  constructor() {
    this.utmParams = this.extractUTMParams();
    this.sessionId = this.generateSessionId();
    this.userJourney = [];
    this.pageStartTime = Date.now();
    this.scrollDepth = {
      25: false,
      50: false,
      75: false,
      100: false
    };
    this.visibleElements = new Set();
    this.funnelSteps = {
      landing_page_view: 1,
      feature_exploration: 2,
      signup_click: 3,
      signup_completion: 4,
      trial_start: 5,
      payment_attempt: 6,
      payment_success: 7
    };
    
    // Initialize scroll and visibility tracking
    this.initScrollTracking();
    this.initVisibilityTracking();
    this.initTimeTracking();
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

  // Track scroll depth
  initScrollTracking() {
    let ticking = false;
    
    const handleScroll = () => {
      if (!ticking) {
        window.requestAnimationFrame(() => {
          const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
          const docHeight = document.documentElement.scrollHeight - window.innerHeight;
          const scrollPercent = Math.round((scrollTop / docHeight) * 100);
          
          // Track milestone scroll depths
          if (scrollPercent >= 25 && !this.scrollDepth[25]) {
            this.scrollDepth[25] = true;
            this.trackEngagement('scroll_depth_25', { scroll_percent: 25 });
          }
          if (scrollPercent >= 50 && !this.scrollDepth[50]) {
            this.scrollDepth[50] = true;
            this.trackEngagement('scroll_depth_50', { scroll_percent: 50 });
          }
          if (scrollPercent >= 75 && !this.scrollDepth[75]) {
            this.scrollDepth[75] = true;
            this.trackEngagement('scroll_depth_75', { scroll_percent: 75 });
          }
          if (scrollPercent >= 100 && !this.scrollDepth[100]) {
            this.scrollDepth[100] = true;
            this.trackEngagement('scroll_depth_100', { scroll_percent: 100 });
          }
          
          ticking = false;
        });
        ticking = true;
      }
    };
    
    window.addEventListener('scroll', handleScroll, { passive: true });
  }

  // Track element visibility using Intersection Observer
  initVisibilityTracking() {
    if (typeof IntersectionObserver === 'undefined') return;
    
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting && entry.intersectionRatio > 0.5) {
          const elementId = entry.target.id || entry.target.className || 'unknown';
          if (!this.visibleElements.has(elementId)) {
            this.visibleElements.add(elementId);
            this.trackEngagement('element_viewed', {
              element_id: elementId,
              element_type: entry.target.tagName.toLowerCase()
            });
          }
        }
      });
    }, {
      threshold: 0.5
    });
    
    // Observe key sections
    const sectionsToTrack = [
      'features',
      'testimonials',
      'pricing',
      'about',
      'faq',
      'contact'
    ];
    
    sectionsToTrack.forEach(sectionId => {
      const element = document.getElementById(sectionId);
      if (element) {
        observer.observe(element);
      }
    });
  }

  // Track time on page
  initTimeTracking() {
    // Track 30 seconds
    setTimeout(() => {
      this.trackEngagement('time_on_page_30s', { time_seconds: 30 });
    }, 30000);
    
    // Track 1 minute
    setTimeout(() => {
      this.trackEngagement('time_on_page_1m', { time_seconds: 60 });
    }, 60000);
    
    // Track 2 minutes
    setTimeout(() => {
      this.trackEngagement('time_on_page_2m', { time_seconds: 120 });
    }, 120000);
    
    // Track 5 minutes
    setTimeout(() => {
      this.trackEngagement('time_on_page_5m', { time_seconds: 300 });
    }, 300000);
    
    // Track time on page when leaving
    window.addEventListener('beforeunload', () => {
      const timeOnPage = Math.round((Date.now() - this.pageStartTime) / 1000);
      this.trackEngagement('time_on_page_exit', { time_seconds: timeOnPage });
    });
  }

  // Track CTA clicks
  trackCTAClick(ctaName, ctaLocation, additionalData = {}) {
    this.trackEngagement('cta_click', {
      cta_name: ctaName,
      cta_location: ctaLocation,
      ...additionalData
    });
    this.trackFunnelStep('cta_click', { cta_name: ctaName, cta_location: ctaLocation });
  }

  // Track testimonial views
  trackTestimonialView(testimonialIndex) {
    this.trackEngagement('testimonial_viewed', {
      testimonial_index: testimonialIndex
    });
  }

  // Track feature card interactions
  trackFeatureCardInteraction(featureName, interactionType = 'view') {
    this.trackEngagement('feature_card_interaction', {
      feature_name: featureName,
      interaction_type: interactionType
    });
    this.trackFeatureUsage(featureName, { interaction_type: interactionType });
  }

  // Track blog post engagement
  trackBlogPostEngagement(postSlug, engagementType, additionalData = {}) {
    this.trackEngagement('blog_post_engagement', {
      post_slug: postSlug,
      engagement_type: engagementType, // 'view', 'read', 'share', 'click'
      ...additionalData
    });
  }

  // Track video interactions
  trackVideoInteraction(videoName, action, additionalData = {}) {
    this.trackEngagement('video_interaction', {
      video_name: videoName,
      action: action, // 'play', 'pause', 'complete', 'seek'
      ...additionalData
    });
  }

  // Track form interactions
  trackFormInteraction(formName, fieldName, interactionType, additionalData = {}) {
    this.trackEngagement('form_interaction', {
      form_name: formName,
      field_name: fieldName,
      interaction_type: interactionType, // 'focus', 'blur', 'change', 'submit'
      ...additionalData
    });
  }

  // Track external link clicks
  trackExternalLinkClick(url, linkText) {
    this.trackEngagement('external_link_click', {
      link_url: url,
      link_text: linkText
    });
  }

  // Track search queries (if you add search)
  trackSearchQuery(query, resultsCount = 0) {
    this.trackEngagement('search_query', {
      search_query: query,
      results_count: resultsCount
    });
  }

  // Track user device and browser info
  trackDeviceInfo() {
    const deviceInfo = {
      user_agent: navigator.userAgent,
      screen_width: window.screen.width,
      screen_height: window.screen.height,
      viewport_width: window.innerWidth,
      viewport_height: window.innerHeight,
      device_type: this.getDeviceType(),
      browser: this.getBrowser(),
      os: this.getOS()
    };
    
    this.trackEngagement('device_info', deviceInfo);
    return deviceInfo;
  }

  getDeviceType() {
    const width = window.innerWidth;
    if (width < 768) return 'mobile';
    if (width < 1024) return 'tablet';
    return 'desktop';
  }

  getBrowser() {
    const ua = navigator.userAgent;
    if (ua.indexOf('Chrome') > -1) return 'Chrome';
    if (ua.indexOf('Firefox') > -1) return 'Firefox';
    if (ua.indexOf('Safari') > -1) return 'Safari';
    if (ua.indexOf('Edge') > -1) return 'Edge';
    return 'Unknown';
  }

  getOS() {
    const ua = navigator.userAgent;
    if (ua.indexOf('Windows') > -1) return 'Windows';
    if (ua.indexOf('Mac') > -1) return 'macOS';
    if (ua.indexOf('Linux') > -1) return 'Linux';
    if (ua.indexOf('Android') > -1) return 'Android';
    if (ua.indexOf('iOS') > -1) return 'iOS';
    return 'Unknown';
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

// Enhanced tracking functions
export const trackCTAClick = (ctaName, ctaLocation, additionalData = {}) => {
  analyticsTracker.trackCTAClick(ctaName, ctaLocation, additionalData);
};

export const trackTestimonialView = (testimonialIndex) => {
  analyticsTracker.trackTestimonialView(testimonialIndex);
};

export const trackFeatureCardInteraction = (featureName, interactionType = 'view') => {
  analyticsTracker.trackFeatureCardInteraction(featureName, interactionType);
};

export const trackBlogPostEngagement = (postSlug, engagementType, additionalData = {}) => {
  analyticsTracker.trackBlogPostEngagement(postSlug, engagementType, additionalData);
};

export const trackVideoInteraction = (videoName, action, additionalData = {}) => {
  analyticsTracker.trackVideoInteraction(videoName, action, additionalData);
};

export const trackFormInteraction = (formName, fieldName, interactionType, additionalData = {}) => {
  analyticsTracker.trackFormInteraction(formName, fieldName, interactionType, additionalData);
};

export const trackExternalLinkClick = (url, linkText) => {
  analyticsTracker.trackExternalLinkClick(url, linkText);
};

export const trackSearchQuery = (query, resultsCount = 0) => {
  analyticsTracker.trackSearchQuery(query, resultsCount);
};

// Initialize device tracking on import
if (typeof window !== 'undefined') {
  analyticsTracker.trackDeviceInfo();
}
