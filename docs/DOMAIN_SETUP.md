# 🌐 FXSentinel Domain & Hosting Setup Guide

## 🎯 **Quick Start (Recommended)**

### Step 1: Register Domain
1. **Go to [Namecheap](https://namecheap.com)** or [Porkbun](https://porkbun.com)
2. **Search for**: `fxsentinel.io`
3. **Register for**: ~$30-40/year
4. **Why `.io`**: Perfect for tech/finance apps, professional, memorable

### Step 2: Deploy Backend (Railway)
1. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Prepare for deployment"
   git push origin main
   ```

2. **Deploy on Railway**:
   - Go to [railway.app](https://railway.app)
   - Sign up with GitHub
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Set root directory to `backend`
   - Wait for deployment (2-3 minutes)
   - Copy your backend URL (e.g., `https://fxsentinel-backend.railway.app`)

### Step 3: Deploy Frontend (Vercel)
1. **Go to Vercel**:
   - Visit [vercel.com](https://vercel.com)
   - Sign up with GitHub
   - Click "New Project"
   - Import your GitHub repository

2. **Configure Environment Variables**:
   - In Vercel project settings, add:
   ```
   VITE_API_URL=https://fxsentinel-backend.railway.app
   ```

3. **Deploy**:
   - Vercel will auto-detect Vite React app
   - Click "Deploy"
   - Get your frontend URL (e.g., `https://fxsentinel.vercel.app`)

### Step 4: Connect Custom Domain
1. **In Vercel**:
   - Go to your project settings
   - Click "Domains"
   - Add `fxsentinel.io`
   - Vercel will provide DNS records

2. **In your domain registrar**:
   - Go to DNS settings
   - Add the CNAME record Vercel provided
   - Point `fxsentinel.io` to your Vercel deployment

3. **Optional: Add www subdomain**:
   - Add `www.fxsentinel.io` as well
   - Vercel will handle redirects automatically

## 💰 **Cost Breakdown**

| Service | Cost | Notes |
|---------|------|-------|
| Domain (`fxsentinel.io`) | $30-40/year | One-time annual cost |
| Vercel (Frontend) | **FREE** | Unlimited deployments, custom domains |
| Railway (Backend) | **FREE** | Limited hours, sufficient for MVP |
| **Total** | **$30-40/year** | Professional hosting for MVP |

## 🚀 **Why This Setup is Perfect**

### ✅ **Professional**
- Custom domain looks credible to investors
- SSL certificate included automatically
- Global CDN for fast loading

### ✅ **Scalable**
- Can easily upgrade as you grow
- No vendor lock-in
- Enterprise-grade infrastructure

### ✅ **Cost-Effective**
- Nearly free hosting for MVP stage
- Only domain cost (~$3-4/month)
- No hidden fees

### ✅ **Developer-Friendly**
- Automatic deployments from GitHub
- Easy environment variable management
- Built-in monitoring and analytics

## 🔧 **Alternative Options**

### **Option 2: Render (All-in-One)**
- **Pros**: Single platform, easy setup
- **Cons**: Slower cold starts, less reliable
- **Cost**: Free tier available

### **Option 3: Netlify + Railway**
- **Pros**: Netlify has great static hosting
- **Cons**: Two platforms to manage
- **Cost**: Free tier available

### **Option 4: Heroku**
- **Pros**: Very reliable, great documentation
- **Cons**: $7/month minimum cost
- **Cost**: $7-14/month

## 🛠️ **Technical Details**

### **Frontend (Vercel)**
- **Framework**: React + Vite
- **Build Command**: `npm run build`
- **Output Directory**: `frontend/dist`
- **Environment Variables**: `VITE_API_URL`

### **Backend (Railway)**
- **Framework**: Flask (Python)
- **Requirements**: `requirements.txt`
- **Start Command**: `gunicorn app:app`
- **Port**: Railway auto-assigns

### **Domain Configuration**
- **A Record**: Points to Vercel's servers
- **CNAME**: `www` subdomain
- **SSL**: Automatic with Vercel
- **DNS Propagation**: 24-48 hours

## 🔍 **Testing Your Setup**

### **1. Test Backend API**
```bash
curl https://fxsentinel-backend.railway.app/api/hello
# Should return: {"message": "Hello from FXSentinel API!"}
```

### **2. Test Frontend**
- Visit: `https://fxsentinel.io`
- Should load the React app
- Check browser console for API calls

### **3. Test API Integration**
- Go to Dashboard
- Check if news data loads
- Test AI analysis feature

## 🚨 **Common Issues & Solutions**

### **CORS Errors**
- **Cause**: Frontend can't reach backend
- **Solution**: Check `VITE_API_URL` environment variable

### **Domain Not Working**
- **Cause**: DNS propagation delay
- **Solution**: Wait 24-48 hours, check DNS settings

### **Build Failures**
- **Cause**: Missing dependencies
- **Solution**: Check `package.json` and `requirements.txt`

### **API Timeouts**
- **Cause**: Railway free tier limitations
- **Solution**: Upgrade to paid plan if needed

## 📈 **Scaling Up**

### **When to Upgrade**
- **Railway**: When you exceed free tier hours
- **Vercel**: When you need more bandwidth
- **Domain**: When you want additional features

### **Upgrade Path**
1. **Railway Pro**: $5/month for unlimited hours
2. **Vercel Pro**: $20/month for team features
3. **Additional Domains**: $10-20/year each

## 🎯 **MVP Checklist**

- [ ] Domain registered (`fxsentinel.io`)
- [ ] Backend deployed on Railway
- [ ] Frontend deployed on Vercel
- [ ] Custom domain connected
- [ ] SSL certificate active
- [ ] API integration working
- [ ] Mobile responsive
- [ ] Professional URL active

## 🚀 **Next Steps After Setup**

1. **Set up monitoring**: Vercel and Railway provide basic analytics
2. **Configure backups**: GitHub serves as your backup
3. **Set up CI/CD**: Already configured with GitHub integration
4. **Add analytics**: Google Analytics or similar
5. **Set up error tracking**: Sentry or similar

---

**🎉 Congratulations! Your MVP is now live at https://fxsentinel.io** 