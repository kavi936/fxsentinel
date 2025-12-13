#!/bin/bash

# FXSentinel Development Server Startup Script
echo "🚀 Starting FXSentinel development servers..."

# Function to check if a port is in use
check_port() {
    lsof -i :$1 > /dev/null 2>&1
}

# Check if backend is already running
if check_port 5001; then
    echo "✅ Backend server already running on port 5001"
else
    echo "🔧 Starting backend server on port 5001..."
    cd backend
    python3 app.py &
    BACKEND_PID=$!
    cd ..
    echo "✅ Backend server started (PID: $BACKEND_PID)"
fi

# Wait a moment for backend to start
sleep 2

# Check if frontend is already running
if check_port 5173; then
    echo "✅ Frontend server already running on port 5173"
else
    echo "🔧 Starting frontend server on port 5173..."
    npm run dev &
    FRONTEND_PID=$!
    echo "✅ Frontend server started (PID: $FRONTEND_PID)"
fi

echo ""
echo "🎉 Servers are starting up!"
echo "📱 Frontend: http://localhost:5173"
echo "🔧 Backend:  http://localhost:5001"
echo ""
echo "💡 To stop servers, use: pkill -f 'python3 app.py' && pkill -f 'vite'"
echo ""
