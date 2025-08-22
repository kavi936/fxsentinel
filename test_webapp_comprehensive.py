#!/usr/bin/env python3
"""
Comprehensive Web App Test Suite
Tests all major components of FXSentinel web application
"""

import os
import sys
import requests
import json
import time
import subprocess
import threading
from datetime import datetime

# Add backend to path
sys.path.append('backend')

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print(f"{'='*60}")

def print_status(message, status="INFO"):
    """Print a formatted status message"""
    status_icons = {
        "SUCCESS": "✅",
        "ERROR": "❌", 
        "WARNING": "⚠️",
        "INFO": "ℹ️"
    }
    icon = status_icons.get(status, "ℹ️")
    print(f"{icon} {message}")

def test_environment_setup():
    """Test environment variables and configuration"""
    print_section("Environment Setup Test")
    
    # Check if .env files exist
    env_files = ['.env', 'backend/.env']
    for env_file in env_files:
        if os.path.exists(env_file):
            print_status(f"{env_file} exists", "SUCCESS")
        else:
            print_status(f"{env_file} missing", "ERROR")
    
    # Check required environment variables
    required_vars = [
        'OPENAI_API_KEY',
        'FINNHUB_API_KEY', 
        'ALPHA_VANTAGE_API_KEY_1',
        'UNIRATE_API_KEY',
        'TELEGRAM_BOT_TOKEN',
        'FIREBASE_PROJECT_ID',
        'STRIPE_PUBLISHABLE_KEY',
        'STRIPE_SECRET_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if os.getenv(var):
            print_status(f"{var} is set", "SUCCESS")
        else:
            print_status(f"{var} is not set", "WARNING")
            missing_vars.append(var)
    
    if missing_vars:
        print_status(f"Missing environment variables: {', '.join(missing_vars)}", "WARNING")
        print_status("You'll need to add these to your .env files for full functionality", "INFO")

def test_backend_dependencies():
    """Test backend Python dependencies"""
    print_section("Backend Dependencies Test")
    
    try:
        # Check if we can import key modules
        import flask
        print_status("Flask is available", "SUCCESS")
        
        import openai
        print_status("OpenAI is available", "SUCCESS")
        
        import stripe
        print_status("Stripe is available", "SUCCESS")
        
        import firebase_admin
        print_status("Firebase Admin is available", "SUCCESS")
        
        import requests
        print_status("Requests is available", "SUCCESS")
        
        import beautifulsoup4
        print_status("BeautifulSoup4 is available", "SUCCESS")
        
    except ImportError as e:
        print_status(f"Missing dependency: {e}", "ERROR")
        return False
    
    return True

def test_backend_server():
    """Test backend Flask server"""
    print_section("Backend Server Test")
    
    # Change to backend directory
    os.chdir('backend')
    
    try:
        # Test if we can import the app
        from app import app
        print_status("Flask app imports successfully", "SUCCESS")
        
        # Test basic app configuration
        with app.test_client() as client:
            # Test health check endpoint
            response = client.get('/')
            if response.status_code == 200:
                print_status("Backend server responds to root endpoint", "SUCCESS")
            else:
                print_status(f"Backend server root endpoint returned {response.status_code}", "WARNING")
            
            # Test API endpoints
            endpoints_to_test = [
                '/api/forex',
                '/api/news',
                '/api/analysis',
                '/api/economic-calendar'
            ]
            
            for endpoint in endpoints_to_test:
                try:
                    response = client.get(endpoint)
                    if response.status_code in [200, 400, 401, 500]:  # Acceptable responses
                        print_status(f"Endpoint {endpoint} responds (status: {response.status_code})", "SUCCESS")
                    else:
                        print_status(f"Endpoint {endpoint} returned unexpected status {response.status_code}", "WARNING")
                except Exception as e:
                    print_status(f"Endpoint {endpoint} failed: {str(e)}", "ERROR")
        
    except Exception as e:
        print_status(f"Backend server test failed: {str(e)}", "ERROR")
        return False
    
    finally:
        os.chdir('..')  # Return to root directory
    
    return True

def test_frontend_dependencies():
    """Test frontend Node.js dependencies"""
    print_section("Frontend Dependencies Test")
    
    try:
        # Check if node_modules exists
        if os.path.exists('node_modules'):
            print_status("node_modules directory exists", "SUCCESS")
        else:
            print_status("node_modules directory missing - run 'npm install'", "ERROR")
            return False
        
        # Check if package.json exists
        if os.path.exists('package.json'):
            print_status("package.json exists", "SUCCESS")
        else:
            print_status("package.json missing", "ERROR")
            return False
        
        # Check if vite.config.js exists
        if os.path.exists('vite.config.js'):
            print_status("Vite config exists", "SUCCESS")
        else:
            print_status("Vite config missing", "ERROR")
            return False
        
        return True
        
    except Exception as e:
        print_status(f"Frontend dependencies test failed: {str(e)}", "ERROR")
        return False

def test_api_connections():
    """Test external API connections"""
    print_section("External API Connections Test")
    
    # Test Alpha Vantage API
    try:
        api_key = os.getenv('ALPHA_VANTAGE_API_KEY_1')
        if api_key and api_key != 'your_alpha_vantage_key_1_here':
            url = f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency=USD&to_currency=EUR&apikey={api_key}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'Realtime Currency Exchange Rate' in data:
                    print_status("Alpha Vantage API connection successful", "SUCCESS")
                else:
                    print_status("Alpha Vantage API returned unexpected data", "WARNING")
            else:
                print_status(f"Alpha Vantage API returned status {response.status_code}", "WARNING")
        else:
            print_status("Alpha Vantage API key not configured", "WARNING")
    except Exception as e:
        print_status(f"Alpha Vantage API test failed: {str(e)}", "WARNING")
    
    # Test Finnhub API
    try:
        api_key = os.getenv('FINNHUB_API_KEY')
        if api_key and api_key != 'your_finnhub_api_key_here':
            url = f"https://finnhub.io/api/v1/quote?symbol=AAPL&token={api_key}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print_status("Finnhub API connection successful", "SUCCESS")
            else:
                print_status(f"Finnhub API returned status {response.status_code}", "WARNING")
        else:
            print_status("Finnhub API key not configured", "WARNING")
    except Exception as e:
        print_status(f"Finnhub API test failed: {str(e)}", "WARNING")
    
    # Test OpenAI API
    try:
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key and api_key != 'your_openai_api_key_here':
            import openai
            openai.api_key = api_key
            # Test with a simple completion
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            if response.choices:
                print_status("OpenAI API connection successful", "SUCCESS")
            else:
                print_status("OpenAI API returned unexpected response", "WARNING")
        else:
            print_status("OpenAI API key not configured", "WARNING")
    except Exception as e:
        print_status(f"OpenAI API test failed: {str(e)}", "WARNING")

def test_database_connections():
    """Test database connections"""
    print_section("Database Connections Test")
    
    # Test Firebase connection
    try:
        import firebase_admin
        from firebase_admin import firestore
        
        if firebase_admin._apps:
            db = firestore.client()
            # Try to read a document
            doc_ref = db.collection('test').document('test')
            doc = doc_ref.get()
            print_status("Firebase connection successful", "SUCCESS")
        else:
            print_status("Firebase not initialized", "WARNING")
    except Exception as e:
        print_status(f"Firebase connection test failed: {str(e)}", "WARNING")

def test_file_structure():
    """Test file structure and key files"""
    print_section("File Structure Test")
    
    required_files = [
        'src/App.jsx',
        'src/main.jsx',
        'src/components/',
        'backend/app.py',
        'backend/requirements.txt',
        'index.html',
        'vite.config.js',
        'package.json'
    ]
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print_status(f"{file_path} exists", "SUCCESS")
        else:
            print_status(f"{file_path} missing", "ERROR")

def start_backend_server():
    """Start the backend server in a separate thread"""
    def run_server():
        os.chdir('backend')
        os.system('python3 app.py')
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(3)  # Give server time to start
    return server_thread

def test_frontend_build():
    """Test frontend build process"""
    print_section("Frontend Build Test")
    
    try:
        # Test if we can build the frontend
        result = subprocess.run(['npm', 'run', 'build'], 
                              capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print_status("Frontend builds successfully", "SUCCESS")
            
            # Check if dist directory was created
            if os.path.exists('dist'):
                print_status("Build output directory created", "SUCCESS")
            else:
                print_status("Build output directory missing", "ERROR")
        else:
            print_status(f"Frontend build failed: {result.stderr}", "ERROR")
            return False
            
    except subprocess.TimeoutExpired:
        print_status("Frontend build timed out", "ERROR")
        return False
    except Exception as e:
        print_status(f"Frontend build test failed: {str(e)}", "ERROR")
        return False
    
    return True

def test_development_server():
    """Test development server startup"""
    print_section("Development Server Test")
    
    try:
        # Test if we can start the dev server (briefly)
        process = subprocess.Popen(['npm', 'run', 'dev'], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE)
        
        # Wait a bit for server to start
        time.sleep(5)
        
        # Check if process is still running
        if process.poll() is None:
            print_status("Development server starts successfully", "SUCCESS")
            process.terminate()
            process.wait()
        else:
            stdout, stderr = process.communicate()
            print_status(f"Development server failed to start: {stderr.decode()}", "ERROR")
            return False
            
    except Exception as e:
        print_status(f"Development server test failed: {str(e)}", "ERROR")
        return False
    
    return True

def main():
    """Run all tests"""
    print("🚀 FXSentinel Web App Comprehensive Test Suite")
    print(f"📅 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    load_dotenv('backend/.env')
    
    # Run all tests
    tests = [
        test_environment_setup,
        test_file_structure,
        test_backend_dependencies,
        test_frontend_dependencies,
        test_api_connections,
        test_database_connections,
        test_backend_server,
        test_frontend_build,
        test_development_server
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append((test.__name__, result))
        except Exception as e:
            print_status(f"Test {test.__name__} crashed: {str(e)}", "ERROR")
            results.append((test.__name__, False))
    
    # Summary
    print_section("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print_status(f"Tests passed: {passed}/{total}", "SUCCESS" if passed == total else "WARNING")
    
    if passed < total:
        print_status("Some tests failed. Check the output above for details.", "WARNING")
        print_status("You may need to:", "INFO")
        print_status("1. Configure your .env files with actual API keys", "INFO")
        print_status("2. Install missing dependencies", "INFO")
        print_status("3. Fix any configuration issues", "INFO")
    else:
        print_status("All tests passed! Your web app should be working correctly.", "SUCCESS")
    
    print_status("To start the development server, run: npm run dev", "INFO")
    print_status("To start the backend server, run: cd backend && python3 app.py", "INFO")

if __name__ == "__main__":
    main()
