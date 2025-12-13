#!/usr/bin/env python3
"""
Test script for clearing analyzed news history
"""

import sys
import os

# Add the current directory to path
sys.path.append('.')

def test_clear_function():
    """Test the clear analyzed news function"""
    
    print("🧪 Testing Clear Analyzed News Function")
    print("=" * 50)
    
    try:
        # Import the function
        from clear_analyzed_news import clear_analyzed_news_history, show_current_stats
        
        # First, show current stats
        print("\n📊 Current Statistics:")
        show_current_stats()
        
        # Test clearing only analysis history (with confirmation)
        print("\n" + "="*50)
        print("🧪 Test 1: Clear only analysis history")
        print("="*50)
        
        # This will prompt for confirmation
        result = clear_analyzed_news_history(clear_type="analysis", confirm=False)
        
        print(f"\n📋 Test 1 Result:")
        print(f"   Success: {result['success']}")
        print(f"   Cleared Items: {result['cleared_items']}")
        if result['errors']:
            print(f"   Errors: {result['errors']}")
        
        # Test clearing all data (with auto-confirm)
        print("\n" + "="*50)
        print("🧪 Test 2: Clear all data (auto-confirm)")
        print("="*50)
        
        result = clear_analyzed_news_history(clear_type="all", confirm=True)
        
        print(f"\n📋 Test 2 Result:")
        print(f"   Success: {result['success']}")
        print(f"   Cleared Items: {result['cleared_items']}")
        if result['errors']:
            print(f"   Errors: {result['errors']}")
        
        # Show final stats
        print("\n📊 Final Statistics:")
        show_current_stats()
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you're running this script from the project root directory")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def test_api_endpoint():
    """Test the API endpoint for clearing history"""
    
    print("\n🌐 Testing API Endpoint")
    print("=" * 50)
    
    try:
        import requests
        import json
        
        # Test the API endpoint
        api_url = "http://localhost:5001/api/clear-analysis-history"
        
        # Test data
        test_data = {
            "type": "analysis",
            "confirm": True
        }
        
        print(f"📡 Making POST request to: {api_url}")
        print(f"📦 Request data: {json.dumps(test_data, indent=2)}")
        
        response = requests.post(api_url, json=test_data)
        
        print(f"\n📋 API Response:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        
    except ImportError:
        print("❌ requests library not available. Install with: pip install requests")
    except Exception as e:
        print(f"❌ API test error: {e}")

if __name__ == "__main__":
    print("🚀 Starting Clear Analyzed News Tests")
    
    # Test the Python function
    test_clear_function()
    
    # Test the API endpoint (optional)
    print("\n" + "="*50)
    response = input("❓ Do you want to test the API endpoint? (y/n): ").lower().strip()
    if response in ['y', 'yes']:
        test_api_endpoint()
    
    print("\n✅ Tests completed!")
