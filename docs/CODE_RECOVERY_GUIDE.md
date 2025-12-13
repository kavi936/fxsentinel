# Code Recovery Guide for FXSentinel

## Overview
This guide will help you recover your code from your live hosted website using browser inspection tools.

## Prerequisites
- Access to your live website URL
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Basic knowledge of browser developer tools

## Method 1: Manual Recovery (Step-by-Step)

### Step 1: Access Your Live Site
1. Open your browser and navigate to your live website
2. Open Developer Tools:
   - **Chrome/Edge**: Press `F12` or `Ctrl+Shift+I` (Windows) / `Cmd+Option+I` (Mac)
   - **Firefox**: Press `F12` or `Ctrl+Shift+I` (Windows) / `Cmd+Option+I` (Mac)
   - **Safari**: Press `Cmd+Option+I` (Mac)

### Step 2: Recover Source Files
1. **Go to Sources Tab**
2. **Look for your source files** in the file tree:
   - Usually under your domain name
   - Look for folders like `src/`, `components/`, `js/`, etc.
3. **For each file you find**:
   - Right-click on the file
   - Select "Copy" or manually select all content (Ctrl+A, Ctrl+C)
   - Paste into a new file locally

### Step 3: Recover CSS Files
1. **In Sources tab**, look for `.css` files
2. **Alternative method**:
   - Go to Elements tab
   - Find your component's element
   - Look at the Styles panel on the right
   - Copy the computed CSS

### Step 4: Recover HTML Structure
1. **Go to Elements tab**
2. **Find your main app container** (usually `<div id="root">`)
3. **Copy the HTML structure** if needed

## Method 2: Using the Recovery Scripts

### Step 1: Run Basic Recovery Script
1. Open your live website
2. Open Developer Tools → Console tab
3. Copy and paste the entire content of `code_recovery_script.js`
4. Press Enter to execute
5. Check the console output for extracted code

### Step 2: Run Advanced React Recovery Script
1. In the same console, copy and paste the entire content of `react_code_recovery.js`
2. Press Enter to execute
3. This will generate a comprehensive JSON report and save it automatically

### Step 3: Extract Specific Components
After running the scripts, you can use these commands in the console:

```javascript
// Extract specific component styles
window.reactRecovery.extractComputedStyles('.dashboard');

// Extract form data
window.reactRecovery.extractFormData();

// Generate a new report
window.reactRecovery.generateRecoveryReport();
```

## Method 3: Network Tab Recovery

### Step 1: Capture Network Requests
1. Go to Network tab in Developer Tools
2. Refresh the page (F5)
3. Look for your source files in the network requests

### Step 2: Download Files
1. **For each source file**:
   - Right-click on the request
   - Select "Save as" or "Copy response"
   - Save with appropriate filename

## Method 4: React DevTools (If Available)

### Step 1: Install React Developer Tools
1. Install the React Developer Tools browser extension
2. Restart your browser

### Step 2: Use React DevTools
1. Open your live site
2. Open Developer Tools
3. Look for "Components" and "Profiler" tabs
4. Use these to inspect React component structure and props

## Recovery Checklist

### Frontend Files to Recover
- [ ] `src/App.jsx`
- [ ] `src/main.jsx`
- [ ] `src/components/Dashboard.jsx`
- [ ] `src/components/Overview.jsx`
- [ ] `src/components/LandingPage.jsx`
- [ ] `src/components/Login.jsx`
- [ ] `src/components/Signup.jsx`
- [ ] `src/components/Markets.jsx`
- [ ] `src/components/Alerts.jsx`
- [ ] `src/components/LiveTicker.jsx`
- [ ] All corresponding `.css` files
- [ ] `src/config/firebase.js`
- [ ] `src/contexts/AuthContext.jsx`
- [ ] `src/hooks/useForexPrices.js`

### Configuration Files to Recover
- [ ] `package.json`
- [ ] `vite.config.js`
- [ ] `vercel.json`
- [ ] `index.html`

### Backend Files to Recover
- [ ] `backend/app.py`
- [ ] `backend/requirements.txt`
- [ ] `api/index.py`
- [ ] `wsgi.py`

## Tips for Successful Recovery

### 1. Start with the Most Important Files
- Begin with your main components (Dashboard, Overview, LandingPage)
- Then move to authentication components
- Finally, recover utility files and configurations

### 2. Verify File Integrity
- After copying each file, check if it looks complete
- Look for missing imports or broken syntax
- Test the recovered code locally

### 3. Handle Minified Code
- If you find minified JavaScript, use a beautifier:
  - Online: https://beautifier.io/
  - Browser extension: "JavaScript Beautifier"

### 4. Recover Assets
- Don't forget to download images, fonts, and other assets
- Check the Network tab for all static files

### 5. Backup Your Recovery
- Save the recovery scripts locally
- Keep the JSON report for reference
- Create a backup of all recovered files

## Common Issues and Solutions

### Issue: Code is Minified
**Solution**: Use a JavaScript beautifier to format the code

### Issue: CSS is Inline
**Solution**: Use the recovery script to extract computed styles

### Issue: React Components Not Visible
**Solution**: Look for the compiled JavaScript bundle in Sources tab

### Issue: Missing Dependencies
**Solution**: Check `package.json` and install missing packages

## Post-Recovery Steps

1. **Test the recovered code locally**
2. **Install dependencies**: `npm install`
3. **Fix any import issues**
4. **Update configuration files** if needed
5. **Test all functionality**
6. **Commit to version control** immediately

## Prevention for Future

1. **Use Git for version control**
2. **Set up automatic backups**
3. **Use cloud storage for important files**
4. **Regular commits and pushes**
5. **Document your deployment process**

## Emergency Contacts

If you need additional help:
- Check your hosting provider's backup options
- Contact your hosting provider's support
- Use version control history if available
- Check for any automated backups

---

**Remember**: Always test recovered code thoroughly before deploying to production!
