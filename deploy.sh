#!/bin/bash

echo "🚀 FXSentinel MVP Deployment Script"
echo "=================================="

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "❌ Git repository not found. Please initialize git first:"
    echo "   git init"
    echo "   git add ."
    echo "   git commit -m 'Initial commit'"
    echo "   git remote add origin <your-github-repo-url>"
    echo "   git push -u origin main"
    exit 1
fi

# Check if backend requirements.txt exists
if [ ! -f "backend/requirements.txt" ]; then
    echo "📝 Creating requirements.txt for backend..."
    cat > backend/requirements.txt << EOF
Flask==2.3.3
Flask-CORS==4.0.0
requests==2.31.0
beautifulsoup4==4.12.2
openai==0.28.1
gunicorn==21.2.0
python-dotenv==1.0.0
EOF
fi

# Check if frontend is built
if [ ! -d "frontend/dist" ]; then
    echo "🔨 Building frontend..."
    cd frontend
    npm install
    npm run build
    cd ..
fi

echo "✅ Setup complete! Next steps:"
echo ""
echo "1. 🏠 Register domain: fxsentinel.io"
echo "   - Go to namecheap.com or porkbun.com"
echo "   - Search for 'fxsentinel.io'"
echo "   - Register for ~$30-40/year"
echo ""
echo "2. 🚂 Deploy backend on Railway:"
echo "   - Go to railway.app"
echo "   - Connect GitHub repo"
echo "   - Set root directory to 'backend'"
echo "   - Copy the deployment URL"
echo ""
echo "3. 🌐 Deploy frontend on Vercel:"
echo "   - Go to vercel.com"
echo "   - Connect GitHub repo"
echo "   - Add environment variable:"
echo "     VITE_API_URL=https://your-railway-url"
echo ""
echo "4. 🔗 Connect custom domain:"
echo "   - In Vercel, add domain 'fxsentinel.io'"
echo "   - Update DNS records at your registrar"
echo ""
echo "🎯 Your MVP will be live at: https://fxsentinel.io" 