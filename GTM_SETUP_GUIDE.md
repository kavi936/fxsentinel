# Google Tag Manager Setup Guide for FXSentinel

## 🎯 Overview

This guide will walk you through setting up Google Tag Manager (GTM) for FXSentinel. GTM will replace the direct GA4 implementation while maintaining all existing functionality and adding enhanced tracking capabilities.

## 📋 Prerequisites

1. **Google Account**: You need a Google account to access GTM
2. **GA4 Property**: Your existing GA4 property (G-1QMRKVJD8C) will be used
3. **Website Access**: Ability to update your website code (already done)

## 🚀 Step 1: Create GTM Container

### 1.1 Access Google Tag Manager
1. Go to [tagmanager.google.com](https://tagmanager.google.com)
2. Sign in with your Google account
3. Click **"Create Account"** if you don't have one

### 1.2 Create Account & Container
1. **Account Name**: `FXSentinel`
2. **Container Name**: `FXSentinel Website`
3. **Target Platform**: `Web`
4. Click **"Create"**

### 1.3 Accept Terms & Get Container ID
1. Accept the terms of service
2. Copy your **Container ID** (format: `GTM-XXXXXXX`)
3. **Important**: Replace `GTM-XXXXXXX` in your `index.html` file with your actual container ID

## 🔧 Step 2: Configure GA4 Tag

### 2.1 Create GA4 Configuration Tag
1. In GTM, go to **Tags** → **New**
2. **Tag Name**: `GA4 - Configuration`
3. **Tag Type**: `Google Analytics: GA4 Configuration`
4. **Measurement ID**: `G-1QMRKVJD8C` (your existing GA4 ID)

### 2.2 Configure GA4 Settings
1. **Measurement ID**: `G-1QMRKVJD8C`
2. **Send Page View**: ✅ Checked
3. **Advanced Settings** → **Fields to Set**:
   ```
   page_title: FXSentinel Landing Page
   ```
4. **Custom Parameters**:
   ```
   custom_parameter_1: {{UTM Source}}
   custom_parameter_2: {{UTM Medium}}
   custom_parameter_3: {{UTM Campaign}}
   custom_parameter_4: {{UTM Content}}
   custom_parameter_5: {{UTM Term}}
   ```

### 2.3 Set Trigger
1. **Trigger**: `All Pages`
2. Click **"Save"**

## 📊 Step 3: Create UTM Variable Triggers

### 3.1 Create UTM Variables
Create these **Variables** in GTM:

#### UTM Source Variable
1. **Variable Name**: `UTM Source`
2. **Variable Type**: `URL`
3. **Component Type**: `Query`
4. **Query Key**: `utm_source`

#### UTM Medium Variable
1. **Variable Name**: `UTM Medium`
2. **Variable Type**: `URL`
3. **Component Type**: `Query`
4. **Query Key**: `utm_medium`

#### UTM Campaign Variable
1. **Variable Name**: `UTM Campaign`
2. **Variable Type**: `URL`
3. **Component Type**: `Query`
4. **Query Key**: `utm_campaign`

#### UTM Content Variable
1. **Variable Name**: `UTM Content`
2. **Variable Type**: `URL`
3. **Component Type**: `Query`
4. **Query Key**: `utm_content`

#### UTM Term Variable
1. **Variable Name**: `UTM Term`
2. **Variable Type**: `URL`
3. **Component Type**: `Query`
4. **Query Key**: `utm_term`

## 🎯 Step 4: Enhanced Event Tracking

### 4.1 Signup Button Click Tracking
1. **Tag Name**: `GA4 - Signup Click`
2. **Tag Type**: `Google Analytics: GA4 Event`
3. **Configuration Tag**: `GA4 - Configuration`
4. **Event Name**: `signup_click`
5. **Parameters**:
   ```
   button_location: {{Click Text}}
   page_location: {{Page URL}}
   ```
6. **Trigger**: `Click - All Elements` with condition: `Click Text contains "Sign Up"`

### 4.2 Trial Start Tracking
1. **Tag Name**: `GA4 - Trial Start`
2. **Tag Type**: `Google Analytics: GA4 Event`
3. **Configuration Tag**: `GA4 - Configuration`
4. **Event Name**: `trial_start`
5. **Parameters**:
   ```
   trial_type: free
   user_source: {{UTM Source}}
   ```
6. **Trigger**: Custom trigger when trial is initiated

### 4.3 Payment Attempt Tracking
1. **Tag Name**: `GA4 - Payment Attempt`
2. **Tag Type**: `Google Analytics: GA4 Event`
3. **Configuration Tag**: `GA4 - Configuration`
4. **Event Name**: `payment_attempt`
5. **Parameters**:
   ```
   payment_method: {{Payment Method}}
   amount: {{Payment Amount}}
   ```
6. **Trigger**: Custom trigger when payment is attempted

### 4.4 Payment Success Tracking
1. **Tag Name**: `GA4 - Payment Success`
2. **Tag Type**: `Google Analytics: GA4 Event`
3. **Configuration Tag**: `GA4 - Configuration`
4. **Event Name**: `purchase`
5. **Parameters**:
   ```
   transaction_id: {{Transaction ID}}
   value: {{Payment Amount}}
   currency: USD
   ```
6. **Trigger**: Custom trigger when payment succeeds

## 🔍 Step 5: Custom Event Tracking

### 5.1 Economic Calendar View
1. **Tag Name**: `GA4 - Calendar View`
2. **Tag Type**: `Google Analytics: GA4 Event`
3. **Configuration Tag**: `GA4 - Configuration`
4. **Event Name**: `calendar_view`
5. **Trigger**: Custom trigger when calendar is viewed

### 5.2 News Alert Click
1. **Tag Name**: `GA4 - News Alert Click`
2. **Tag Type**: `Google Analytics: GA4 Event`
3. **Configuration Tag**: `GA4 - Configuration`
4. **Event Name**: `news_alert_click`
5. **Parameters**:
   ```
   news_source: {{News Source}}
   alert_type: {{Alert Type}}
   ```
6. **Trigger**: Custom trigger when news alert is clicked

## 🧪 Step 6: Testing & Validation

### 6.1 Preview Mode
1. Click **"Preview"** in GTM
2. Enter your website URL: `https://fxsentinel.io`
3. Test the following actions:
   - Page load
   - Signup button click
   - UTM parameter tracking
   - Any custom events

### 6.2 Verify GA4 Data
1. Go to your GA4 property
2. Check **Real-time** reports
3. Verify events are firing correctly
4. Confirm UTM parameters are being tracked

### 6.3 Debug Mode
1. Install **Google Tag Assistant** browser extension
2. Test your website with the extension
3. Verify all tags are firing as expected

## 📈 Step 7: Advanced Configuration

### 7.1 Custom JavaScript Variables
For complex tracking, you can create custom JavaScript variables:

```javascript
// Example: User Type Detection
function() {
  var userType = 'guest';
  if ({{User Logged In}}) {
    userType = 'registered';
  }
  if ({{User Has Subscription}}) {
    userType = 'subscriber';
  }
  return userType;
}
```

### 7.2 Data Layer Events
Push custom events to the data layer from your React app:

```javascript
// In your React components
window.dataLayer.push({
  'event': 'custom_event',
  'event_category': 'user_engagement',
  'event_action': 'feature_used',
  'event_label': 'economic_calendar'
});
```

## 🔧 Step 8: Maintenance & Updates

### 8.1 Regular Monitoring
- Check GTM container health monthly
- Monitor tag firing rates
- Review error logs in GTM

### 8.2 Adding New Tracking
1. Create new tags in GTM
2. Test in preview mode
3. Publish changes
4. Verify in GA4

### 8.3 Version Control
- Create versions before major changes
- Use descriptive version names
- Keep backup of working configurations

## 🚨 Troubleshooting

### Common Issues:

**1. Tags Not Firing**
- Check trigger conditions
- Verify variables are set correctly
- Use preview mode to debug

**2. GA4 Data Missing**
- Confirm measurement ID is correct
- Check if GA4 configuration tag is firing
- Verify GA4 property settings

**3. UTM Parameters Not Tracking**
- Ensure UTM variables are created
- Check URL format is correct
- Verify custom parameters in GA4 tag

**4. Performance Issues**
- Limit number of active tags
- Use efficient triggers
- Monitor page load times

## 📞 Support

If you encounter issues:
1. Check GTM's built-in debugging tools
2. Use Google Tag Assistant
3. Review GTM documentation
4. Test in preview mode before publishing

## ✅ Checklist

- [ ] GTM container created
- [ ] Container ID updated in HTML
- [ ] GA4 configuration tag created
- [ ] UTM variables configured
- [ ] Enhanced event tracking set up
- [ ] Preview mode tested
- [ ] GA4 data verified
- [ ] Production deployment completed

---

**Remember**: Always test in preview mode before publishing changes to production. This ensures your tracking continues to work while you make improvements.
