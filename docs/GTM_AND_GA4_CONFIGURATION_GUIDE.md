# GTM & GA4 Configuration Guide - Post Implementation

> **Date**: January 2025  
> **Status**: Required Configuration Steps  
> **GTM Container**: GTM-M64QPF8Z  
> **GA4 Measurement ID**: G-1QMRKVJD8C

This guide provides step-by-step instructions for configuring Google Tag Manager and Google Analytics 4 to properly capture and report on the enhanced tracking we've implemented.

---

## 🎯 Overview

Your code now pushes events to the `dataLayer`, but GTM needs to be configured to:
1. Capture these dataLayer events
2. Send them to GA4 with proper parameters
3. Map custom parameters to GA4 custom dimensions

GA4 needs to be configured to:
1. Create custom dimensions for UTM parameters and funnel data
2. Set up conversion events
3. Create reports for funnel analysis

---

## Part 1: Google Tag Manager Configuration

### Step 1: Verify GTM Container Setup

1. Go to [tagmanager.google.com](https://tagmanager.google.com)
2. Select your container: **GTM-M64QPF8Z**
3. Verify the container is published and active

---

### Step 2: Create DataLayer Variables

Your code pushes data to `dataLayer`, so we need to create variables to read this data.

#### 2.1 Create UTM Source Variable (from dataLayer)

1. Go to **Variables** → **New**
2. **Variable Name**: `DL - UTM Source`
3. **Variable Type**: `Data Layer Variable`
4. **Data Layer Variable Name**: `utm_source`
5. Click **Save**

#### 2.2 Create UTM Medium Variable

1. **Variable Name**: `DL - UTM Medium`
2. **Variable Type**: `Data Layer Variable`
3. **Data Layer Variable Name**: `utm_medium`
4. Click **Save**

#### 2.3 Create UTM Campaign Variable

1. **Variable Name**: `DL - UTM Campaign`
2. **Variable Type**: `Data Layer Variable`
3. **Data Layer Variable Name**: `utm_campaign`
4. Click **Save**

#### 2.4 Create UTM Content Variable

1. **Variable Name**: `DL - UTM Content`
2. **Variable Type**: `Data Layer Variable`
3. **Data Layer Variable Name**: `utm_content`
4. Click **Save**

#### 2.5 Create UTM Term Variable

1. **Variable Name**: `DL - UTM Term`
2. **Variable Type**: `Data Layer Variable`
3. **Data Layer Variable Name**: `utm_term`
4. Click **Save**

#### 2.6 Create Page Name Variable

1. **Variable Name**: `DL - Page Name`
2. **Variable Type**: `Data Layer Variable`
3. **Data Layer Variable Name**: `page_name`
4. Click **Save**

#### 2.7 Create Funnel Step Variable

1. **Variable Name**: `DL - Funnel Step`
2. **Variable Type**: `Data Layer Variable`
3. **Data Layer Variable Name**: `funnel_step`
4. Click **Save**

#### 2.8 Create Funnel Step Number Variable

1. **Variable Name**: `DL - Funnel Step Number`
2. **Variable Type**: `Data Layer Variable`
3. **Data Layer Variable Name**: `funnel_step_number`
4. Click **Save**

#### 2.9 Create Conversion Type Variable (Optional)

1. **Variable Name**: `DL - Conversion Type`
2. **Variable Type**: `Data Layer Variable`
3. **Data Layer Variable Name**: `conversion_type`
4. Click **Save**

**Note**: This variable is optional. Conversion events may not always push this to dataLayer. You can remove it from tags if not needed.

#### 2.10 Create Conversion Value Variable (Optional)

1. **Variable Name**: `DL - Conversion Value`
2. **Variable Type**: `Data Layer Variable`
3. **Data Layer Variable Name**: `conversion_value`
4. Click **Save**

**Note**: This variable is optional. Conversion events may not always push this to dataLayer. You can remove it from tags if not needed.

---

### Step 3: Update GA4 Configuration Tag

Your existing GA4 Configuration tag needs to be updated to capture custom parameters.

1. Go to **Tags** → Find **GA4 - Configuration** (or create if it doesn't exist)
2. **Tag Type**: `Google Analytics: GA4 Configuration`
3. **Measurement ID**: `G-1QMRKVJD8C`
4. **Configuration Tag**: (leave blank if this is the config tag)

#### 3.1 Add Custom Parameters

Click **Fields to Set** → **Add Row** for each:

| Field Name | Value |
|------------|-------|
| `custom_parameter_1` | `{{DL - UTM Source}}` |
| `custom_parameter_2` | `{{DL - UTM Medium}}` |
| `custom_parameter_3` | `{{DL - UTM Campaign}}` |
| `custom_parameter_4` | `{{DL - UTM Content}}` |
| `custom_parameter_5` | `{{DL - UTM Term}}` |

#### 3.2 Set Trigger

- **Trigger**: `All Pages`
- Click **Save**

---

### Step 4: Create Funnel Step Event Tag

This tag captures the `funnel_step` events pushed to dataLayer.

1. Go to **Tags** → **New**
2. **Tag Name**: `GA4 - Funnel Step`
3. **Tag Type**: `Google Analytics: GA4 Event`
4. **Configuration Tag**: Select `GA4 - Configuration`
5. **Event Name**: `funnel_step`

#### 4.1 Add Event Parameters

Click **Event Parameters** → **Add Row** for each:

| Parameter Name | Value |
|---------------|-------|
| `funnel_step` | `{{DL - Funnel Step}}` |
| `funnel_step_number` | `{{DL - Funnel Step Number}}` |
| `utm_source` | `{{DL - UTM Source}}` |
| `utm_medium` | `{{DL - UTM Medium}}` |
| `utm_campaign` | `{{DL - UTM Campaign}}` |

**Note**: If `DL - Funnel Step Number` variable doesn't exist yet, create it first (see Step 2.8 above).

#### 4.2 Create Custom Trigger

1. Go to **Triggers** → **New**
2. **Trigger Name**: `DataLayer - Funnel Step`
3. **Trigger Type**: `Custom Event`
4. **Event Name**: `funnel_step`
5. Click **Save**

#### 4.3 Assign Trigger to Tag

- Go back to **GA4 - Funnel Step** tag
- **Triggering**: Select `DataLayer - Funnel Step`
- Click **Save**

---

### Step 5: Create Page View Event Tag

This captures page views from dataLayer.

1. Go to **Tags** → **New**
2. **Tag Name**: `GA4 - Page View (DataLayer)`
3. **Tag Type**: `Google Analytics: GA4 Event`
4. **Configuration Tag**: Select `GA4 - Configuration`
5. **Event Name**: `page_view`

#### 5.1 Add Event Parameters

| Parameter Name | Value |
|---------------|-------|
| `page_name` | `{{DL - Page Name}}` |
| `page_location` | `{{Page URL}}` |
| `utm_source` | `{{DL - UTM Source}}` |
| `utm_medium` | `{{DL - UTM Medium}}` |

#### 5.2 Create Trigger

1. Go to **Triggers** → **New**
2. **Trigger Name**: `DataLayer - Page View`
3. **Trigger Type**: `Custom Event`
4. **Event Name**: `page_view`
5. Click **Save**

#### 5.3 Assign Trigger

- Go back to **GA4 - Page View (DataLayer)** tag
- **Triggering**: Select `DataLayer - Page View`
- Click **Save**

---

### Step 6: Create Engagement Event Tag

This captures engagement events (signup clicks, CTA clicks, etc.).

1. Go to **Tags** → **New**
2. **Tag Name**: `GA4 - Engagement Events`
3. **Tag Type**: `Google Analytics: GA4 Event`
4. **Configuration Tag**: Select `GA4 - Configuration`
5. **Event Name**: `{{Event}}` (use built-in Event variable)

#### 6.1 Add Event Parameters

| Parameter Name | Value |
|---------------|-------|
| `event_name` | `{{Event}}` |
| `utm_source` | `{{DL - UTM Source}}` |
| `utm_medium` | `{{DL - UTM Medium}}` |

#### 6.2 Create Trigger

1. Go to **Triggers** → **New**
2. **Trigger Name**: `DataLayer - Engagement Events`
3. **Trigger Type**: `Custom Event`
4. **Event Name**: Use regex matching: `^(signup_click|cta_click|engagement|feature_usage).*`
5. Click **Save**

#### 6.3 Assign Trigger

- Go back to **GA4 - Engagement Events** tag
- **Triggering**: Select `DataLayer - Engagement Events`
- Click **Save**

---

### Step 7: Create Conversion Event Tag

This captures conversion events (signup completion, payment success).

1. Go to **Tags** → **New**
2. **Tag Name**: `GA4 - Conversion Events`
3. **Tag Type**: `Google Analytics: GA4 Event`
4. **Configuration Tag**: Select `GA4 - Configuration`
5. **Event Name**: `{{Event}}`

#### 7.1 Add Event Parameters

| Parameter Name | Value |
|---------------|-------|
| `utm_source` | `{{DL - UTM Source}}` |
| `utm_medium` | `{{DL - UTM Medium}}` |
| `utm_campaign` | `{{DL - UTM Campaign}}` |

**Optional Parameters** (only add if you created these variables):
- `conversion_type` | `{{DL - Conversion Type}}` (optional)
- `conversion_value` | `{{DL - Conversion Value}}` (optional)

**Note**: Conversion events are currently tracked via `funnel_step` events (like `signup_completion`, `payment_success`). The conversion_type and conversion_value parameters are optional and may not always be present in dataLayer. You can safely remove them from this tag if you get errors.

#### 7.2 Create Trigger

1. Go to **Triggers** → **New**
2. **Trigger Name**: `DataLayer - Conversion Events`
3. **Trigger Type**: `Custom Event`
4. **Event Name**: Use regex: `^(conversion|signup_completion|payment_success|trial_start).*`
5. Click **Save**

#### 7.3 Assign Trigger

- Go back to **GA4 - Conversion Events** tag
- **Triggering**: Select `DataLayer - Conversion Events`
- Click **Save**

---

### Step 8: Test GTM Configuration

1. Click **Preview** in GTM
2. Enter your website URL: `https://fxsentinel.io`
3. Navigate through your site and check:
   - ✅ `page_view` events appear in GTM Preview
   - ✅ `funnel_step` events appear
   - ✅ UTM parameters are captured
   - ✅ Events are firing to GA4

4. Check **Tags Fired** section to verify all tags are firing
5. Check **Data Layer** section to see data being pushed

---

## Part 2: Google Analytics 4 Configuration

### Step 1: Create Custom Dimensions

Custom dimensions allow you to analyze data by UTM parameters and funnel steps.

#### 1.1 Create UTM Source Dimension

1. Go to [analytics.google.com](https://analytics.google.com)
2. Select your GA4 property
3. Go to **Admin** (gear icon) → **Custom Definitions** → **Custom Dimensions**
4. Click **Create Custom Dimension**
5. **Dimension Name**: `UTM Source`
6. **Scope**: `Event`
7. **Event Parameter**: `utm_source`
8. **Description**: `Traffic source from UTM parameter or referrer detection`
9. Click **Save**

#### 1.2 Create UTM Medium Dimension

1. Click **Create Custom Dimension**
2. **Dimension Name**: `UTM Medium`
3. **Scope**: `Event`
4. **Event Parameter**: `utm_medium`
5. **Description**: `Traffic medium from UTM parameter or referrer detection`
6. Click **Save**

#### 1.3 Create UTM Campaign Dimension

1. Click **Create Custom Dimension**
2. **Dimension Name**: `UTM Campaign`
3. **Scope**: `Event`
4. **Event Parameter**: `utm_campaign`
5. Click **Save**

#### 1.4 Create Funnel Step Dimension

1. Click **Create Custom Dimension**
2. **Dimension Name**: `Funnel Step`
3. **Scope**: `Event`
4. **Event Parameter**: `funnel_step`
5. **Description**: `Current step in the conversion funnel`
6. Click **Save**

#### 1.5 Create Page Name Dimension

1. Click **Create Custom Dimension**
2. **Dimension Name**: `Page Name`
3. **Scope**: `Event`
4. **Event Parameter**: `page_name`
5. Click **Save**

---

### Step 2: Mark Conversion Events

Mark key events as conversions to track in reports.

1. Go to **Admin** → **Events**
2. Find each event and toggle **Mark as conversion**:

#### Events to Mark as Conversions:

- ✅ `signup_completion` - User completes signup
- ✅ `dashboard_access` - User accesses dashboard
- ✅ `payment_success` - Payment completed
- ✅ `trial_start` - Trial started

---

### Step 3: Create Funnel Exploration Report

1. Go to **Explore** → **Funnel Exploration**
2. Click **Blank** to create new report
3. **Report Name**: `Signup to Dashboard Funnel`

#### 3.1 Add Funnel Steps

Click **Add Step** for each:

1. **Step 1**: 
   - **Step Name**: `Landing Page View`
   - **Event**: `funnel_step`
   - **Filter**: `funnel_step = landing_page_view`

2. **Step 2**:
   - **Step Name**: `Signup Click`
   - **Event**: `funnel_step`
   - **Filter**: `funnel_step = signup_click`

3. **Step 3**:
   - **Step Name**: `Signup Completion`
   - **Event**: `funnel_step`
   - **Filter**: `funnel_step = signup_completion`

4. **Step 4**:
   - **Step Name**: `Auth Redirect`
   - **Event**: `funnel_step`
   - **Filter**: `funnel_step = auth_redirect`

5. **Step 5**:
   - **Step Name**: `Dashboard Access`
   - **Event**: `funnel_step`
   - **Filter**: `funnel_step = dashboard_access`

#### 3.2 Add Breakdown

- Click **Breakdown**
- **Dimension**: `UTM Source`
- This shows conversion rates by traffic source

#### 3.3 Save Report

- Click **Save** in top right
- Name: `Signup to Dashboard Funnel`

---

### Step 4: Create Traffic Source Report

1. Go to **Explore** → **Free Form**
2. Click **Blank** to create new report
3. **Report Name**: `Traffic Source Analysis`

#### 4.1 Add Dimensions

- **Row**: `UTM Source`
- **Column**: `UTM Medium`

#### 4.2 Add Metrics

- **Values**: 
  - `Users`
  - `Sessions`
  - `Conversions` (signup_completion)
  - `Conversion Rate`

#### 4.3 Add Filters

- **Filter**: `UTM Source` contains `google` OR `instagram`
- This shows Google Search vs Instagram performance

#### 4.4 Save Report

- Click **Save**

---

### Step 5: Create Conversion Report

1. Go to **Explore** → **Free Form**
2. Click **Blank**
3. **Report Name**: `Conversion Analysis by Source`

#### 5.1 Add Dimensions

- **Row**: `UTM Source`
- **Column**: `Funnel Step`

#### 5.2 Add Metrics

- **Values**: 
  - `Event Count`
  - `Users`
  - `Conversion Rate`

#### 5.3 Visualization

- Select **Funnel Chart** visualization
- This shows conversion rates at each funnel step by source

#### 5.4 Save Report

- Click **Save**

---

## Part 3: Testing & Verification

### Test 1: Verify DataLayer Events

1. Open your website: `https://fxsentinel.io`
2. Open browser DevTools (F12)
3. Go to **Console**
4. Type: `window.dataLayer`
5. You should see events being pushed:
   ```javascript
   [
     {event: "page_view", page_name: "landing_page", utm_source: "google", ...},
     {event: "funnel_step", funnel_step: "landing_page_view", ...}
   ]
   ```

### Test 2: Verify GTM Preview

1. Open GTM Preview mode
2. Navigate through your site
3. Check **Tags Fired** section:
   - ✅ `GA4 - Configuration` fires on page load
   - ✅ `GA4 - Page View (DataLayer)` fires on page view
   - ✅ `GA4 - Funnel Step` fires on funnel steps
   - ✅ `GA4 - Engagement Events` fires on engagement
   - ✅ `GA4 - Conversion Events` fires on conversions

### Test 3: Verify GA4 Real-Time

1. Go to GA4 → **Reports** → **Real-time**
2. Navigate through your site
3. Check:
   - ✅ Events appear in Real-time (may take 30-60 seconds)
   - ✅ `page_view` events show
   - ✅ `funnel_step` events show
   - ✅ Custom dimensions populated

### Test 4: Test Source Attribution

1. Visit from Google Search:
   - Search for "fxsentinel" on Google
   - Click through to your site
   - Check GA4 Real-time → Should show `utm_source: google, utm_medium: organic`

2. Visit from Instagram:
   - Click link from Instagram bio
   - Check GA4 Real-time → Should show `utm_source: instagram, utm_medium: social`

3. Visit with UTM:
   - Visit: `https://fxsentinel.io/?utm_source=test&utm_medium=email`
   - Check GA4 Real-time → Should show `utm_source: test, utm_medium: email`

---

## Part 4: Common Issues & Troubleshooting

### Issue 1: Events Not Appearing in GA4

**Solution**:
- Check GTM Preview mode - are tags firing?
- Check GA4 Real-time - events may take 30-60 seconds
- Verify GTM container is published
- Check browser console for errors

### Issue 2: UTM Parameters Not Captured

**Solution**:
- Verify dataLayer variables are created correctly
- Check dataLayer in browser console - is `utm_source` present?
- Verify GA4 Configuration tag has custom parameters set

### Issue 3: Funnel Steps Not Tracking

**Solution**:
- Check `funnel_step` events in dataLayer
- Verify `GA4 - Funnel Step` tag is firing in GTM Preview
- Check trigger configuration - event name must match exactly

### Issue 4: Custom Dimensions Not Populated

**Solution**:
- Custom dimensions take 24-48 hours to populate in historical data
- Check Real-time reports - dimensions should appear immediately
- Verify event parameters match dimension names exactly

---

## Part 5: Maintenance & Monitoring

### Weekly Tasks

1. **Check GTM Preview Mode**
   - Verify all tags are firing correctly
   - Check for any errors

2. **Review GA4 Real-time**
   - Verify events are coming through
   - Check source attribution is working

3. **Monitor Funnel Report**
   - Check conversion rates at each step
   - Identify drop-off points

### Monthly Tasks

1. **Review Custom Dimensions**
   - Check data quality
   - Verify dimensions are populated

2. **Update Reports**
   - Add new dimensions if needed
   - Optimize report configurations

3. **Analyze Traffic Sources**
   - Compare Google vs Instagram performance
   - Identify best-performing sources

---

## Quick Reference

### GTM Container
- **Container ID**: `GTM-M64QPF8Z`
- **URL**: [tagmanager.google.com](https://tagmanager.google.com)

### GA4 Property
- **Measurement ID**: `G-1QMRKVJD8C`
- **URL**: [analytics.google.com](https://analytics.google.com)

### Key Events Tracked
- `page_view` - Page views
- `funnel_step` - Funnel progression
- `signup_click` - Signup button clicks
- `signup_completion` - Signup completed
- `auth_redirect` - Auth redirect page
- `dashboard_access` - Dashboard accessed
- `dashboard_first_view` - First dashboard view
- `conversion` - Conversion events

### Key Custom Dimensions
- `UTM Source` - Traffic source
- `UTM Medium` - Traffic medium
- `UTM Campaign` - Campaign name
- `Funnel Step` - Current funnel step
- `Page Name` - Page identifier

---

**Last Updated**: January 2025  
**Status**: Ready for Configuration

