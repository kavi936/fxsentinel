import { useEffect } from 'react';

const DEFAULT_TITLE = 'FXSentinel | Macro Dashboard & AI News Context for Forex Traders';
const DEFAULT_DESCRIPTION =
  'Retail forex macro intelligence in one place: live economic calendar, AI-assisted news context for major pairs and gold, and Telegram alerts. Tools and education—we are not a broker.';
const DEFAULT_ROBOTS = 'index, follow';

/**
 * Sets document title and meta description for the current page. Restores previous values on unmount.
 * Use on every main route so each page has unique, crawlable title and description for SEO.
 *
 * @param {string | undefined} title
 * @param {string | undefined} description
 * @param {{ robots?: string }} [options] — e.g. { robots: 'noindex, follow' } for login-gated app surfaces
 */
export function useMeta(title, description, options = {}) {
  const { robots } = options;

  useEffect(() => {
    const prevTitle = document.title;
    document.title = title ?? DEFAULT_TITLE;

    let descMeta = document.querySelector('meta[name="description"]');
    const prevDescContent = descMeta?.getAttribute('content');
    const newDesc = description ?? DEFAULT_DESCRIPTION;
    if (!descMeta) {
      descMeta = document.createElement('meta');
      descMeta.setAttribute('name', 'description');
      document.head.appendChild(descMeta);
    }
    descMeta.setAttribute('content', newDesc);

    let robotsMeta = document.querySelector('meta[name="robots"]');
    const prevRobotsContent =
      robots != null ? robotsMeta?.getAttribute('content') ?? DEFAULT_ROBOTS : null;

    if (robots != null) {
      if (!robotsMeta) {
        robotsMeta = document.createElement('meta');
        robotsMeta.setAttribute('name', 'robots');
        document.head.appendChild(robotsMeta);
      }
      robotsMeta.setAttribute('content', robots);
    }

    return () => {
      document.title = prevTitle;
      if (descMeta && prevDescContent !== undefined) {
        descMeta.setAttribute('content', prevDescContent);
      }
      if (robots != null) {
        const m = document.querySelector('meta[name="robots"]');
        if (m) {
          m.setAttribute('content', prevRobotsContent ?? DEFAULT_ROBOTS);
        }
      }
    };
  }, [title, description, robots]);
}
