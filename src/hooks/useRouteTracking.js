import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import analyticsTracker from '../utils/analytics';

/**
 * Hook to automatically track page views when route changes
 * This ensures all pages are tracked without manual tracking in each component
 */
export const useRouteTracking = () => {
  const location = useLocation();
  
  useEffect(() => {
    // Map route paths to readable page names
    const getPageName = (pathname) => {
      // Remove leading slash and replace with readable name
      const path = pathname.replace('/', '') || 'landing_page';
      
      // Map common routes to readable names
      const routeMap = {
        '': 'landing_page',
        'blog': 'blog',
        'login': 'login',
        'signup': 'signup',
        'auth-redirect': 'auth_redirect',
        'dashboard': 'dashboard',
        'disclaimer': 'disclaimer',
        'privacy': 'privacy',
        'feedback': 'feedback',
        'trial-welcome': 'trial_welcome'
      };
      
      // Check if it's a blog post
      if (pathname.startsWith('/blog/')) {
        const blogSlug = pathname.replace('/blog/', '');
        return `blog_post_${blogSlug}`;
      }
      
      return routeMap[path] || path.replace(/-/g, '_');
    };
    
    const pageName = getPageName(location.pathname);
    
    // Track page view with route information
    analyticsTracker.trackPageView(pageName, {
      route: location.pathname,
      search: location.search,
      hash: location.hash
    });
    
  }, [location]);
};

