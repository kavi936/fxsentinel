import { useEffect } from 'react';

const DEFAULT_TITLE = 'FXSentinel - Smarter Market Dashboard | Powered with AI';
const DEFAULT_DESCRIPTION = 'Fundamentals and macroeconomics, simplified for retail traders. Get real-time alerts, AI-powered news analysis, and actionable market insights in one place.';

/**
 * Sets document title and meta description for the current page. Restores previous values on unmount.
 * Use on every main route so each page has unique, crawlable title and description for SEO.
 */
export function useMeta(title, description) {
  useEffect(() => {
    const prevTitle = document.title;
    document.title = title ?? DEFAULT_TITLE;

    let meta = document.querySelector('meta[name="description"]');
    const prevContent = meta?.getAttribute('content');
    const newContent = description ?? DEFAULT_DESCRIPTION;
    if (!meta) {
      meta = document.createElement('meta');
      meta.setAttribute('name', 'description');
      document.head.appendChild(meta);
    }
    meta.setAttribute('content', newContent);

    return () => {
      document.title = prevTitle;
      if (meta && prevContent !== undefined) meta.setAttribute('content', prevContent);
    };
  }, [title, description]);
}
