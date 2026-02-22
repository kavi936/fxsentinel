# SEO Full Audit Checklist

Audit date: Feb 2026. This doc summarizes what was checked and fixed so **site URLs and logo work reliably** after recent changes.

---

## 1. Favicon / logo

| Check | Status | Notes |
|------|--------|------|
| `public/favicon.png` exists | ✅ | You added the Fx-on-black PNG. |
| Favicon linked with **relative** `/favicon.png` | ✅ | So local dev and production both use the correct file (no hardcoded production URL). |
| 48×48 (and 96×96) `sizes` in `<link rel="icon">` | ✅ | Meets Google’s SERP favicon preference. |
| `manifest.json` icons use `/favicon.png` | ✅ | PWA icons point to same file. |
| Vercel header for `/favicon.png` | ✅ | `Content-Type: image/png`, cache immutable. |

**Why it can break:** If favicon links were switched to absolute `https://fxsentinel.io/favicon.png`, local dev would never use `public/favicon.png`. Keeping **relative** `/favicon.png` fixes that.

---

## 2. Canonical URLs

| Check | Status | Notes |
|------|--------|------|
| Default canonical in `index.html` | ✅ | `<link rel="canonical" href="https://fxsentinel.io/">` so crawlers see it before JS. |
| `useCanonicalTag` hook | ✅ | Updates canonical per route (used in `useRouteTracking` → `App.jsx`). |
| Base URL | ✅ | `https://fxsentinel.io` in hook; no trailing slash on path segments. |

**Why it can break:** If the only canonical is set in JS, crawlers that don’t run JS (or run it late) may see no canonical or wrong one. The default in HTML fixes that.

---

## 3. Sitemap and robots

| Check | Status | Notes |
|------|--------|------|
| `public/sitemap.xml` | ✅ | 13 URLs, all `https://fxsentinel.io/...`. |
| `public/robots.txt` | ✅ | `Sitemap: https://fxsentinel.io/sitemap.xml`, Allow rules, Disallow for auth flows. |
| Vercel headers for sitemap/robots | ✅ | Correct Content-Type and cache. |
| Sitemap URLs match routes | ✅ | All listed paths have a route or redirect (see /terms below). |

**Vercel behavior:** Static files in `dist/` (from `public/`) are served first. So `dist/sitemap.xml` and `dist/robots.txt` are served; the catch‑all rewrite to `index.html` only applies when no static file matches.

---

## 4. Routes and URLs (why “site URLs stopped working”)

| Check | Status | Notes |
|------|--------|------|
| `/terms` in sitemap and Signup link | ✅ Fixed | Route was missing; `/terms` now **redirects to `/disclaimer`** so the URL doesn’t 404. |
| Static crawler nav in `index.html` | ✅ | Includes Terms of Service link so crawlers see it. |
| Route map in `useRouteTracking` | ✅ | `terms` added for analytics. |

**Why it broke:** Sitemap and Signup linked to `/terms`, but there was no route. Visiting `/terms` showed the app shell with no content. The redirect to `/disclaimer` keeps the URL valid; you can later replace it with a dedicated Terms page.

---

## 5. Meta and Open Graph (unchanged, verified)

| Check | Status |
|------|--------|
| `og:url`, `og:image`, `twitter:url`, `twitter:image` | ✅ Absolute `https://fxsentinel.io/...` |
| Title, description, keywords in HTML | ✅ |
| Structured data: Organization, WebApplication, FAQPage, BreadcrumbList | ✅ |

---

## 6. Deployment (Vercel)

| Check | Status | Notes |
|------|--------|------|
| Rewrite `/(.*)` → `/index.html` | ✅ | SPA fallback; static files still served first. |
| Headers for `/favicon.png`, `/og-image.png`, `/sitemap.xml`, `/robots.txt` | ✅ | Correct types and cache. |
| `dist` = build output | ✅ | So `public/favicon.png` → `dist/favicon.png` at root. |

---

## Quick checklist after future changes

1. **Favicon:** Keep favicon links **relative** (`/favicon.png`) so dev and prod both use the right file.
2. **Canonical:** Keep the default `<link rel="canonical" href="https://fxsentinel.io/">` in `index.html`; the hook can override it per route.
3. **New pages:** If you add a URL to the sitemap or main nav, add a matching route (or redirect) in `App.jsx`.
4. **Static files:** Any new root asset (e.g. `favicon.ico`) should live in `public/` so it’s copied to `dist/` and served before the SPA rewrite.

---

## Files touched in this audit

- `index.html` – Default canonical; Terms in crawler nav.
- `src/App.jsx` – `/terms` → redirect to `/disclaimer`; `Navigate` import.
- `src/hooks/useRouteTracking.js` – `terms` in route map.
- `vercel.json` – Header for `/favicon.png`.
- `docs/SEO_FAVICON_AND_SITELINKS_EVALUATION.md` – Earlier favicon/sitelinks notes (favicon is now relative again).
- `docs/SEO_FULL_AUDIT_CHECKLIST.md` – This file.
