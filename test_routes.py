#!/usr/bin/env python3
"""
Test script to check Flask routes
"""
import requests

def test_routes():
    """Test various routes to see which ones are working"""
    base_url = "http://localhost:5001"
    
    routes_to_test = [
        "/api/subscription-status/test_user",
        "/api/stripe-webhook", 
        "/api/create-checkout-session",
        "/api/create-portal-session"
    ]
    
    print("🔍 Testing Flask Routes:")
    print("=" * 40)
    
    for route in routes_to_test:
        try:
            if route == "/api/stripe-webhook":
                # Test POST for webhook
                response = requests.post(f"{base_url}{route}", 
                                       json={"test": "data"},
                                       headers={"Content-Type": "application/json"})
            else:
                # Test GET for other routes
                response = requests.get(f"{base_url}{route}")
            
            print(f"   {route}: {response.status_code}")
            
        except requests.exceptions.ConnectionError:
            print(f"   {route}: ❌ Connection Error")
        except Exception as e:
            print(f"   {route}: ❌ Error - {e}")

if __name__ == "__main__":
    test_routes()
