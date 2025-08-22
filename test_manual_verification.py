#!/usr/bin/env python3
"""
Manual Verification Test
Tests key features of FXSentinel web application manually
"""

import os
import requests
import json
from datetime import datetime

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

def test_news_api():
    """Test the news API endpoint"""
    print_status("Testing News API...", "INFO")
    
    try:
        response = requests.get("http://localhost:5001/api/news", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print_status("News API is working", "SUCCESS")
            
            # Check if we have news articles
            if 'articles' in data and len(data['articles']) > 0:
                print_status(f"Found {len(data['articles'])} news articles", "SUCCESS")
                # Show first article title
                first_article = data['articles'][0]
                if 'title' in first_article:
                    print_status(f"Sample article: {first_article['title'][:50]}...", "INFO")
            else:
                print_status("No news articles found", "WARNING")
            
            return True
        else:
            print_status(f"News API returned status {response.status_code}", "ERROR")
            return False
    except Exception as e:
        print_status(f"News API test failed: {str(e)}", "ERROR")
        return False

def test_economic_calendar():
    """Test the economic calendar API"""
    print_status("Testing Economic Calendar API...", "INFO")
    
    try:
        response = requests.get("http://localhost:5001/api/economic-calendar", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print_status("Economic Calendar API is working", "SUCCESS")
            
            # Check if we have calendar events
            if 'events' in data and len(data['events']) > 0:
                print_status(f"Found {len(data['events'])} calendar events", "SUCCESS")
                # Show first event
                first_event = data['events'][0]
                if 'event' in first_event:
                    print_status(f"Sample event: {first_event['event'][:50]}...", "INFO")
            else:
                print_status("No calendar events found", "WARNING")
            
            return True
        else:
            print_status(f"Economic Calendar API returned status {response.status_code}", "ERROR")
            return False
    except Exception as e:
        print_status(f"Economic Calendar API test failed: {str(e)}", "ERROR")
        return False

def test_forex_data():
    """Test forex data API"""
    print_status("Testing Forex Data API...", "INFO")
    
    try:
        response = requests.get("http://localhost:5001/api/forex", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print_status("Forex Data API is working", "SUCCESS")
            
            # Check if we have forex data
            if 'rates' in data and len(data['rates']) > 0:
                print_status(f"Found {len(data['rates'])} forex rates", "SUCCESS")
                # Show first rate
                first_rate = list(data['rates'].items())[0]
                print_status(f"Sample rate: {first_rate[0]} = {first_rate[1]}", "INFO")
            else:
                print_status("No forex rates found", "WARNING")
            
            return True
        else:
            print_status(f"Forex Data API returned status {response.status_code}", "ERROR")
            return False
    except Exception as e:
        print_status(f"Forex Data API test failed: {str(e)}", "ERROR")
        return False

def test_frontend_components():
    """Test frontend components"""
    print_status("Testing Frontend Components...", "INFO")
    
    try:
        # Test if frontend is accessible
        response = requests.get("http://localhost:5173", timeout=10)
        if response.status_code == 200:
            print_status("Frontend is accessible", "SUCCESS")
            
            # Check if it's a React app (look for React indicators)
            content = response.text
            if 'react' in content.lower() or 'vite' in content.lower():
                print_status("Frontend appears to be a React app", "SUCCESS")
            else:
                print_status("Frontend content doesn't look like React", "WARNING")
            
            return True
        else:
            print_status(f"Frontend returned status {response.status_code}", "ERROR")
            return False
    except Exception as e:
        print_status(f"Frontend test failed: {str(e)}", "ERROR")
        return False

def test_ai_analysis():
    """Test AI analysis functionality"""
    print_status("Testing AI Analysis...", "INFO")
    
    try:
        # Test if AI analysis endpoint exists
        response = requests.get("http://localhost:5001/api/analysis", timeout=10)
        if response.status_code == 200:
            print_status("AI Analysis API is working", "SUCCESS")
            return True
        elif response.status_code == 404:
            print_status("AI Analysis endpoint not found (may be POST only)", "WARNING")
            
            # Try POST request
            test_data = {
                "text": "USD/EUR exchange rate increased by 2% today due to positive economic data."
            }
            response = requests.post("http://localhost:5001/api/analysis", 
                                   json=test_data, timeout=30)
            if response.status_code == 200:
                print_status("AI Analysis POST endpoint is working", "SUCCESS")
                return True
            else:
                print_status(f"AI Analysis POST returned status {response.status_code}", "WARNING")
                return False
        else:
            print_status(f"AI Analysis API returned status {response.status_code}", "WARNING")
            return False
    except Exception as e:
        print_status(f"AI Analysis test failed: {str(e)}", "ERROR")
        return False

def main():
    """Run manual verification tests"""
    print("🔍 FXSentinel Manual Verification Test")
    print(f"📅 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_status("Make sure both servers are running:", "INFO")
    print_status("Backend: cd backend && python3 app.py", "INFO")
    print_status("Frontend: npm run dev", "INFO")
    print_status("", "INFO")
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    load_dotenv('backend/.env')
    
    # Run tests
    tests = [
        ("News API", test_news_api),
        ("Economic Calendar", test_economic_calendar),
        ("Forex Data", test_forex_data),
        ("Frontend Components", test_frontend_components),
        ("AI Analysis", test_ai_analysis)
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
    print_status("MANUAL VERIFICATION SUMMARY", "INFO")
    print_status("="*50, "INFO")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print_status(f"Tests passed: {passed}/{total}", "SUCCESS" if passed == total else "WARNING")
    
    for test_name, result in results:
        status = "SUCCESS" if result else "ERROR"
        print_status(f"{test_name}: {'Working' if result else 'Not working'}", status)
    
    if passed == total:
        print_status("🎉 All core features are working!", "SUCCESS")
        print_status("Your web app is ready for use", "INFO")
    else:
        print_status("⚠️ Some features need attention", "WARNING")
        print_status("Check the output above for specific issues", "INFO")
    
    print_status("", "INFO")
    print_status("To access your web app:", "INFO")
    print_status("1. Open http://localhost:5173 in your browser", "INFO")
    print_status("2. Test the different features manually", "INFO")
    print_status("3. Check the browser console for any errors", "INFO")

if __name__ == "__main__":
    main()
