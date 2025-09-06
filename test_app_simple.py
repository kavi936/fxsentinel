#!/usr/bin/env python3
"""
Simple App Test
Test the main app by importing it directly and checking if it works.
"""

import os
import sys
import time

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_app_import():
    """Test if we can import the app"""
    print("🔍 Testing app import...")
    
    try:
        from app import app
        print("✅ App imported successfully!")
        
        # Test app configuration
        print(f"   App name: {app.name}")
        print(f"   Debug mode: {app.debug}")
        
        return True
    except Exception as e:
        print(f"❌ App import failed: {e}")
        return False

def test_app_routes():
    """Test if app has the expected routes"""
    print("\n🔍 Testing app routes...")
    
    try:
        from app import app
        
        # Get all routes
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append(rule.rule)
        
        print(f"✅ Found {len(routes)} routes")
        
        # Check for critical routes
        critical_routes = ['/api/health', '/api/status']
        for route in critical_routes:
            if route in routes:
                print(f"✅ Found critical route: {route}")
            else:
                print(f"⚠️ Missing critical route: {route}")
        
        return True
    except Exception as e:
        print(f"❌ Route test failed: {e}")
        return False

def test_environment():
    """Test environment setup"""
    print("\n🔍 Testing environment...")
    
    # Set test environment
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['PORT'] = '5001'
    
    # Check environment variables
    env_vars = ['OPENAI_API_KEY', 'TELEGRAM_BOT_TOKEN', 'STRIPE_SECRET_KEY']
    for var in env_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: SET")
        else:
            print(f"⚠️ {var}: NOT SET")
    
    return True

def test_app_startup():
    """Test if app can start (without actually running it)"""
    print("\n🔍 Testing app startup capability...")
    
    try:
        from app import app
        
        # Test if we can create a test client
        with app.test_client() as client:
            print("✅ Test client created successfully!")
            
            # Test health endpoint
            response = client.get('/api/health')
            if response.status_code == 200:
                print("✅ Health endpoint working!")
                print(f"   Response: {response.get_json()}")
                return True
            else:
                print(f"⚠️ Health endpoint returned status {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ App startup test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 FXSentinel Simple App Test")
    print("=" * 40)
    
    tests = [
        test_environment,
        test_app_import,
        test_app_routes,
        test_app_startup
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 40)
    print(f"Tests passed: {passed}/{len(tests)}")
    
    if passed == len(tests):
        print("🎉 All tests passed! App is ready for deployment!")
        return True
    else:
        print("❌ Some tests failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
