# Google Search Console & SEO – Codebase Analysis

This doc summarizes how the project supports **Google Search Console (GSC)** and **SEO**, and what to do next for “Pages” and indexing.

---

## 1. What’s already in place

### 1.1 Crawlability & discovery

| Item | Location | Purpose |
|------|----------|--------|
| **Sitemap** | `public/sitemap.xml` | 19 URLs (home, blog, blog posts, dashboard, login, signup, disclaimer, privacy, feedback). `/terms` omitted because it redirects to `/disclaimer`. Used by GSC to discover and prioritize URLs. |
| **robots.txt** | `public/robots.txt` | `Allow: /`, `Disallow` for `/trial-welcome`, `/auth-redirect`, `/forgot-password`. Points to `Sitemap: https://fxsentinel.io/sitemap.xml`. |
| **Vercel** | `vercel.json` | Correct `Content-Type` and cache headers for `/sitemap.xml`, `/robots.txt`, `/og-image.png`, `/favicon.png`. |

**Note:** The build copies `public/` into `dist/`, so the **live** sitemap and robots are the **static** files. The serverless `api/sitemap.js` and `api/robots.js` are only used if you explicitly rewrite `/sitemap.xml` → `/api/sitemap` (you don’t). Keep `public/sitemap.xml` as the source of truth.

### 1.2 Canonical URLs (important for GSC “Pages”)

| Item | Location | Purpose |
|------|----------|--------|
| **Default canonical** | `index.html` | `<link rel="canonical" href="https://fxsentinel.io/">` so crawlers see a valid canonical before JS. |
| **Per-route canonical** | `src/hooks/useCanonicalTag.js` | Sets canonical to `https://fxsentinel.io` + current path + search. Fixes GSC “Alternate page with proper canonical tag” when every page pointed to `/`. |
| **Usage** | `src/hooks/useRouteTracking.js` → `App.jsx` | `useRouteTracking()` runs on every route, so every page gets the correct canonical. |

So each URL (e.g. `/blog`, `/signup`) has its **own** canonical; Google can index them as separate pages.

### 1.3 Titles & meta descriptions

| Item | Location | Purpose |
|------|----------|--------|
| **Default** | `index.html` | `<title>`, `<meta name="description">`, `<meta name="keywords">` for the homepage. |
| **Per-page** | `src/hooks/useMeta.js` | Updates `document.title` and `<meta name="description">` per route. |
| **Used on** | Landing, Blog, each blog post, Login, Signup, Dashboard, Disclaimer, Privacy, Feedback, Verify Email. |

Unique titles and descriptions help GSC “Pages” and search snippets.

### 1.4 Open Graph & Twitter

In `index.html`: `og:type`, `og:url`, `og:title`, `og:description`, `og:image` (1200×630), `twitter:card`, `twitter:url`, `twitter:title`, `twitter:description`, `twitter:image`. All use absolute `https://fxsentinel.io/...` URLs. Important for sharing and for crawlers that use OG as a fallback.

### 1.5 Structured data (Schema.org)

In `index.html`:

- **Organization** – name, url, logo, description, contact, sameAs.
- **WebApplication** – name, description, url, category, offers.
- **FAQPage** – 4 Q&As (what we do, cost, no profit guarantee, data sources).
- **BreadcrumbList** – Home (helps hierarchy/sitelinks).

In `src/components/BlogPost.jsx`: **BlogPosting** JSON-LD per post (headline, description, datePublished, author, mainEntityOfPage, url, articleSection, keywords). Helps rich results and GEO.

### 1.6 Crawler-friendly links

In `index.html`, a visually hidden `<nav>` with static links to Home, Dashboard, Blog, Login, Sign Up, Feedback, Disclaimer, Privacy, Terms. So crawlers see important URLs even without executing JS.

### 1.7 Routes vs sitemap

All sitemap URLs have a route or redirect in `App.jsx`:

- `/terms` → `<Navigate to="/disclaimer" replace />` (no 404).
- `/feedbackform` → redirect to `/feedback`.

So GSC won’t see 404s for sitemap URLs.

---

## 2. Google Search Console verification

There is **no** `google-site-verification` meta tag in the codebase. Verification is often done by:

- **HTML tag:** add `<meta name="google-site-verification" content="YOUR_CODE" />` in `index.html` (a commented placeholder is in `index.html` for this).
- **DNS:** TXT record on `fxsentinel.io`.
- **Google Analytics / GTM:** if the property is linked to GSC.

If the property is already verified (e.g. via DNS), you don’t need to add the meta tag. If you want to use the HTML tag method, uncomment and set the value in `index.html`.

---

## 3. What to do in Google Search Console (“Pages”)

1. **Submit sitemap**  
   GSC → **Sitemaps** → submit `https://fxsentinel.io/sitemap.xml`. You can re-submit after big URL or meta changes (as in `docs/2026_SEO_and _GEO to-do.md`).

2. **Request indexing for important URLs**  
   GSC → **URL Inspection** (top bar) → enter URL → **Request indexing**. Use for new or updated pages; limit ~10/day. Details: `docs/GOOGLE_SEARCH_CONSOLE_INDEXING.md`.

3. **Check “Pages” and “Why pages aren’t indexed”**  
   - **Pages** → see indexed vs not indexed.  
   - **Why pages aren’t indexed** → fix “Alternate page with proper canonical tag” (already addressed by `useCanonicalTag`), “Crawled – currently not indexed”, “Discovered – currently not indexed”, etc.

4. **Validate fixes**  
   After changing canonicals or meta, use URL Inspection and “Request indexing” for a few key URLs to speed up re-crawl.

---

## 4. “Page with redirect” for `http://fxsentinel.io/`

**What GSC shows:** Under “Why pages aren’t indexed” you may see **“Page with redirect”** for `http://fxsentinel.io/`, with **Validation failed** (e.g. Started 2/17/26, Failed 3/7/26).

**What it means:** Google is crawling the **HTTP** URL. Your host (Vercel) redirects HTTP → HTTPS, so that URL is a redirect, not a final page. GSC correctly does **not** index the redirecting URL; it indexes the **destination** (`https://fxsentinel.io/`). So “Page with redirect” + “Validation failed” for the HTTP URL is **expected** and not a bug.

**What to do:**

1. **Use the HTTPS property in GSC**  
   In Search Console, use the **URL-prefix** property **`https://fxsentinel.io`** (not `http://`). Submit the sitemap and request indexing for **`https://fxsentinel.io/`** and other **https** URLs only.

2. **Don’t try to “fix” the HTTP URL**  
   You do **not** want `http://fxsentinel.io/` indexed. You want only `https://fxsentinel.io/` in the index. The redirect is correct; no code change is needed. The codebase already uses `https://fxsentinel.io` everywhere (canonical, sitemap, OG, links).

3. **If you have an HTTP property**  
   If you added `http://fxsentinel.io` as a separate property, you can leave it; the “Page with redirect” report there is expected. Or remove that property and use only **`https://fxsentinel.io`**.

4. **Request indexing for the HTTPS URL**  
   In the **https** property: URL Inspection → enter **`https://fxsentinel.io/`** → **Request indexing**. That is the URL that should be indexed; the HTTP one will keep showing as “Page with redirect” and that’s fine.

**Summary:** The message is about the **http** URL. Rely on the **https** property and request indexing for **https://fxsentinel.io/** (and other https URLs). No code changes required.

---

## 5. “Why pages aren’t indexed” – the three reasons you see

GSC shows **Reason**, **Source**, and **Pages** for each issue. Here’s what each means and what to do.

### Blocked by robots.txt (1 page) — *Source: Website*

**Meaning:** Google found a URL (e.g. from a link on your site), tried to crawl it, and your `robots.txt` disallows it.

**Your setup:** You disallow only `/trial-welcome`, `/auth-redirect`, and `/forgot-password`. So the 1 page is almost certainly one of those (e.g. Login links to `/forgot-password`, so Google discovers it and is then blocked).

**Action:** **None.** You want those URLs blocked from indexing. No sitemap or code change.

---

### Discovered – currently not indexed (5 pages) — *Source: Google systems*

**Meaning:** Google knows the URL (sitemap or links) but hasn’t crawled it yet, or hasn’t decided to index it. Common for newer or lower-priority URLs.

**Action:** No code fix. In GSC use **URL Inspection** for the URLs you care about (e.g. homepage, blog, key posts) and click **Request indexing**. Over time more may get crawled and indexed.

---

### Crawled – currently not indexed (4 pages) — *Source: Google systems*

**Meaning:** Google crawled the page but chose not to add it to the index (e.g. thin/duplicate content, or lower value in their view).

**Action:** No sitemap change. Ensure those pages have unique titles and meta descriptions (you already use `useMeta`). Use **Request indexing** for important ones; for the rest, improving content and internal links can help over time.

---

**Summary:** The 1 “Blocked by robots.txt” is intentional. The 5 “Discovered” and 4 “Crawled” are Google’s normal behavior; request indexing for priority URLs and keep content strong.

---

## 6. Gaps and maintenance

| Gap | Action |
|-----|--------|
| **GSC verification** | Add `<meta name="google-site-verification" content="…">` in `index.html` if you use HTML tag method; otherwise ensure DNS/GA is set. |
| **api/sitemap.js** | Kept in sync with `public/sitemap.xml` (same URLs, no `/terms`, same `lastmod`). Static `public/sitemap.xml` is what GSC uses unless you rewrite to the API. |
| **Sitelinks** | Sitelinks are chosen by Google; you can’t force them in GSC. You already have BreadcrumbList and good internal links; keep structure clear and wait for recrawls. |
| **favicon / og-image** | Ensure `public/favicon.png` and `public/og-image.png` exist and load at `https://fxsentinel.io/...` (see `docs/2026_SEO_and _GEO to-do.md`). |

---

## 7. File reference

| Purpose | Files |
|--------|--------|
| Sitemap & robots | `public/sitemap.xml`, `public/robots.txt`, `api/sitemap.js`, `api/robots.js` |
| Canonical | `index.html` (default), `src/hooks/useCanonicalTag.js`, `src/hooks/useRouteTracking.js` |
| Meta & title | `index.html`, `src/hooks/useMeta.js`, each page component |
| Structured data | `index.html` (Organization, WebApplication, FAQPage, BreadcrumbList), `src/components/BlogPost.jsx` (BlogPosting) |
| GSC / indexing | `docs/GOOGLE_SEARCH_CONSOLE_INDEXING.md`, `docs/CANONICAL_TAG_FIX.md` |
| SEO to-dos | `docs/2026_SEO_and _GEO to-do.md`, `docs/SEO_FULL_AUDIT_CHECKLIST.md` |

---

## 8. Quick GSC checklist

- [ ] Property verified (HTML tag, DNS, or GA).
- [ ] Sitemap submitted: `https://fxsentinel.io/sitemap.xml`.
- [ ] “Pages” and “Why pages aren’t indexed” reviewed.
- [ ] Request indexing for key URLs after changes.
- [ ] Re-submit sitemap after large URL/meta updates.
