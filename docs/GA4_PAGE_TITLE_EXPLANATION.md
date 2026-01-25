# GA4 Page Title Confusion - Explanation & Fix

## The Problem

You're seeing multiple page titles for the same landing page in GA4:

1. **"FXSentinel Landing Page"** - 332 views (348.6%)
2. **"FXSentinel - Professional AI Analysis Dashboard | Real-Time Trading Alerts"** - 160 views (321.1%)
3. **"landing_page"** - 158 views (327.0%)

## Why This Happens

### 1. Multiple Title Sources

- **HTML Default Title**: `index.html` has a default title that loads first
- **Analytics Page Name**: Code tracks with `page_name: "landing_page"`
- **GA4 Page Title Dimension**: GA4 uses `document.title` which can change

### 2. The Percentage Over 100%

The percentages (348.6%, 321.1%, etc.) are **comparison metrics**, not actual percentages. GA4 shows:
- Current period views
- Percentage change compared to previous period (year-over-year or period-over-period)

If it says "348.6%", it means:
- **332 views** in current period
- **348.6% more** than the previous period (or 3.486x the previous period)

This is normal and indicates growth, not an error.

## The Fix

I've updated the `LandingPage.jsx` component to set a consistent page title:

```javascript
document.title = 'FXSentinel - AI-Powered Forex Market Analysis | Real-Time Trading Alerts';
```

This ensures:
- ✅ Consistent page title across all tracking
- ✅ Matches your SEO meta tags
- ✅ Cleaner GA4 reports

## What You'll See Going Forward

After this fix:
- **New page views** will use the consistent title
- **Old data** will still show the mixed titles (historical data doesn't change)
- Over time, the consistent title will dominate

## Understanding GA4 Dimensions

### Page Title vs Page Name

- **Page Title** (`page_title`): Uses `document.title` from the browser
- **Page Name** (`page_name`): Custom parameter we send in analytics

In your reports, you can:
1. Use **Page Name** dimension for cleaner data (uses our custom `page_name` parameter)
2. Use **Page Title** dimension to see what users actually see in their browser tab

## Recommendation

For cleaner analytics, use the **Page Name** dimension instead of **Page Title**:
- Go to your report
- Change dimension from "Page title" to "Page name"
- You'll see: `landing_page`, `blog`, `signup`, etc. (cleaner, consistent)

---

**Last Updated**: January 2025

