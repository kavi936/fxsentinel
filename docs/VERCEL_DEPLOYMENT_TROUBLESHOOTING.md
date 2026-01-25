# Vercel Deployment Troubleshooting Guide

## Issue: Git Push Not Triggering Vercel Deployment

If your git pushes aren't automatically triggering Vercel deployments, follow these steps:

### 1. Check Vercel Project Settings

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Select your `fxsentinel` project
3. Go to **Settings** → **Git**
4. Verify:
   - ✅ Repository is connected: `kavi936/fxsentinel`
   - ✅ Production Branch: `main`
   - ✅ Auto-deploy is enabled

### 2. Check GitHub Webhook

1. Go to your GitHub repository: `https://github.com/kavi936/fxsentinel`
2. Go to **Settings** → **Webhooks**
3. Look for a Vercel webhook
4. If missing or failed:
   - Go back to Vercel Dashboard
   - **Settings** → **Git** → **Disconnect** repository
   - Then **Connect** it again to recreate the webhook

### 3. Verify Build Configuration

In Vercel Dashboard → **Settings** → **General**:
- **Root Directory**: Should be empty (root) or set correctly
- **Build Command**: Should be `npm run build` (or auto-detected)
- **Output Directory**: Should be `dist`
- **Install Command**: Should be `npm install` (or auto-detected)

### 4. Manual Deployment Trigger

If auto-deploy isn't working:

1. Go to Vercel Dashboard → Your Project
2. Click **Deployments** tab
3. Click **Redeploy** on the latest deployment
4. Or click **Deploy** → **Deploy Git Commit** → Select latest commit

### 5. Check Build Logs

1. Go to **Deployments** tab
2. Click on the latest deployment
3. Check **Build Logs** for errors
4. Common issues:
   - Missing environment variables
   - Build command failing
   - Dependencies not installing

### 6. Force Fresh Deployment

If you suspect caching issues:

1. In Vercel Dashboard → **Deployments**
2. Click **...** (three dots) on latest deployment
3. Select **Redeploy**
4. **Uncheck** "Use existing Build Cache" if available
5. Click **Redeploy**

### 7. Verify Files Are in Repository

Check that `sitemap.xml` and `robots.txt` are actually in the repo:

```bash
git ls-files public/sitemap.xml public/robots.txt
```

If they don't show up, they're not tracked. Fix `.gitignore` and commit them.

### 8. Check Vercel CLI (Alternative)

If dashboard isn't working, use Vercel CLI:

```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy
vercel --prod
```

### 9. Common Issues and Fixes

**Issue**: "Build failed" or "No changes detected"
- **Fix**: Make a small change and commit (like updating a comment)

**Issue**: Webhook not receiving events
- **Fix**: Reconnect the GitHub repository in Vercel settings

**Issue**: Wrong branch being deployed
- **Fix**: Check **Settings** → **Git** → **Production Branch** is set to `main`

**Issue**: Files not appearing in deployment
- **Fix**: Verify files are committed to git (not just staged locally)

### 10. Verify Deployment

After deployment, check:
- ✅ `https://fxsentinel.io/sitemap.xml` returns XML (not 404)
- ✅ `https://fxsentinel.io/robots.txt` returns text
- ✅ Build logs show no errors
- ✅ Files appear in deployment preview

## Quick Fix Commands

```bash
# Make sure everything is committed
git add .
git commit -m "Trigger Vercel deployment"
git push origin main

# Then manually trigger in Vercel dashboard or use CLI
vercel --prod
```

## Still Not Working?

1. Check Vercel status: https://www.vercel-status.com/
2. Check GitHub status: https://www.githubstatus.com/
3. Review Vercel documentation: https://vercel.com/docs
4. Contact Vercel support through dashboard

