# 🚀 FXSentinel Deployment Guide

Quick deployment options for investor demos and production hosting.

## 🎯 **Recommended: Vercel + Railway (Fastest)**

### Step 1: Deploy Backend (Railway)
1. **Push to GitHub** (if not already done):
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
   - Railway will auto-detect Python/Flask
   - Wait for deployment (2-3 minutes)
   - Copy your backend URL (e.g., `https://your-app.railway.app`)

### Step 2: Deploy Frontend (Vercel)
1. **Go to Vercel**:
   - Visit [vercel.com](https://vercel.com)
   - Sign up with GitHub
   - Click "New Project"
   - Import your GitHub repository

2. **Configure Environment Variables**:
   - In Vercel project settings, add:
   ```
   VITE_API_URL=https://your-app.railway.app
   ```
   (Replace with your actual Railway URL)

3. **Deploy**:
   - Vercel will auto-detect Vite React app
   - Click "Deploy"
   - Get your frontend URL (e.g., `https://your-app.vercel.app`)

### Step 3: Test Your Deployment
- Frontend: `https://your-app.vercel.app`
- Backend API: `https://your-app.railway.app/api/hello`

---

## 🔄 **Alternative: Render (All-in-One)**

### Deploy Both on Render
1. **Frontend (Static Site)**:
   - Go to [render.com](https://render.com)
   - Create new "Static Site"
   - Connect GitHub repo
   - Build command: `cd frontend && npm install && npm run build`
   - Publish directory: `frontend/dist`

2. **Backend (Web Service)**:
   - Create new "Web Service"
   - Connect same GitHub repo
   - Root directory: `backend`
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn app:app`

3. **Set Environment Variables**:
   - In frontend service, add:
   ```
   VITE_API_URL=https://your-backend-service.onrender.com
   ```

---

## 🔄 **Alternative: Netlify + Render**

### Frontend (Netlify)
1. Go to [netlify.com](https://netlify.com)
2. Drag and drop your `frontend/dist` folder (after building)
3. Or connect GitHub for auto-deployment

### Backend (Render)
- Same as above

---

## 🔄 **Alternative: Heroku (Paid but Reliable)**

### Deploy Both on Heroku
1. **Install Heroku CLI**:
   ```bash
   # macOS
   brew tap heroku/brew && brew install heroku
   
   # Or download from heroku.com
   ```

2. **Deploy Backend**:
   ```bash
   cd backend
   heroku create your-app-backend
   git add .
   git commit -m "Deploy backend"
   git push heroku main
   ```

3. **Deploy Frontend**:
   ```bash
   cd frontend
   heroku create your-app-frontend
   # Add buildpack for static sites
   heroku buildpacks:set https://github.com/heroku/heroku-buildpack-static.git
   # Build and deploy
   npm run build
   git add dist
   git commit -m "Add build"
   git push heroku main
   ```

---

## 🛠️ **Local Testing Before Deployment**

### Test Backend
```bash
cd backend
python app.py
# Test: http://localhost:5000/api/hello
```

### Test Frontend
```bash
cd frontend
npm install
npm run dev
# Test: http://localhost:5173
```

### Build Frontend
```bash
cd frontend
npm run build
# Check dist/ folder is created
```

---

## 🔧 **Troubleshooting**

### Common Issues:
1. **CORS Errors**: Backend already has CORS enabled
2. **API Not Found**: Check environment variable `VITE_API_URL`
3. **Build Failures**: Ensure all dependencies are in `package.json`

### Environment Variables:
- **Frontend**: `VITE_API_URL=https://your-backend-url.com`
- **Backend**: No special variables needed for this MVP

---

## 📊 **Performance Tips**

1. **Enable Caching**: Add cache headers to Flask responses
2. **Compress Images**: Optimize any images for web
3. **CDN**: Vercel/Netlify provide global CDN automatically

---

## 🎯 **For Investor Demo**

### Recommended Setup:
1. **Vercel + Railway** (fastest setup)
2. **Custom Domain** (optional but professional)
3. **SSL Certificate** (automatic with Vercel/Railway)

### Demo Checklist:
- ✅ Frontend loads correctly
- ✅ Backend API responds
- ✅ News data displays
- ✅ Analysis popup works
- ✅ Mobile responsive
- ✅ Professional URL

---

## 💰 **Costs**

- **Vercel**: Free tier (unlimited deployments)
- **Railway**: Free tier (limited hours)
- **Render**: Free tier available
- **Netlify**: Free tier (unlimited)
- **Heroku**: $7/month minimum

**Total Cost**: $0-7/month for professional hosting 