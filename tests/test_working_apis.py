#!/usr/bin/env python3
"""
Test Working APIs
Tests only the APIs that are actually configured
"""

import os
import requests
import json
import time
from datetime import datetime

# Load environment variables from backend
os.chdir('backend')
from dotenv import load_dotenv
load_dotenv()
os.chdir('..')

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

def test_openai_api():
    """Test OpenAI API connection"""
    print_status("Testing OpenAI API...", "INFO")
    
    try:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key or api_key == 'your_openai_api_key_here':
            print_status("OpenAI API key not configured", "WARNING")
            return False
        
        import openai
        openai.api_key = api_key
        
        # Test with a simple completion
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'Hello World'"}],
            max_tokens=10
        )
        
        if response.choices and len(response.choices) > 0:
            content = response.choices[0].message.content
            print_status(f"OpenAI API working - Response: {content}", "SUCCESS")
            return True
        else:
            print_status("OpenAI API returned empty response", "ERROR")
            return False
            
    except Exception as e:
        print_status(f"OpenAI API test failed: {str(e)}", "ERROR")
        return False

def test_finnhub_api():
    """Test Finnhub API connection"""
    print_status("Testing Finnhub API...", "INFO")
    
    try:
        api_key = os.getenv('FINNHUB_API_KEY')
        if not api_key or api_key == 'your_finnhub_api_key_here':
            print_status("Finnhub API key not configured", "WARNING")
            return False
        
        # Test quote endpoint
        url = f"https://finnhub.io/api/v1/quote?symbol=AAPL&token={api_key}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'c' in data:  # Current price
                print_status(f"Finnhub API working - AAPL price: ${data['c']}", "SUCCESS")
                return True
            else:
                print_status("Finnhub API returned unexpected data format", "WARNING")
                return False
        else:
            print_status(f"Finnhub API returned status {response.status_code}", "ERROR")
            return False
            
    except Exception as e:
        print_status(f"Finnhub API test failed: {str(e)}", "ERROR")
        return False

def test_backend_server():
    """Test backend server functionality"""
    print_status("Testing Backend Server...", "INFO")
    
    import subprocess
    import threading
    import time
    
    def start_server():
        os.chdir('backend')
        subprocess.run(['python3', 'app.py'], capture_output=True)
    
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    time.sleep(8)  # Give server more time to start
    
    try:
        # Test news endpoint
        response = requests.get("http://localhost:5001/api/news", timeout=15)
        if response.status_code == 200:
            data = response.json()
            if 'articles' in data and len(data['articles']) > 0:
                print_status(f"Backend news endpoint working - {len(data['articles'])} articles", "SUCCESS")
                # Show sample article
                first_article = data['articles'][0]
                if 'title' in first_article:
                    print_status(f"Sample article: {first_article['title'][:60]}...", "INFO")
                return True
            else:
                print_status("Backend news endpoint working but no articles", "WARNING")
                return False
        else:
            print_status(f"Backend news endpoint failed - status {response.status_code}", "ERROR")
            return False
            
    except Exception as e:
        print_status(f"Backend server test failed: {str(e)}", "ERROR")
        return False
    
    finally:
        os.chdir('..')

def test_frontend_server():
    """Test frontend server"""
    print_status("Testing Frontend Server...", "INFO")
    
    import subprocess
    import threading
    import time
    
    def start_server():
        subprocess.run(['npm', 'run', 'dev'], capture_output=True)
    
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    time.sleep(10)  # Give server time to start
    
    try:
        # Test frontend access
        response = requests.get("http://localhost:5173", timeout=10)
        if response.status_code == 200:
            print_status("Frontend server working", "SUCCESS")
            return True
        else:
            print_status(f"Frontend server returned status {response.status_code}", "ERROR")
            return False
            
    except Exception as e:
        print_status(f"Frontend server test failed: {str(e)}", "ERROR")
        return False

def test_full_integration():
    """Test full integration between frontend and backend"""
    print_status("Testing Full Integration...", "INFO")
    
    try:
        # Test if frontend can access backend API
        response = requests.get("http://localhost:5001/api/news", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'articles' in data and len(data['articles']) > 0:
                print_status("Full integration working - news data available", "SUCCESS")
                return True
            else:
                print_status("Full integration working but no news data", "WARNING")
                return False
        else:
            print_status(f"Full integration failed - status {response.status_code}", "ERROR")
            return False
            
    except Exception as e:
        print_status(f"Full integration test failed: {str(e)}", "ERROR")
        return False

def main():
    """Run tests for working APIs"""
    print("🔌 FXSentinel Working APIs Test")
    print(f"📅 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_status("Testing configured APIs and server functionality...", "INFO")
    
    # Test individual APIs
    api_tests = [
        ("OpenAI API", test_openai_api),
        ("Finnhub API", test_finnhub_api)
    ]
    
    api_results = []
    for test_name, test_func in api_tests:
        try:
            result = test_func()
            api_results.append((test_name, result))
        except Exception as e:
            print_status(f"API test {test_name} crashed: {str(e)}", "ERROR")
            api_results.append((test_name, False))
    
    # Test servers
    server_tests = [
        ("Backend Server", test_backend_server),
        ("Frontend Server", test_frontend_server)
    ]
    
    server_results = []
    for test_name, test_func in server_tests:
        try:
            result = test_func()
            server_results.append((test_name, result))
        except Exception as e:
            print_status(f"Server test {test_name} crashed: {str(e)}", "ERROR")
            server_results.append((test_name, False))
    
    # Test integration
    integration_result = test_full_integration()
    
    # Summary
    print_status("\n" + "="*50, "INFO")
    print_status("WORKING APIS TEST SUMMARY", "INFO")
    print_status("="*50, "INFO")
    
    api_passed = sum(1 for _, result in api_results if result)
    server_passed = sum(1 for _, result in server_results if result)
    
    print_status(f"APIs working: {api_passed}/{len(api_results)}", "SUCCESS" if api_passed > 0 else "WARNING")
    print_status(f"Servers working: {server_passed}/{len(server_results)}", "SUCCESS" if server_passed > 0 else "WARNING")
    print_status(f"Integration working: {'Yes' if integration_result else 'No'}", "SUCCESS" if integration_result else "WARNING")
    
    print_status("\nDetailed Results:", "INFO")
    for test_name, result in api_results + server_results:
        status = "SUCCESS" if result else "ERROR"
        print_status(f"{test_name}: {'Working' if result else 'Not working'}", status)
    
    if api_passed > 0 and server_passed > 0 and integration_result:
        print_status("🎉 Your web app is fully functional!", "SUCCESS")
        print_status("Frontend: http://localhost:5173", "INFO")
        print_status("Backend: http://localhost:5001", "INFO")
        print_status("You can now use your web app", "INFO")
    elif server_passed > 0:
        print_status("⚠️ Servers are working but some APIs need configuration", "WARNING")
        print_status("Basic functionality should work", "INFO")
    else:
        print_status("❌ Core functionality needs attention", "ERROR")
        print_status("Check server configuration and API keys", "INFO")

if __name__ == "__main__":
    main()
