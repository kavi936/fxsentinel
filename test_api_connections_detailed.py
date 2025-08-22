#!/usr/bin/env python3
"""
Detailed API Connection Test
Tests all external API connections with real keys
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
            print_status("OpenAI API key not configured", "ERROR")
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
            print_status("Finnhub API key not configured", "ERROR")
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

def test_alpha_vantage_api():
    """Test Alpha Vantage API connection"""
    print_status("Testing Alpha Vantage API...", "INFO")
    
    try:
        api_key = os.getenv('ALPHA_VANTAGE_API_KEY_1')
        if not api_key or api_key == 'your_alpha_vantage_key_1_here':
            print_status("Alpha Vantage API key not configured", "ERROR")
            return False
        
        # Test currency exchange rate
        url = f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency=USD&to_currency=EUR&apikey={api_key}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'Realtime Currency Exchange Rate' in data:
                rate_info = data['Realtime Currency Exchange Rate']
                rate = rate_info.get('5. Exchange Rate', 'N/A')
                print_status(f"Alpha Vantage API working - USD/EUR rate: {rate}", "SUCCESS")
                return True
            else:
                print_status("Alpha Vantage API returned unexpected data format", "WARNING")
                return False
        else:
            print_status(f"Alpha Vantage API returned status {response.status_code}", "ERROR")
            return False
            
    except Exception as e:
        print_status(f"Alpha Vantage API test failed: {str(e)}", "ERROR")
        return False

def test_unirate_api():
    """Test UniRate API connection"""
    print_status("Testing UniRate API...", "INFO")
    
    try:
        api_key = os.getenv('UNIRATE_API_KEY')
        if not api_key or api_key == 'demo':
            print_status("UniRate API key not configured", "WARNING")
            return False
        
        # Test exchange rate endpoint
        url = f"https://api.unirate.io/v1/exchange-rate?from=USD&to=EUR&api_key={api_key}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'rate' in data:
                print_status(f"UniRate API working - USD/EUR rate: {data['rate']}", "SUCCESS")
                return True
            else:
                print_status("UniRate API returned unexpected data format", "WARNING")
                return False
        else:
            print_status(f"UniRate API returned status {response.status_code}", "WARNING")
            return False
            
    except Exception as e:
        print_status(f"UniRate API test failed: {str(e)}", "WARNING")
        return False

def test_stripe_api():
    """Test Stripe API connection"""
    print_status("Testing Stripe API...", "INFO")
    
    try:
        secret_key = os.getenv('STRIPE_SECRET_KEY')
        if not secret_key or secret_key == 'sk_test_your_secret_key_here':
            print_status("Stripe secret key not configured", "WARNING")
            return False
        
        import stripe
        stripe.api_key = secret_key
        
        # Test by retrieving account info
        account = stripe.Account.retrieve()
        if account:
            print_status(f"Stripe API working - Account: {account.id}", "SUCCESS")
            return True
        else:
            print_status("Stripe API returned empty response", "WARNING")
            return False
            
    except Exception as e:
        print_status(f"Stripe API test failed: {str(e)}", "WARNING")
        return False

def test_telegram_bot():
    """Test Telegram Bot API"""
    print_status("Testing Telegram Bot API...", "INFO")
    
    try:
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not bot_token or bot_token == 'your_telegram_bot_token_here':
            print_status("Telegram bot token not configured", "WARNING")
            return False
        
        # Test bot info endpoint
        url = f"https://api.telegram.org/bot{bot_token}/getMe"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok') and data.get('result'):
                bot_info = data['result']
                bot_name = bot_info.get('first_name', 'Unknown')
                bot_username = bot_info.get('username', 'Unknown')
                print_status(f"Telegram Bot API working - Bot: {bot_name} (@{bot_username})", "SUCCESS")
                return True
            else:
                print_status("Telegram Bot API returned error", "WARNING")
                return False
        else:
            print_status(f"Telegram Bot API returned status {response.status_code}", "WARNING")
            return False
            
    except Exception as e:
        print_status(f"Telegram Bot API test failed: {str(e)}", "WARNING")
        return False

def test_firebase_connection():
    """Test Firebase connection"""
    print_status("Testing Firebase connection...", "INFO")
    
    try:
        project_id = os.getenv('FIREBASE_PROJECT_ID')
        if not project_id or project_id == 'fxsentinel':
            print_status("Firebase project ID not configured", "WARNING")
            return False
        
        import firebase_admin
        from firebase_admin import firestore
        
        if firebase_admin._apps:
            db = firestore.client()
            # Try to read a test document
            doc_ref = db.collection('test').document('connection_test')
            doc = doc_ref.get()
            print_status("Firebase connection working", "SUCCESS")
            return True
        else:
            print_status("Firebase not initialized", "WARNING")
            return False
            
    except Exception as e:
        print_status(f"Firebase connection test failed: {str(e)}", "WARNING")
        return False

def test_backend_endpoints_with_real_data():
    """Test backend endpoints with real API data"""
    print_status("Testing Backend Endpoints with Real Data...", "INFO")
    
    # Start backend server in background
    import subprocess
    import threading
    import time
    
    def start_server():
        os.chdir('backend')
        subprocess.run(['python3', 'app.py'], capture_output=True)
    
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    time.sleep(5)  # Give server time to start
    
    try:
        # Test news endpoint
        response = requests.get("http://localhost:5001/api/news", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'articles' in data and len(data['articles']) > 0:
                print_status(f"Backend news endpoint working - {len(data['articles'])} articles", "SUCCESS")
            else:
                print_status("Backend news endpoint working but no articles", "WARNING")
        else:
            print_status(f"Backend news endpoint failed - status {response.status_code}", "ERROR")
        
        # Test economic calendar endpoint
        response = requests.get("http://localhost:5001/api/economic-calendar", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'events' in data:
                print_status(f"Backend calendar endpoint working - {len(data['events'])} events", "SUCCESS")
            else:
                print_status("Backend calendar endpoint working but no events", "WARNING")
        else:
            print_status(f"Backend calendar endpoint failed - status {response.status_code}", "ERROR")
            
    except Exception as e:
        print_status(f"Backend endpoint test failed: {str(e)}", "ERROR")
    
    finally:
        os.chdir('..')

def main():
    """Run all API connection tests"""
    print("🔌 FXSentinel API Connection Test")
    print(f"📅 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_status("Testing all external API connections...", "INFO")
    
    # Run all tests
    tests = [
        ("OpenAI API", test_openai_api),
        ("Finnhub API", test_finnhub_api),
        ("Alpha Vantage API", test_alpha_vantage_api),
        ("UniRate API", test_unirate_api),
        ("Stripe API", test_stripe_api),
        ("Telegram Bot API", test_telegram_bot),
        ("Firebase Connection", test_firebase_connection)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_status(f"Test {test_name} crashed: {str(e)}", "ERROR")
            results.append((test_name, False))
    
    # Summary
    print_status("\n" + "="*50, "INFO")
    print_status("API CONNECTION TEST SUMMARY", "INFO")
    print_status("="*50, "INFO")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print_status(f"APIs working: {passed}/{total}", "SUCCESS" if passed > 0 else "WARNING")
    
    for test_name, result in results:
        status = "SUCCESS" if result else "ERROR"
        print_status(f"{test_name}: {'Working' if result else 'Not working'}", status)
    
    if passed > 0:
        print_status("🎉 Some APIs are working correctly!", "SUCCESS")
        print_status("Your web app should have partial functionality", "INFO")
    else:
        print_status("⚠️ No APIs are working", "WARNING")
        print_status("Check your API keys and configuration", "INFO")
    
    # Test backend endpoints
    print_status("\nTesting backend endpoints with real data...", "INFO")
    test_backend_endpoints_with_real_data()

if __name__ == "__main__":
    main()
