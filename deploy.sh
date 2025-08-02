#!/bin/bash

# 🚀 FXSentinel Deployment Script
echo "🚀 Starting FXSentinel deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if git is initialized
if [ ! -d ".git" ]; then
    print_error "Git repository not found. Please initialize git first:"
    echo "git init"
    echo "git add ."
    echo "git commit -m 'Initial commit'"
    exit 1
fi

# Build frontend
print_status "Building frontend..."
cd frontend
if npm run build; then
    print_status "Frontend build successful!"
else
    print_error "Frontend build failed!"
    exit 1
fi
cd ..

# Check backend dependencies
print_status "Checking backend dependencies..."
cd backend
if [ -f "requirements.txt" ]; then
    print_status "requirements.txt found"
else
    print_error "requirements.txt not found in backend directory"
    exit 1
fi

if [ -f "Procfile" ]; then
    print_status "Procfile found"
else
    print_error "Procfile not found in backend directory"
    exit 1
fi
cd ..

print_status "✅ All checks passed! Your app is ready for deployment."

echo ""
echo "🎯 Next steps:"
echo "1. Push to GitHub:"
echo "   git add ."
echo "   git commit -m 'Prepare for deployment'"
echo "   git push origin main"
echo ""
echo "2. Deploy backend on Railway:"
echo "   - Go to railway.app"
echo "   - Connect your GitHub repo"
echo "   - Set root directory to 'backend'"
echo ""
echo "3. Deploy frontend on Vercel:"
echo "   - Go to vercel.com"
echo "   - Import your GitHub repo"
echo "   - Add environment variable: VITE_API_URL=https://your-railway-url.com"
echo ""
echo "📖 See DEPLOYMENT.md for detailed instructions" 