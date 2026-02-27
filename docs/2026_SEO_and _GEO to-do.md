# FXSentinel SEO & GEO To‑Do

> Focus: strengthen search visibility and make FXSentinel easier for AI systems to understand and describe correctly.

---

## 1. Page Titles & Meta Descriptions

- [ ] **Audit existing titles**
  - **Why**: Ensure each route has a unique, descriptive `<title>` so Google understands intent and users see clear snippets.
  - **Tasks**:
    - [ ] List all main routes (`/`, `/blog`, each `/blog/...`, `/login`, `/signup`, `/dashboard`, `/disclaimer`, `/privacy`, `/feedback`).
    - [ ] Document current `document.title` (if any) for each route.

- [ ] **Add/update titles for all key pages**
  - **Why**: Avoid generic or duplicated titles that hurt rankings and CTR.
  - **Tasks**:
    - [ ] Set clear titles for each blog post (e.g. `"AI-Powered News Analysis: The Future of Trading | FXSentinel Blog"`).
    - [ ] Confirm `/login`, `/signup`, `/dashboard` have short, specific titles.

- [ ] **Implement reusable meta description helper**
  - **Why**: Consistent way to add `<meta name="description">` to React pages.
  - **Tasks**:
    - [ ] Create a small hook or utility (e.g. `useMeta`) that can set `title` and `description`.
    - [ ] Use it in landing page, blog index, each blog post, and legal/feedback pages.

---

## 2. Structured Data (Schema.org)

- [ ] **Add `BlogPosting` schema for blog posts**
  - **Why**: Help Google and generative engines treat posts as articles, improving rich results and summaries.
  - **Tasks**:
    - [ ] Decide whether to inject JSON‑LD in `BlogPost` or per‑post component.
    - [ ] Include fields: `headline`, `description`, `datePublished`, `author`, `image` (optional), `mainEntityOfPage`, `url`.
    - [ ] Validate with Google’s Rich Results Test.

- [ ] **Extend schemas with topical info**
  - **Why**: Tie FXSentinel to key concepts like “AI forex news analysis” and “trading macro news”.
  - **Tasks**:
    - [ ] Add `about` / `keywords` fields to blog schemas (e.g. forex trading, economic news, AI market analysis, FXSentinel).
    - [ ] Review existing `Organization` and `WebApplication` JSON‑LD to ensure descriptions match current positioning.

---

## 3. Landing Page Content for GEO

- [ ] **Create a “What is FXSentinel?” section**
  - **Why**: Give generative engines a short, canonical explanation they can quote.
  - **Tasks**:
    - [ ] Add a small section (e.g. near “About”) with 2–3 sentences explaining what FXSentinel is, who it’s for, and the core benefit.
    - [ ] Include a short bullet list: key features (AI news analysis, economic calendar, alerts, dashboard).

- [ ] **Clarify “Who it’s for” and “What it is not”**
  - **Why**: Reduce confusion in AI answers and human understanding.
  - **Tasks**:
    - [ ] Add a line or mini‑block describing ideal users (e.g. beginner–intermediate forex traders, serious macro traders).
    - [ ] Repeat a clear statement that FXSentinel is not a broker, not a copy‑trading or signals provider, and doesn’t guarantee profits.

---

## 4. Internal Linking & Topic Clusters

- [ ] **Add deep links from product sections to blog posts**
  - **Why**: Strengthen topical relevance and help crawlers/LLMs connect features with educational content.
  - **Tasks**:
    - [ ] From “AI analysis” sections, link to the AI news analysis blog post.
    - [ ] From macro/volatility sections, link to relevant posts (central bank decisions, volatility, sentiment).
    - [ ] Ensure footer or sidebar includes at least one link to the blog home.

- [ ] **Plan and grow topic clusters**
  - **Why**: Build authority for specific search and GEO intents.
  - **Tasks**:
    - [ ] Define 2–3 clusters (e.g. “Trading economic news”, “AI for forex”, “Market sentiment & volatility”).
    - [ ] For each cluster, plan 2–3 additional posts and cross‑link between them.

---

## 5. Image & Accessibility Tweaks

- [ ] **Audit image alt text**
  - **Why**: Better accessibility and clearer context for search/AI when images are referenced.
  - **Tasks**:
    - [ ] Review hero, dashboard, and feature images to ensure alt text describes the content (“FXSentinel dashboard with real-time macro alerts”) rather than generic labels.
    - [ ] Leave purely decorative background images with empty or minimal alt where appropriate.

---

## 6. Logos, Favicons & OG Images

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

## 7. Monitoring & Validation

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
