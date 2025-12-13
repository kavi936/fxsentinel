#!/usr/bin/env python3
"""
Quick Test for API Keys and Servers
"""

import os
import requests
import subprocess
import time
import threading

# Load environment variables
os.chdir('backend')
from dotenv import load_dotenv
load_dotenv()
os.chdir('..')

def check_api_keys():
    """Check which API keys are configured"""
    print("🔑 Checking API Keys...")
    
    openai_key = os.getenv('OPENAI_API_KEY', '')
    finnhub_key = os.getenv('FINNHUB_API_KEY', '')
    alpha_key = os.getenv('ALPHA_VANTAGE_API_KEY_1', '')
    
    print(f"OpenAI: {'✅ Configured' if openai_key and 'your_' not in openai_key else '❌ Not configured'}")
    print(f"Finnhub: {'✅ Configured' if finnhub_key and 'your_' not in finnhub_key else '❌ Not configured'}")
    print(f"Alpha Vantage: {'✅ Configured' if alpha_key and 'your_' not in alpha_key else '❌ Not configured'}")
    
    return openai_key, finnhub_key, alpha_key

def test_openai(api_key):
    """Test OpenAI API"""
    if not api_key or 'your_' in api_key:
        print("❌ OpenAI API not configured")
        return False
    
    try:
        import openai
        openai.api_key = api_key
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=5
        )
        
        if response.choices:
            print("✅ OpenAI API working")
            return True
        else:
            print("❌ OpenAI API failed")
            return False
    except Exception as e:
        print(f"❌ OpenAI API error: {str(e)}")
        return False

def test_finnhub(api_key):
    """Test Finnhub API"""
    if not api_key or 'your_' in api_key:
        print("❌ Finnhub API not configured")
        return False
    
    try:
        url = f"https://finnhub.io/api/v1/quote?symbol=AAPL&token={api_key}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'c' in data:
                print(f"✅ Finnhub API working - AAPL: ${data['c']}")
                return True
            else:
                print("❌ Finnhub API returned unexpected data")
                return False
        else:
            print(f"❌ Finnhub API failed - status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Finnhub API error: {str(e)}")
        return False

def start_backend():
    """Start backend server"""
    print("🚀 Starting backend server...")
    
    def run_server():
        os.chdir('backend')
        subprocess.run(['python3', 'app.py'])
    
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    time.sleep(5)
    return thread

def start_frontend():
    """Start frontend server"""
    print("🚀 Starting frontend server...")
    
    def run_server():
        subprocess.run(['npm', 'run', 'dev'])
    
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    time.sleep(8)
    return thread

def test_servers():
    """Test if servers are working"""
    print("🌐 Testing servers...")
    
    # Test backend
    try:
        response = requests.get("http://localhost:5001/api/news", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'articles' in data:
                print(f"✅ Backend working - {len(data['articles'])} articles")
                return True
            else:
                print("⚠️ Backend working but no articles")
                return False
        else:
            print(f"❌ Backend failed - status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend error: {str(e)}")
        return False

def test_frontend():
    """Test frontend"""
    try:
        response = requests.get("http://localhost:5173", timeout=10)
        if response.status_code == 200:
            print("✅ Frontend working")
            return True
        else:
            print(f"❌ Frontend failed - status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frontend error: {str(e)}")
        return False

def main():
    """Run quick test"""
    print("🔍 FXSentinel Quick Test")
    print("=" * 40)
    
    # Check API keys
    openai_key, finnhub_key, alpha_key = check_api_keys()
    
    print("\n🧪 Testing APIs...")
    openai_working = test_openai(openai_key)
    finnhub_working = test_finnhub(finnhub_key)
    
    print("\n🚀 Starting servers...")
    backend_thread = start_backend()
    frontend_thread = start_frontend()
    
    print("\n🌐 Testing servers...")
    backend_working = test_servers()
    frontend_working = test_frontend()
    
    print("\n📊 Summary:")
    print(f"OpenAI API: {'✅ Working' if openai_working else '❌ Not working'}")
    print(f"Finnhub API: {'✅ Working' if finnhub_working else '❌ Not working'}")
    print(f"Backend Server: {'✅ Working' if backend_working else '❌ Not working'}")
    print(f"Frontend Server: {'✅ Working' if frontend_working else '❌ Not working'}")
    
    if backend_working and frontend_working:
        print("\n🎉 Your web app is working!")
        print("Frontend: http://localhost:5173")
        print("Backend: http://localhost:5001")
    else:
        print("\n⚠️ Some components need attention")
    
    # Keep servers running
    print("\nServers are running. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping servers...")

if __name__ == "__main__":
    main()
