#!/usr/bin/env python3
"""
Test script for Finnhub API integration
Tests the economic calendar service with the demo credentials
"""

import os
import sys
import requests
from datetime import datetime, timedelta

# Add backend directory to path
sys.path.append('backend')

def test_finnhub_direct():
    """Test Finnhub API directly"""
    print("🔍 Testing Finnhub API directly...")
    
    # Demo credentials from email
    api_key = 'd2d51d1r01qjem5j4g9gd2d51d1r01qjem5j4ga0'
    base_url = 'https://finnhub.io/api/v1'
    
    # Test economic calendar endpoint
    url = f"{base_url}/calendar/economic"
    params = {
        'from': datetime.now().strftime('%Y-%m-%d'),
        'to': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
    }
    
    headers = {
        'X-Finnhub-Token': api_key,
        'User-Agent': 'FXSentinel/1.0'
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            events = data.get('economicCalendar', [])
            print(f"✅ Success! Found {len(events)} economic events")
            
            if events:
                print("\n📅 Sample events:")
                for i, event in enumerate(events[:3]):  # Show first 3 events
                    print(f"  {i+1}. {event.get('event', 'Unknown')} - {event.get('date', 'No date')} {event.get('time', 'No time')}")
                    print(f"     Currency: {event.get('currency', 'Unknown')}")
                    print(f"     Impact: {event.get('impact', 'Unknown')}")
                    print()
            
            return True
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Finnhub API: {e}")
        return False

def test_finnhub_service():
    """Test our Finnhub service"""
    print("\n🔍 Testing Finnhub Calendar Service...")
    
    try:
        from backend.services.finnhub_calendar import finnhub_calendar
        
        # Test connection
        result = finnhub_calendar.test_connection()
        print(f"Connection Test: {result}")
        
        # Test calendar fetch
        events = finnhub_calendar.get_economic_calendar()
        print(f"✅ Service fetched {len(events)} events")
        
        if events:
            print("\n📅 Transformed events:")
            for i, event in enumerate(events[:3]):  # Show first 3 events
                print(f"  {i+1}. {event.get('title', 'Unknown')}")
                print(f"     Time: {event.get('time', 'Unknown')} | Date: {event.get('date', 'Unknown')}")
                print(f"     Currency: {event.get('currency', 'Unknown')} | Impact: {event.get('impact', 'Unknown')}")
                print(f"     Type: {event.get('type', 'Unknown')} | Status: {event.get('status', 'Unknown')}")
                print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing service: {e}")
        return False

def test_backend_endpoint():
    """Test the backend API endpoint"""
    print("\n🔍 Testing Backend API Endpoint...")
    
    try:
        # Test the economic calendar endpoint
        url = "http://localhost:8000/api/economic-calendar"
        response = requests.get(url, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            events = data.get('events', [])
            source = data.get('source', 'Unknown')
            status = data.get('status', 'Unknown')
            
            print(f"✅ Success! Source: {source}, Status: {status}")
            print(f"Found {len(events)} events")
            
            if events:
                print("\n📅 API Events:")
                for i, event in enumerate(events[:3]):  # Show first 3 events
                    print(f"  {i+1}. {event.get('title', 'Unknown')}")
                    print(f"     Time: {event.get('time', 'Unknown')} | Date: {event.get('date', 'Unknown')}")
                    print(f"     Currency: {event.get('currency', 'Unknown')} | Impact: {event.get('impact', 'Unknown')}")
                    print()
            
            return True
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing backend endpoint: {e}")
        return False

def test_finnhub_test_endpoint():
    """Test the Finnhub test endpoint"""
    print("\n🔍 Testing Finnhub Test Endpoint...")
    
    try:
        url = "http://localhost:8000/api/finnhub-test"
        response = requests.get(url, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            finnhub_status = data.get('finnhub_status', {})
            
            print(f"✅ Finnhub Status: {finnhub_status}")
            return True
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Finnhub test endpoint: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 FXSentinel Finnhub Integration Test")
    print("=" * 50)
    
    # Test 1: Direct Finnhub API
    test1_success = test_finnhub_direct()
    
    # Test 2: Our Finnhub service
    test2_success = test_finnhub_service()
    
    # Test 3: Backend endpoint (if server is running)
    test3_success = test_backend_endpoint()
    
    # Test 4: Finnhub test endpoint
    test4_success = test_finnhub_test_endpoint()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"  Direct API Test: {'✅ PASS' if test1_success else '❌ FAIL'}")
    print(f"  Service Test: {'✅ PASS' if test2_success else '❌ FAIL'}")
    print(f"  Backend Endpoint: {'✅ PASS' if test3_success else '❌ FAIL'}")
    print(f"  Test Endpoint: {'✅ PASS' if test4_success else '❌ FAIL'}")
    
    if test1_success and test2_success:
        print("\n🎉 Finnhub integration is working correctly!")
        print("💡 You can now use the demo account for 1 month")
        print("💰 Consider upgrading to the $300/month plan for production use")
    else:
        print("\n⚠️ Some tests failed. Check the error messages above.")

if __name__ == "__main__":
    main()
