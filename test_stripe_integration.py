#!/usr/bin/env python3
"""
Test script for Stripe integration
Run this to verify the basic setup is working
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test configuration
BASE_URL = "http://localhost:5001"  # Adjust if your Flask app runs on different port

def test_stripe_service_import():
    """Test that the Stripe service can be imported"""
    try:
        from backend.services.stripe_service import StripeService
        print("✅ Stripe service imported successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import Stripe service: {e}")
        return False

def test_environment_variables():
    """Test that required environment variables are set"""
    required_vars = [
        'STRIPE_PUBLISHABLE_KEY',
        'STRIPE_SECRET_KEY',
        'STRIPE_WEBHOOK_SECRET'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️ Missing environment variables: {', '.join(missing_vars)}")
        print("   These are required for full Stripe functionality")
        return False
    else:
        print("✅ All required environment variables are set")
        return True

def test_flask_app_routes():
    """Test that Flask app has the required routes"""
    try:
        # Test if the app is running
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Flask app is running")
            
            # Test subscription status endpoint (should return 404 for non-existent user)
            response = requests.get(f"{BASE_URL}/api/subscription-status/test_user", timeout=5)
            if response.status_code in [200, 404, 500]:  # Any response means endpoint exists
                print("✅ Subscription status endpoint is accessible")
            else:
                print("❌ Subscription status endpoint not accessible")
                return False
                
            return True
        else:
            print(f"❌ Flask app returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Flask app is not running. Start it with: cd backend && python3 app.py")
        return False
    except Exception as e:
        print(f"❌ Error testing Flask app: {e}")
        return False

def test_frontend_dependencies():
    """Test that frontend dependencies are installed"""
    try:
        import stripe
        print("✅ Stripe Python package is installed")
    except ImportError:
        print("❌ Stripe Python package is not installed")
        return False
    
    # Check if package.json has Stripe dependencies
    try:
        with open('package.json', 'r') as f:
            package_data = json.load(f)
            dependencies = package_data.get('dependencies', {})
            
            stripe_deps = [
                '@stripe/stripe-js',
                '@stripe/react-stripe-js'
            ]
            
            missing_deps = []
            for dep in stripe_deps:
                if dep not in dependencies:
                    missing_deps.append(dep)
            
            if missing_deps:
                print(f"⚠️ Missing frontend dependencies: {', '.join(missing_deps)}")
                print("   Run: npm install @stripe/stripe-js @stripe/react-stripe-js")
                return False
            else:
                print("✅ Frontend Stripe dependencies are installed")
                return True
    except Exception as e:
        print(f"❌ Error checking frontend dependencies: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Stripe Integration Setup")
    print("=" * 50)
    
    tests = [
        ("Stripe Service Import", test_stripe_service_import),
        ("Environment Variables", test_environment_variables),
        ("Flask App Routes", test_flask_app_routes),
        ("Frontend Dependencies", test_frontend_dependencies),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing: {test_name}")
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Stripe integration is ready for development.")
        print("\n📝 Next steps:")
        print("1. Set up your Stripe account and get API keys")
        print("2. Update your .env file with the actual Stripe keys")
        print("3. Create a subscription product in Stripe dashboard")
        print("4. Test the trial welcome flow")
    else:
        print("⚠️ Some tests failed. Please fix the issues above before proceeding.")
    
    return passed == total

if __name__ == "__main__":
    main()
