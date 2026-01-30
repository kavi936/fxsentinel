import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

/**
 * Hook to dynamically set canonical tag based on current route
 * Fixes Google Search Console "Alternate page with proper canonical tag" error
 */
export const useCanonicalTag = () => {
  const location = useLocation();
  
  useEffect(() => {
    const baseUrl = 'https://fxsentinel.io';
    const canonicalUrl = `${baseUrl}${location.pathname}${location.search}`;
    
    // Remove existing canonical tag if it exists
    let canonicalLink = document.querySelector('link[rel="canonical"]');
    
    if (!canonicalLink) {
      // Create new canonical link element
      canonicalLink = document.createElement('link');
      canonicalLink.setAttribute('rel', 'canonical');
      document.head.appendChild(canonicalLink);
    }
    
    // Set the canonical URL to the current page
    canonicalLink.setAttribute('href', canonicalUrl);
    
    // Cleanup function (optional, but good practice)
    return () => {
      // Don't remove on cleanup - we want the canonical tag to persist
    };
  }, [location.pathname, location.search]);
};
