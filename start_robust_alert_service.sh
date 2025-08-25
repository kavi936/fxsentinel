#!/bin/bash

# FXSentinel Robust Alert Service Startup Script
# This script starts the production-ready alert service with auto-restart and monitoring

echo "🚀 Starting FXSentinel Robust Alert Service..."
echo "=============================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed or not in PATH"
    exit 1
fi

# Check if the Flask app is running
if ! curl -s http://localhost:5001/api/health > /dev/null; then
    echo "❌ Flask app is not running on port 5001"
    echo "   Please start the Flask app first:"
    echo "   cd backend && python3 app.py"
    exit 1
fi

echo "✅ Flask app is running"

# Check if psutil is installed (required for memory monitoring)
if ! python3 -c "import psutil" 2>/dev/null; then
    echo "⚠️  psutil not found, installing..."
    pip3 install psutil
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Function to start the service
start_service() {
    echo "📱 Starting robust alert service..."
    echo "   Features: Auto-restart, Health monitoring, Memory management"
    echo "   Check interval: 5 minutes"
    echo "   Max memory: 500MB"
    echo "   Max errors before restart: 10"
    echo "   Log file: robust_alert_service.log"
    echo ""
    
    # Start the robust alert service
    cd backend
    python3 services/robust_alert_service.py
}

# Function to check service health
check_health() {
    echo "🔍 Checking service health..."
    response=$(curl -s http://localhost:5001/api/health/alerts)
    
    if [ $? -eq 0 ]; then
        echo "✅ Health check successful"
        echo "Response: $response"
    else
        echo "❌ Health check failed"
    fi
}

# Function to monitor the service
monitor_service() {
    echo "📊 Monitoring service..."
    echo "Press Ctrl+C to stop monitoring"
    echo ""
    
    while true; do
        clear
        echo "=== FXSentinel Robust Alert Service Monitor ==="
        echo "Time: $(date)"
        echo ""
        
        # Check service health
        response=$(curl -s http://localhost:5001/api/health/alerts 2>/dev/null)
        if [ $? -eq 0 ]; then
            echo "✅ Service Status: Healthy"
            echo "Response: $response" | jq '.' 2>/dev/null || echo "$response"
        else
            echo "❌ Service Status: Unhealthy"
        fi
        
        echo ""
        echo "Logs (last 10 lines):"
        echo "====================="
        tail -n 10 robust_alert_service.log 2>/dev/null || echo "No log file found"
        
        echo ""
        echo "Press Ctrl+C to stop monitoring"
        sleep 30
    done
}

# Main script logic
case "${1:-start}" in
    "start")
        start_service
        ;;
    "health")
        check_health
        ;;
    "monitor")
        monitor_service
        ;;
    "restart")
        echo "🔄 Restarting service..."
        pkill -f "robust_alert_service.py" 2>/dev/null
        sleep 2
        start_service
        ;;
    "stop")
        echo "🛑 Stopping service..."
        pkill -f "robust_alert_service.py"
        echo "✅ Service stopped"
        ;;
    "status")
        echo "📊 Service Status:"
        if pgrep -f "robust_alert_service.py" > /dev/null; then
            echo "✅ Service is running"
            check_health
        else
            echo "❌ Service is not running"
        fi
        ;;
    *)
        echo "Usage: $0 {start|health|monitor|restart|stop|status}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the robust alert service"
        echo "  health  - Check service health"
        echo "  monitor - Monitor service in real-time"
        echo "  restart - Restart the service"
        echo "  stop    - Stop the service"
        echo "  status  - Check service status"
        exit 1
        ;;
esac
