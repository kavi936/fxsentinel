#!/usr/bin/env python3
"""
Test security on both local and production deployments
"""

import requests
import json

def test_production_security():
    """Test security on production deployment"""
    
    print("🔒 Testing Production Security")
    print("=" * 50)
    
    # Test URLs
    urls = [
        "http://localhost:5001",  # Local
        "https://fxsentinel-production.up.railway.app"  # Production
    ]
    
    for base_url in urls:
        print(f"\n🌐 Testing: {base_url}")
        print("-" * 30)
        
        # Test basic connectivity
        try:
            response = requests.get(f"{base_url}/api/hello", timeout=10)
            if response.status_code == 200:
                print("   ✅ App is running")
                
                # Check for sensitive data exposure
                data = response.json()
                sensitive_keys = ['api_key', 'token', 'password', 'secret', 'firebase', 'telegram']
                exposed = [key for key in sensitive_keys if key in str(data).lower()]
                
                if exposed:
                    print(f"   ❌ Sensitive data exposed: {exposed}")
                else:
                    print("   ✅ No sensitive data exposed")
                    
            else:
                print(f"   ⚠️ App responded with: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Cannot connect: {e}")
        
        # Test alert system security
        try:
            response = requests.get(f"{base_url}/api/alerts/user-settings?userId=test", timeout=10)
            if response.status_code in [401, 403]:
                print("   ✅ Alert endpoint properly secured")
            else:
                print(f"   ⚠️ Alert endpoint security unclear: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Alert endpoint error: {e}")
        
        # Test news endpoint (should be public)
        try:
            response = requests.get(f"{base_url}/api/news", timeout=10)
            if response.status_code == 200:
                print("   ✅ News endpoint accessible (public)")
            else:
                print(f"   ⚠️ News endpoint issue: {response.status_code}")
        except Exception as e:
            print(f"   ❌ News endpoint error: {e}")

if __name__ == "__main__":
    test_production_security()
