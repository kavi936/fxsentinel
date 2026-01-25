# GTM & GA4 Configuration - Quick Checklist

> **Quick Reference**: What needs to be configured after code implementation

## ✅ What's Already Done (Code)

- ✅ Enhanced source attribution (Google Search, Instagram detection)
- ✅ Complete funnel tracking (all steps from landing to dashboard)
- ✅ DataLayer events pushing to GTM
- ✅ GTM container installed (GTM-M64QPF8Z)
- ✅ Firebase Analytics tracking

## 🔧 What You Need to Configure

### Google Tag Manager (GTM) - Required

#### Step 1: Create DataLayer Variables (5-10 minutes)
- [ ] `DL - UTM Source` (DataLayer Variable: `utm_source`)
- [ ] `DL - UTM Medium` (DataLayer Variable: `utm_medium`)
- [ ] `DL - UTM Campaign` (DataLayer Variable: `utm_campaign`)
- [ ] `DL - UTM Content` (DataLayer Variable: `utm_content`)
- [ ] `DL - UTM Term` (DataLayer Variable: `utm_term`)
- [ ] `DL - Page Name` (DataLayer Variable: `page_name`)
- [ ] `DL - Funnel Step` (DataLayer Variable: `funnel_step`)

#### Step 2: Update/Create GA4 Configuration Tag (5 minutes)
- [ ] Verify GA4 Configuration tag exists
- [ ] Add custom parameters mapping UTM variables
- [ ] Set trigger to "All Pages"

#### Step 3: Create Event Tags (15-20 minutes)
- [ ] `GA4 - Funnel Step` tag (captures funnel_step events)
- [ ] `GA4 - Page View (DataLayer)` tag (captures page_view events)
- [ ] `GA4 - Engagement Events` tag (captures engagement events)
- [ ] `GA4 - Conversion Events` tag (captures conversion events)

#### Step 4: Test GTM (5 minutes)
- [ ] Use GTM Preview mode
- [ ] Verify all tags are firing
- [ ] Check dataLayer is populated

**Total GTM Time**: ~30-40 minutes

---

### Google Analytics 4 (GA4) - Required

#### Step 1: Create Custom Dimensions (10 minutes)
- [ ] `UTM Source` (Event parameter: `utm_source`)
- [ ] `UTM Medium` (Event parameter: `utm_medium`)
- [ ] `UTM Campaign` (Event parameter: `utm_campaign`)
- [ ] `Funnel Step` (Event parameter: `funnel_step`)
- [ ] `Page Name` (Event parameter: `page_name`)

#### Step 2: Mark Conversion Events (5 minutes)
- [ ] `signup_completion` → Mark as conversion
- [ ] `dashboard_access` → Mark as conversion
- [ ] `payment_success` → Mark as conversion
- [ ] `trial_start` → Mark as conversion

#### Step 3: Create Reports (15-20 minutes)
- [ ] **Funnel Exploration Report**: Signup to Dashboard Funnel
  - Steps: landing_page_view → signup_click → signup_completion → auth_redirect → dashboard_access
- [ ] **Traffic Source Report**: Google vs Instagram performance
- [ ] **Conversion Report**: Conversion rates by source

**Total GA4 Time**: ~30-40 minutes

---

## 🎯 Priority Order

### Must Do First (Critical)
1. ✅ Create DataLayer Variables in GTM
2. ✅ Update GA4 Configuration Tag
3. ✅ Create Funnel Step Event Tag
4. ✅ Test in GTM Preview mode

### Should Do Next (Important)
5. ✅ Create Custom Dimensions in GA4
6. ✅ Mark Conversion Events
7. ✅ Create Funnel Exploration Report

### Nice to Have (Can Wait)
8. ✅ Create additional event tags
9. ✅ Create Traffic Source Report
10. ✅ Create Conversion Report

---

## 📊 How to Verify It's Working

### Quick Test (5 minutes)

1. **Open GTM Preview**:
   - Go to tagmanager.google.com
   - Click "Preview"
   - Enter: `https://fxsentinel.io`
   - Navigate through site
   - ✅ Check "Tags Fired" section shows events

2. **Check GA4 Real-time**:
   - Go to analytics.google.com
   - Reports → Real-time
   - Navigate through site
   - ✅ Check events appear (may take 30-60 seconds)

3. **Test Source Attribution**:
   - Visit from Google Search → Should show `source: google, medium: organic`
   - Visit from Instagram → Should show `source: instagram, medium: social`

---

## 📚 Full Documentation

For detailed step-by-step instructions, see:
- **`docs/GTM_AND_GA4_CONFIGURATION_GUIDE.md`** - Complete configuration guide

---

## ⚠️ Common Mistakes to Avoid

1. **Don't forget to publish GTM container** after making changes
2. **Don't create duplicate tags** - check if tags already exist
3. **Custom dimensions take 24-48 hours** to populate in historical data (Real-time works immediately)
4. **Event parameter names must match exactly** - case sensitive
5. **Test in Preview mode first** before publishing

---

## 🆘 Need Help?

If you get stuck:
1. Check GTM Preview mode for errors
2. Check browser console (F12) for JavaScript errors
3. Verify dataLayer is populated: `window.dataLayer` in console
4. Check GA4 Real-time reports (events appear faster than standard reports)

---

**Estimated Total Time**: 60-80 minutes  
**Difficulty**: Medium (follow the guide step-by-step)

