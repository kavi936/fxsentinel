import { analytics } from '../config/firebase';
import { logEvent } from 'firebase/analytics';

// Analytics utility for comprehensive tracking
class AnalyticsTracker {
  constructor() {
    // Try to retrieve persisted UTM params first, then extract from URL
    this.utmParams = this.getPersistedUTMParams() || this.extractUTMParams();
    // Persist UTM params if they exist (for use after redirects)
    if (this.utmParams && this.utmParams.utm_source !== 'direct') {
      this.persistUTMParams(this.utmParams);
    }
    
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
      auth_redirect: 5,
      dashboard_access: 6,
      dashboard_first_view: 7,
      trial_start: 8,
      payment_attempt: 9,
      payment_success: 10
    };
    
    // Initialize scroll and visibility tracking
    this.initScrollTracking();
    this.initVisibilityTracking();
    this.initTimeTracking();
  }

  // Persist UTM parameters to sessionStorage (survives redirects)
  persistUTMParams(utmParams) {
    try {
      if (typeof window !== 'undefined' && window.sessionStorage) {
        sessionStorage.setItem('fxsentinel_utm_params', JSON.stringify(utmParams));
        console.log('📊 Analytics: UTM params persisted', utmParams);
      }
    } catch (e) {
      console.warn('📊 Analytics: Failed to persist UTM params', e);
    }
  }

  // Retrieve persisted UTM parameters from sessionStorage
  getPersistedUTMParams() {
    try {
      if (typeof window !== 'undefined' && window.sessionStorage) {
        const stored = sessionStorage.getItem('fxsentinel_utm_params');
        if (stored) {
          const params = JSON.parse(stored);
          console.log('📊 Analytics: Retrieved persisted UTM params', params);
          return params;
        }
      }
    } catch (e) {
      console.warn('📊 Analytics: Failed to retrieve persisted UTM params', e);
    }
    return null;
  }

  // Extract UTM parameters from URL with enhanced referrer detection
  extractUTMParams() {
    const urlParams = new URLSearchParams(window.location.search);
    const referrer = document.referrer || '';
    
    // Priority 1: Check UTM parameters first (highest priority)
    if (urlParams.get('utm_source')) {
      const params = {
        utm_source: urlParams.get('utm_source'),
        utm_medium: urlParams.get('utm_medium') || 'none',
        utm_campaign: urlParams.get('utm_campaign') || 'none',
        utm_content: urlParams.get('utm_content') || 'none',
        utm_term: urlParams.get('utm_term') || 'none',
        referrer: referrer
      };
      // Persist UTM params when found in URL
      this.persistUTMParams(params);
      return params;
    }
    
    // Priority 2: Handle short source parameter
    const shortSource = urlParams.get('s');
    if (shortSource) {
      const mapped = this.mapShortSource(shortSource);
      const params = {
        ...mapped,
        referrer: referrer
      };
      this.persistUTMParams(params);
      return params;
    }
    
    // Priority 3: Detect traffic source from referrer
    const referrerSource = this.detectReferrerSource(referrer);
    if (referrerSource) {
      const params = {
        ...referrerSource,
        referrer: referrer
      };
      // Only persist if it's not direct traffic
      if (referrerSource.utm_source !== 'direct') {
        this.persistUTMParams(params);
      }
      return params;
    }
    
    // Default: Direct traffic (don't persist direct traffic)
    return {
      utm_source: 'direct',
      utm_medium: 'none',
      utm_campaign: 'direct',
      utm_content: 'direct',
      utm_term: 'direct',
      referrer: referrer
    };
  }

  // Map short source codes to full UTM parameters
  mapShortSource(shortSource) {
    const mapping = {
      'ig': { utm_source: 'instagram', utm_medium: 'social', utm_campaign: 'bio', utm_content: 'profile', utm_term: 'instagram' },
      'tw': { utm_source: 'twitter', utm_medium: 'social', utm_campaign: 'bio', utm_content: 'profile', utm_term: 'twitter' },
      'tk': { utm_source: 'tiktok', utm_medium: 'social', utm_campaign: 'bio', utm_content: 'profile', utm_term: 'tiktok' },
      'fb': { utm_source: 'facebook', utm_medium: 'social', utm_campaign: 'bio', utm_content: 'profile', utm_term: 'facebook' },
      'li': { utm_source: 'linkedin', utm_medium: 'social', utm_campaign: 'bio', utm_content: 'profile', utm_term: 'linkedin' },
      'yt': { utm_source: 'youtube', utm_medium: 'social', utm_campaign: 'bio', utm_content: 'profile', utm_term: 'youtube' }
    };
    
    return mapping[shortSource] || { utm_source: 'direct', utm_medium: 'none', utm_campaign: 'unknown', utm_content: 'unknown', utm_term: 'unknown' };
  }

  // Detect traffic source from referrer URL
  detectReferrerSource(referrer) {
    if (!referrer) return null;
    
    const referrerLower = referrer.toLowerCase();
    
    // Google Search detection
    if (referrerLower.includes('google.com/search') || 
        (referrerLower.includes('google.') && referrerLower.includes('/search'))) {
      const searchQuery = this.extractSearchQuery(referrer);
      return {
        utm_source: 'google',
        utm_medium: 'organic',
        utm_campaign: 'search',
        utm_content: searchQuery || 'organic_search',
        utm_term: searchQuery || 'organic_search'
      };
    }
    
    // Instagram detection
    if (referrerLower.includes('instagram.com') || referrerLower.includes('instagr.am')) {
      return {
        utm_source: 'instagram',
        utm_medium: 'social',
        utm_campaign: 'organic',
        utm_content: 'profile_link',
        utm_term: 'instagram'
      };
    }
    
    // Twitter/X detection
    if (referrerLower.includes('twitter.com') || referrerLower.includes('x.com')) {
      return {
        utm_source: 'twitter',
        utm_medium: 'social',
        utm_campaign: 'organic',
        utm_content: 'tweet',
        utm_term: 'twitter'
      };
    }
    
    // Facebook detection
    if (referrerLower.includes('facebook.com') || referrerLower.includes('fb.com')) {
      return {
        utm_source: 'facebook',
        utm_medium: 'social',
        utm_campaign: 'organic',
        utm_content: 'post',
        utm_term: 'facebook'
      };
    }
    
    // LinkedIn detection
    if (referrerLower.includes('linkedin.com')) {
      return {
        utm_source: 'linkedin',
        utm_medium: 'social',
        utm_campaign: 'organic',
        utm_content: 'post',
        utm_term: 'linkedin'
      };
    }
    
    // TikTok detection
    if (referrerLower.includes('tiktok.com')) {
      return {
        utm_source: 'tiktok',
        utm_medium: 'social',
        utm_campaign: 'organic',
        utm_content: 'video',
        utm_term: 'tiktok'
      };
    }
    
    // YouTube detection
    if (referrerLower.includes('youtube.com') || referrerLower.includes('youtu.be')) {
      return {
        utm_source: 'youtube',
        utm_medium: 'social',
        utm_campaign: 'organic',
        utm_content: 'video',
        utm_term: 'youtube'
      };
    }
    
    // Bing Search detection
    if (referrerLower.includes('bing.com/search')) {
      const searchQuery = this.extractSearchQuery(referrer);
      return {
        utm_source: 'bing',
        utm_medium: 'organic',
        utm_campaign: 'search',
        utm_content: searchQuery || 'organic_search',
        utm_term: searchQuery || 'organic_search'
      };
    }
    
    return null;
  }

  // Extract search query from referrer URL
  extractSearchQuery(referrer) {
    try {
      const url = new URL(referrer);
      const query = url.searchParams.get('q') || url.searchParams.get('query') || '';
      return query.substring(0, 100); // Limit length
    } catch (e) {
      return null;
    }
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

    // Google Tag Manager / Google Analytics 4
    // Push to dataLayer for GTM
    if (window.dataLayer) {
      window.dataLayer.push({
        event: 'page_view',
        page_title: pageName,
        page_location: window.location.href,
        page_name: pageName,
        utm_source: this.utmParams.utm_source,
        utm_medium: this.utmParams.utm_medium,
        utm_campaign: this.utmParams.utm_campaign,
        utm_content: this.utmParams.utm_content,
        utm_term: this.utmParams.utm_term,
        referrer: this.utmParams.referrer || document.referrer
      });
    }
    
    // Also use gtag if available (direct GA4 or GTM)
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

    // Google Tag Manager / Google Analytics 4
    if (window.dataLayer) {
      window.dataLayer.push({
        event: 'funnel_step',
        funnel_step: stepName,
        funnel_step_number: stepNumber,
        utm_source: this.utmParams.utm_source,
        utm_medium: this.utmParams.utm_medium,
        utm_campaign: this.utmParams.utm_campaign,
        ...stepData
      });
    }
    
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

    // Google Tag Manager / Google Analytics 4
    if (window.dataLayer) {
      window.dataLayer.push({
        event: eventName,
        utm_source: this.utmParams.utm_source,
        utm_medium: this.utmParams.utm_medium,
        utm_campaign: this.utmParams.utm_campaign,
        ...eventData
      });
    }
    
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

    // Google Tag Manager / Google Analytics 4
    if (window.dataLayer) {
      window.dataLayer.push({
        event: 'conversion',
        conversion_type: conversionType,
        conversion_value: conversionData.value || 0,
        currency: conversionData.currency || 'USD',
        utm_source: this.utmParams.utm_source,
        utm_medium: this.utmParams.utm_medium,
        utm_campaign: this.utmParams.utm_campaign,
        ...conversionData
      });
    }

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

// New funnel step tracking functions
export const trackAuthRedirect = (authMethod = 'unknown') => {
  analyticsTracker.trackFunnelStep('auth_redirect', { auth_method: authMethod });
  analyticsTracker.trackPageView('auth_redirect', { auth_method: authMethod });
};

export const trackDashboardAccess = (isFirstView = false, subscriptionStatus = null) => {
  analyticsTracker.trackFunnelStep('dashboard_access', { 
    is_first_view: isFirstView,
    subscription_status: subscriptionStatus 
  });
  analyticsTracker.trackEngagement('dashboard_access', { 
    is_first_view: isFirstView,
    subscription_status: subscriptionStatus 
  });
  
  if (isFirstView) {
    analyticsTracker.trackFunnelStep('dashboard_first_view', { subscription_status: subscriptionStatus });
  }
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

// Onboarding tour tracking (see docs/ONBOARDING_PLAN.md Section 9)
export const trackOnboardingStarted = (trigger = 'auto') => {
  analyticsTracker.trackEngagement('onboarding_tour_started', { trigger, step_index: 0 });
};

export const trackOnboardingCompleted = (totalSteps = 8) => {
  analyticsTracker.trackEngagement('onboarding_tour_completed', { total_steps: totalSteps });
};

export const trackOnboardingSkipped = (stepIndex = 0, totalSteps = 8) => {
  analyticsTracker.trackEngagement('onboarding_tour_skipped', { step_index: stepIndex, total_steps: totalSteps });
};

export const trackOnboardingStepViewed = (stepIndex, stepTarget, totalSteps = 8) => {
  analyticsTracker.trackEngagement('onboarding_step_viewed', {
    step_index: stepIndex,
    step_target: stepTarget,
    total_steps: totalSteps
  });
};

// Initialize device tracking on import
if (typeof window !== 'undefined') {
  analyticsTracker.trackDeviceInfo();
  // Expose analytics tracker to window for debugging/testing
  window.analyticsTracker = analyticsTracker;
}
