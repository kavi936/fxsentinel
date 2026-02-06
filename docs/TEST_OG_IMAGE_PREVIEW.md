# How to Test Your Open Graph Image (1200x630px) Preview

## Quick Test Tools

### Option 1: Open Graph Preview (Multi-Platform) ⭐ RECOMMENDED
**URL**: https://www.opengraph.xyz/

**Steps**:
1. Go to https://www.opengraph.xyz/
2. Enter your URL: `https://fxsentinel.io/`
3. Click "Fetch" or press Enter
4. **You'll see previews for**:
   - Facebook
   - Twitter/X
   - LinkedIn
   - Slack
   - Discord
   - And more

**What to Check**:
- ✅ Image displays correctly (1200x630px)
- ✅ Title shows: "FXSentinel - Smarter Market Dashboard | Powered with AI"
- ✅ Description shows your new description
- ✅ Image URL is correct: `https://fxsentinel.io/og-image.png`

---

### Option 2: Facebook Sharing Debugger (Official)
**URL**: https://developers.facebook.com/tools/debug/

**Steps**:
1. Go to https://developers.facebook.com/tools/debug/
2. **Log in with your Facebook account** (required)
3. Enter URL: `https://fxsentinel.io/`
4. Click **"Debug"**
5. **Click "Scrape Again"** to clear cache and see latest version

**What You'll See**:
- Preview of how link appears on Facebook
- All detected Open Graph tags
- Image preview (should show your 1200x630px dashboard image)
- Any warnings or errors

**Important**: Click "Scrape Again" after making changes to clear Facebook's cache!

---

### Option 3: LinkedIn Post Inspector
**URL**: https://www.linkedin.com/post-inspector/

**Steps**:
1. Go to https://www.linkedin.com/post-inspector/
2. **Log in with LinkedIn** (required)
3. Enter URL: `https://fxsentinel.io/`
4. Click **"Inspect"**

**What You'll See**:
- Preview of how link appears on LinkedIn
- Image preview
- Title and description

**Important**: Click "Inspect" again after changes to refresh cache!

---

### Option 4: Twitter Card Validator
**URL**: https://cards-dev.twitter.com/validator

**Steps**:
1. Go to https://cards-dev.twitter.com/validator
2. **Log in with Twitter/X account** (required)
3. Enter URL: `https://fxsentinel.io/`
4. Click **"Preview card"**

**What You'll See**:
- Preview of Twitter card
- Image preview (summary_large_image format)
- Title and description

---

### Option 5: Meta Tags Checker (Simple)
**URL**: https://metatags.io/

**Steps**:
1. Go to https://metatags.io/
2. Enter URL: `https://fxsentinel.io/`
3. See all meta tags and preview

---

## What to Verify

### ✅ Image Requirements
- **Size**: 1200 x 630 pixels ✓
- **Format**: PNG ✓
- **URL**: `https://fxsentinel.io/og-image.png` ✓
- **Accessible**: Image loads without errors ✓

### ✅ Meta Tags
- **Title**: "FXSentinel - Smarter Market Dashboard | Powered with AI"
- **Description**: "Fundamentals and macroeconomics, simplified for retail traders..."
- **Image**: `https://fxsentinel.io/og-image.png`
- **Image Width**: 1200
- **Image Height**: 630
- **Image Type**: image/png

---

## Troubleshooting

### Image Not Showing?
1. **Check image exists**: Visit `https://fxsentinel.io/og-image.png` directly
2. **Clear cache**: Use "Scrape Again" / "Inspect" buttons
3. **Check URL**: Ensure absolute URL (starts with `https://`)
4. **Check file size**: Should be under 5MB (yours is 431KB ✓)

### Wrong Image Showing?
- Social platforms cache images aggressively
- Use "Scrape Again" / "Inspect" to force refresh
- May take 24 hours for cache to clear naturally

### Image Looks Cropped?
- Some platforms crop images differently
- Twitter: May crop sides slightly (normal)
- Facebook: Usually shows full 1200x630px
- LinkedIn: Usually shows full image

---

## Recommended Testing Order

1. **First**: Use **Open Graph Preview** (opengraph.xyz) - fastest, no login needed
2. **Then**: Test on **Facebook** (Sharing Debugger) - most important platform
3. **Then**: Test on **LinkedIn** (Post Inspector) - professional network
4. **Finally**: Test on **Twitter** (Card Validator) - if you use Twitter

---

## Quick Links

- **Multi-platform**: https://www.opengraph.xyz/
- **Facebook**: https://developers.facebook.com/tools/debug/
- **LinkedIn**: https://www.linkedin.com/post-inspector/
- **Twitter**: https://cards-dev.twitter.com/validator
- **Meta Tags**: https://metatags.io/
