# FXSentinel SEO & GEO To‑Do

> Focus: strengthen search visibility and make FXSentinel easier for AI systems to understand and describe correctly.

**Implemented (Feb 2026):** useMeta hook + titles/descriptions on all key pages, BlogPosting schema on blog posts, “What is FXSentinel?” section + “Who it’s for” / “What it’s not”, deep links from feature cards to blog posts, improved alt text on hero/features images. Remaining items are manual (assets, validation) or ongoing (topic clusters, monitoring).

---

## 1. Page Titles & Meta Descriptions

- [x] **Audit existing titles**
  - **Why**: Ensure each route has a unique, descriptive `<title>` so Google understands intent and users see clear snippets.
  - **Done**: All main routes now set title via `useMeta` (see below).

- [x] **Add/update titles for all key pages**
  - **Why**: Avoid generic or duplicated titles that hurt rankings and CTR.
  - **Done**: Landing, Blog, each blog post (`Title | FXSentinel Blog`), Login, Signup, Dashboard, Disclaimer, Privacy, Feedback all use unique titles.

- [x] **Implement reusable meta description helper**
  - **Why**: Consistent way to add `<meta name="description">` to React pages.
  - **Done**: `src/hooks/useMeta.js` created; used on landing, blog, blog posts, login, signup, dashboard, disclaimer, privacy, feedback.

---

## 2. Structured Data (Schema.org)

- [x] **Add `BlogPosting` schema for blog posts**
  - **Why**: Help Google and generative engines treat posts as articles, improving rich results and summaries.
  - **Done**: `BlogPost` injects JSON‑LD with `headline`, `description`, `datePublished`, `author`, `mainEntityOfPage`, `url`, `articleSection`, `keywords`. Validate with [Google Rich Results Test](https://search.google.com/test/rich-results) after deploy.

- [x] **Extend schemas with topical info**
  - **Why**: Tie FXSentinel to key concepts like “AI forex news analysis” and “trading macro news”.
  - **Done**: Blog schemas include `keywords` and `articleSection`. Home page `Organization` / `WebApplication` already match positioning; review periodically.

---

## 3. Landing Page Content for GEO

- [x] **Create a “What is FXSentinel?” section**
  - **Why**: Give generative engines a short, canonical explanation they can quote.
  - **Done**: New section `#what-is-fxsentinel` before About with 2–3 sentences, bullet list (AI analysis, economic calendar, alerts, dashboard).

- [x] **Clarify “Who it’s for” and “What it is not”**
  - **Why**: Reduce confusion in AI answers and human understanding.
  - **Done**: Same section includes “Who it’s for” (beginner–experienced retail forex traders) and “What we’re not” (not a broker/signals provider; no profit guarantees).

---

## 4. Internal Linking & Topic Clusters

- [x] **Add deep links from product sections to blog posts**
  - **Why**: Strengthen topical relevance and help crawlers/LLMs connect features with educational content.
  - **Done**: Each feature card has a “Learn more →” link: Never Miss Events → central-bank-decisions; Understand the Why → ai-powered-news-analysis; Get Alerts → turning-news-actionable-signals; Focus on Trades → understanding-forex-market-sentiment. Footer already links to Blog.

- [x] **Plan and grow topic clusters** *(started 2026-06-03)*
  - **Why**: Build authority for specific search and GEO intents.
  - **Done (cycle 1):** Cluster “Trading economic news + AI for forex” — 3 posts published, cross-linked. Workflow: `docs/BLOG_SEO_GEO_WORKFLOW.md`.
  - **Tasks (next cycle ~2026-08):**
    - [ ] Macro & volatility cluster (2–3 posts) or comparison-style calendar post.
    - [ ] Cross-link from older 2025 posts to new 2026 cluster where relevant.

---

## 5. Image & Accessibility Tweaks

- [x] **Audit image alt text**
  - **Why**: Better accessibility and clearer context for search/AI when images are referenced.
  - **Done**: Hero features image and phone mockup alt text updated to descriptive copy (“FXSentinel dashboard with real-time economic calendar, AI analysis, and macro alerts”; “FXSentinel instant Telegram alerts with AI analysis on iPhone”). Optionally review remaining images (data logos, decorative) for empty/minimal alt where appropriate.

---

## 6. Logos, Favicons & OG Images *(manual)*

- [ ] **Add and verify `public/favicon.png`**
  - **Why**: All favicon links, manifest icons, and schema `logo` fields point to `/favicon.png`, but the file is missing from `public/`, so the favicon and app icons can 404.
  - **Tasks**:
    - [ ] Export a square PNG logo (at least 48×48, ideally 512×512) and save it as `public/favicon.png`.
    - [ ] Keep the background and contrast consistent with the brand so it looks good at tiny sizes.
    - [ ] After deploy, visit `https://fxsentinel.io/favicon.png` directly to confirm it loads.

- [ ] **Add and verify `public/og-image.png`**
  - **Why**: Social/OG meta tags reference `https://fxsentinel.io/og-image.png`, and Vercel headers are configured, but the file is not present in `public/`, so rich link previews can break.
  - **Tasks**:
    - [ ] Export a 1200×630 PNG hero image and save it as `public/og-image.png`.
    - [ ] Optimize it (compress) so it’s under ~300–400 KB without obvious artifacts.
    - [ ] After deploy, test `https://fxsentinel.io/og-image.png` and use a preview tool (e.g. X/Twitter, LinkedIn, or Meta debugger) to confirm the correct image appears.

- [ ] **Ensure app logos and hero images exist and are optimized**
  - **Why**: Components import logo and hero assets (e.g. `fxsentinel_logo_nobg.(png|webp)`, `IMG_8110-portrait.png`, `FXSentinelFeaturesGlance.png`), but these files are not currently in `src/assets/`, and large uncompressed images can slow the landing page.
  - **Tasks**:
    - [ ] Add the missing image files into `src/assets/` with the exact names used by imports.
    - [ ] Export each image at sensible dimensions (no larger than needed on screen) and compress them (PNG/WebP).
    - [ ] Keep `loading="lazy"` on non-critical images (phone mockup, dashboard preview, data logos) to reduce initial load.
    - [ ] After a local build, verify that all image imports resolve and that no 404s appear in the browser network tab.

---

## 7. Monitoring & Validation *(ongoing)*

- [ ] **Validate SEO changes**
  - **Why**: Catch issues early and confirm Google sees what you expect.
  - **Tasks**:
    - [ ] Run updated pages through Lighthouse / PageSpeed Insights.
    - [ ] Re‑submit sitemap in Google Search Console after significant URL/meta updates.

- [ ] **Monitor GEO behavior over time**
  - **Why**: See how models are actually describing FXSentinel.
  - **Tasks**:
    - [ ] Periodically query major LLMs about “What is FXSentinel?” and “tools for AI‑powered forex news analysis”.
    - [ ] Adjust wording on landing/blog/FAQ if answers seem to miss or misstate your positioning.
