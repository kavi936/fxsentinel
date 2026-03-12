import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

/**
 * Hook to dynamically set canonical tag based on current route.
 *
 * Important SEO behavior:
 * - Canonicals are now path-based only (no query string), so tracking params
 *   like utm_* / gclid / fbclid do NOT create separate canonical URLs.
 * - This consolidates link equity and avoids duplicate-content style issues.
 */
export const useCanonicalTag = () => {
  const location = useLocation();

  useEffect(() => {
    const baseUrl = 'https://fxsentinel.io';

    // Always canonicalize on path only; ignore query parameters completely.
    // If we ever need "real" query params in canonicals, we can add a safe
    // allowlist here instead of including the raw search string.
    const path = location.pathname || '/';
    const canonicalUrl = `${baseUrl}${path}`;

    let canonicalLink = document.querySelector('link[rel="canonical"]');

    if (!canonicalLink) {
      canonicalLink = document.createElement('link');
      canonicalLink.setAttribute('rel', 'canonical');
      document.head.appendChild(canonicalLink);
    }

    canonicalLink.setAttribute('href', canonicalUrl);

    return () => {
      // Intentionally keep the canonical tag; it will be updated on the next route.
    };
  }, [location.pathname]);
};
