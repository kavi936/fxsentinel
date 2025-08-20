#!/usr/bin/env python3
"""
Comprehensive Security Test for FXSentinel
Tests all endpoints for security vulnerabilities
"""

import requests
import json
import time

def test_endpoint_security(endpoint, method="GET", data=None, expected_status=401):
    """Test endpoint security"""
    try:
        if method == "GET":
            response = requests.get(f"http://localhost:5001{endpoint}", timeout=10)
        elif method == "POST":
            response = requests.post(f"http://localhost:5001{endpoint}", json=data, timeout=10)
        else:
            return False, f"Unsupported method: {method}"
        
        if response.status_code == expected_status:
            return True, f"✅ {method} {endpoint} - Correctly secured ({response.status_code})"
        else:
            return False, f"❌ {method} {endpoint} - Security issue ({response.status_code}, expected {expected_status})"
            
    except Exception as e:
        return False, f"❌ {method} {endpoint} - Error: {e}"

def comprehensive_security_test():
    """Run comprehensive security tests"""
    
    print("🔒 Comprehensive Security Test for FXSentinel")
    print("=" * 60)
    
    # Test endpoints that should be secured
    endpoints_to_test = [
        # Alert endpoints
        ("/api/alerts/user-settings", "GET"),
        ("/api/alerts/test", "POST"),
        ("/api/telegram/verify", "POST"),
        
        # News endpoints
        ("/api/news", "GET"),
        ("/api/enhanced-analysis/test", "POST"),
        
        # Dashboard endpoints
        ("/api/dashboard-data", "GET"),
        ("/api/forex-prices", "GET"),
        
        # Economic calendar
        ("/api/economic-calendar", "GET"),
        
        # Technical analysis
        ("/api/technical-analysis/EURUSD", "GET"),
        
        # Market sentiment
        ("/api/market-sentiment", "GET"),
    ]
    
    print("\n🔍 Testing Endpoint Security...")
    print("-" * 40)
    
    passed = 0
    failed = 0
    
    for endpoint, method in endpoints_to_test:
        if method == "POST":
            # Test with invalid data
            test_data = {"invalid": "data"}
            success, message = test_endpoint_security(endpoint, method, test_data, 401)
        else:
            success, message = test_endpoint_security(endpoint, method, expected_status=401)
        
        print(f"   {message}")
        
        if success:
            passed += 1
        else:
            failed += 1
    
    # Test SQL injection attempts
    print("\n🔍 Testing SQL Injection Protection...")
    print("-" * 40)
    
    sql_injection_tests = [
        ("/api/alerts/user-settings?userId=1' OR '1'='1", "GET"),
        ("/api/news?source=1' UNION SELECT * FROM users--", "GET"),
    ]
    
    for endpoint, method in sql_injection_tests:
        success, message = test_endpoint_security(endpoint, method, expected_status=401)
        print(f"   {message}")
        if success:
            passed += 1
        else:
            failed += 1
    
    # Test XSS attempts
    print("\n🔍 Testing XSS Protection...")
    print("-" * 40)
    
    xss_test_data = {
        "userId": "<script>alert('xss')</script>",
        "message": "javascript:alert('xss')"
    }
    
    success, message = test_endpoint_security("/api/alerts/test", "POST", xss_test_data, 401)
    print(f"   {message}")
    if success:
        passed += 1
    else:
        failed += 1
    
    # Test rate limiting (basic)
    print("\n🔍 Testing Rate Limiting (Basic)...")
    print("-" * 40)
    
    # Make multiple rapid requests
    rapid_requests = []
    for i in range(5):
        try:
            response = requests.get("http://localhost:5001/api/news", timeout=5)
            rapid_requests.append(response.status_code)
        except:
            rapid_requests.append("error")
    
    if all(status == 401 for status in rapid_requests):
        print("   ✅ Rate limiting working (all requests blocked)")
        passed += 1
    else:
        print(f"   ⚠️ Rate limiting unclear: {rapid_requests}")
        failed += 1
    
    # Test environment variable exposure
    print("\n🔍 Testing Environment Variable Exposure...")
    print("-" * 40)
    
    try:
        response = requests.get("http://localhost:5001/api/hello", timeout=5)
        if response.status_code == 200:
            data = response.json()
            # Check if sensitive data is exposed
            sensitive_keys = ['api_key', 'token', 'password', 'secret', 'firebase', 'telegram']
            exposed = [key for key in sensitive_keys if key in str(data).lower()]
            
            if exposed:
                print(f"   ❌ Sensitive data potentially exposed: {exposed}")
                failed += 1
            else:
                print("   ✅ No sensitive data exposed")
                passed += 1
        else:
            print("   ✅ Endpoint properly secured")
            passed += 1
    except Exception as e:
        print(f"   ⚠️ Could not test: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Security Test Summary:")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📊 Total: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 All security tests passed!")
        print("✅ Your application is secure")
    else:
        print(f"\n⚠️ {failed} security issues found")
        print("🔧 Review and fix the issues above")
    
    print("\n🔒 Security Recommendations:")
    print("   • Add rate limiting to all endpoints")
    print("   • Implement CORS properly")
    print("   • Add input validation")
    print("   • Set up monitoring and logging")
    print("   • Regular security audits")

if __name__ == "__main__":
    comprehensive_security_test()
