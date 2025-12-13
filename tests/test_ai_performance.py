#!/usr/bin/env python3
"""
AI Analysis Performance Test
Measures response times and identifies bottlenecks in the AI analysis system
"""

import requests
import time
import json
from datetime import datetime

def test_ai_analysis_performance():
    """Test AI analysis performance with detailed timing"""
    
    base_url = "http://localhost:5001"
    test_event_id = f"performance_test_{int(time.time())}"
    
    print(f"🚀 AI Analysis Performance Test")
    print(f"==================================================")
    print(f"Testing backend at: {base_url}")
    print(f"Test event ID: {test_event_id}")
    print(f"Time: {datetime.now()}")
    print()
    
    # Test 1: Health check
    print("🧪 Testing Health Check...")
    start_time = time.time()
    try:
        response = requests.get(f"{base_url}/api/health", timeout=5)
        health_time = time.time() - start_time
        if response.status_code == 200:
            print(f"✅ Health check: {health_time:.2f}s")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return
    
    # Test 2: AI Analysis with detailed timing
    print(f"\n🧪 Testing AI Analysis Performance...")
    print(f"URL: {base_url}/api/enhanced-analysis/{test_event_id}")
    
    start_time = time.time()
    try:
        response = requests.get(f"{base_url}/api/enhanced-analysis/{test_event_id}", timeout=120)
        total_time = time.time() - start_time
        
        if response.status_code == 200:
            print(f"✅ AI Analysis completed: {total_time:.2f}s")
            
            # Parse response to get analysis details
            try:
                analysis = response.json()
                model_used = analysis.get('model_used', 'unknown')
                cache_hit = analysis.get('cache_hit', False)
                confidence_score = analysis.get('confidence_score', 0)
                cost_estimate = analysis.get('cost_estimate', 0)
                
                print(f"📊 Analysis Details:")
                print(f"   Model Used: {model_used}")
                print(f"   Cache Hit: {cache_hit}")
                print(f"   Confidence Score: {confidence_score}")
                print(f"   Cost Estimate: ${cost_estimate:.4f}")
                
                # Check response size
                response_size = len(response.content)
                print(f"   Response Size: {response_size:,} bytes")
                
                # Performance assessment
                if total_time < 5:
                    print(f"🎯 Performance: EXCELLENT (< 5s)")
                elif total_time < 15:
                    print(f"🎯 Performance: GOOD (5-15s)")
                elif total_time < 30:
                    print(f"🎯 Performance: ACCEPTABLE (15-30s)")
                else:
                    print(f"🎯 Performance: POOR (> 30s) - NEEDS OPTIMIZATION")
                
            except json.JSONDecodeError:
                print(f"⚠️ Could not parse response as JSON")
                
        else:
            print(f"❌ AI Analysis failed: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            
    except requests.exceptions.Timeout:
        print(f"❌ AI Analysis timed out after 120s")
    except Exception as e:
        print(f"❌ AI Analysis error: {e}")
    
    # Test 3: Cache effectiveness
    print(f"\n🧪 Testing Cache Effectiveness...")
    print(f"Making second request to same endpoint...")
    
    start_time = time.time()
    try:
        response2 = requests.get(f"{base_url}/api/enhanced-analysis/{test_event_id}", timeout=120)
        cache_time = time.time() - start_time
        
        if response2.status_code == 200:
            analysis2 = response2.json()
            cache_hit2 = analysis2.get('cache_hit', False)
            
            print(f"✅ Second request: {cache_time:.2f}s")
            print(f"📊 Cache Hit: {cache_hit2}")
            
            if cache_time > 0: # Avoid division by zero
                speedup = total_time / cache_time
                print(f"🚀 Cache Speedup: {speedup:.1f}x faster")
            else:
                print(f"⚠️ No cache hit - both requests took similar time")
                
        else:
            print(f"❌ Second request failed: {response2.status_code}")
            
    except Exception as e:
        print(f"❌ Cache test error: {e}")
    
    print(f"\n✨ Performance test completed!")
    print(f"==================================================")

if __name__ == "__main__":
    test_ai_analysis_performance()
