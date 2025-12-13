#!/usr/bin/env python3
"""
Performance test script to measure dashboard loading improvements
"""

import requests
import time
import json
from datetime import datetime

def test_endpoint_performance(base_url, endpoint, name):
    """Test the performance of a specific endpoint"""
    url = f"{base_url}{endpoint}"
    
    print(f"\n🧪 Testing {name}...")
    print(f"URL: {url}")
    
    start_time = time.time()
    try:
        response = requests.get(url, timeout=15)
        end_time = time.time()
        
        duration = end_time - start_time
        status = response.status_code
        
        if status == 200:
            data = response.json()
            if 'news' in data:
                article_count = len(data.get('news', []))
                print(f"✅ Success: {duration:.2f}s | Status: {status} | Articles: {article_count}")
            else:
                print(f"✅ Success: {duration:.2f}s | Status: {status}")
        else:
            print(f"❌ Failed: {duration:.2f}s | Status: {status}")
            
        return duration, status == 200
        
    except requests.exceptions.Timeout:
        print(f"⏰ Timeout after 15s")
        return 15.0, False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None, False

def main():
    # Test configuration
    base_url = "http://localhost:8000"  # Change this to your backend URL
    
    print("🚀 FXSentinel Performance Test")
    print("=" * 50)
    print(f"Testing backend at: {base_url}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test individual endpoints
    endpoints = [
        ("/api/news", "News Endpoint"),
        ("/api/trading-data", "Trading Data Endpoint"),
        ("/api/alerts", "Alerts Endpoint"),
        ("/api/ai-insights", "AI Insights Endpoint"),
        ("/api/alert-settings", "Alert Settings Endpoint"),
    ]
    
    individual_results = []
    for endpoint, name in endpoints:
        duration, success = test_endpoint_performance(base_url, endpoint, name)
        if duration:
            individual_results.append((name, duration, success))
    
    # Test optimized dashboard endpoint
    print(f"\n🎯 Testing Optimized Dashboard Endpoint...")
    dashboard_duration, dashboard_success = test_endpoint_performance(
        base_url, "/api/dashboard-data", "Dashboard Data (All-in-One)"
    )
    
    # Calculate improvements
    if individual_results and dashboard_duration:
        total_individual_time = sum(duration for _, duration, _ in individual_results)
        improvement = ((total_individual_time - dashboard_duration) / total_individual_time) * 100
        
        print(f"\n📊 Performance Summary")
        print("=" * 50)
        print(f"Individual endpoints total time: {total_individual_time:.2f}s")
        print(f"Optimized endpoint time: {dashboard_duration:.2f}s")
        print(f"Performance improvement: {improvement:.1f}%")
        
        if improvement > 0:
            print(f"✅ Optimized endpoint is {improvement:.1f}% faster!")
        else:
            print(f"⚠️ Optimized endpoint is {abs(improvement):.1f}% slower")
    
    # Test cache effectiveness
    print(f"\n💾 Testing Cache Effectiveness...")
    cache_duration1, _ = test_endpoint_performance(base_url, "/api/news", "News (First Call)")
    cache_duration2, _ = test_endpoint_performance(base_url, "/api/news", "News (Cached)")
    
    if cache_duration1 and cache_duration2:
        cache_improvement = ((cache_duration1 - cache_duration2) / cache_duration1) * 100
        print(f"Cache improvement: {cache_improvement:.1f}%")
    
    print(f"\n✨ Performance test completed!")

if __name__ == "__main__":
    main()
