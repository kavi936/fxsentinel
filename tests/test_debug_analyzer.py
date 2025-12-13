#!/usr/bin/env python3
"""
Debug Analyzer Test
Tests which analyzer is actually being used and why model selection isn't working
"""

import requests
import time
import json
from datetime import datetime

def test_debug_analyzer():
    """Test to debug which analyzer is being used"""
    
    base_url = "http://localhost:5001"
    test_event_id = f"debug_test_{int(time.time())}"
    
    print(f"🚀 Debug Analyzer Test")
    print(f"==================================================")
    print(f"Testing backend at: {base_url}")
    print(f"Test event ID: {test_event_id}")
    print(f"Time: {datetime.now()}")
    print()
    
    # Test the analysis endpoint
    print(f"🧪 Testing Analysis Endpoint...")
    print(f"URL: {base_url}/api/enhanced-analysis/{test_event_id}")
    
    start_time = time.time()
    try:
        response = requests.get(f"{base_url}/api/enhanced-analysis/{test_event_id}", timeout=120)
        total_time = time.time() - start_time
        
        if response.status_code == 200:
            analysis = response.json()
            
            print(f"✅ Analysis completed: {total_time:.2f}s")
            print(f"📊 Model Used: {analysis.get('model_used', 'unknown')}")
            print(f"📊 Cache Hit: {analysis.get('cache_hit', False)}")
            print(f"📊 Cost: ${analysis.get('cost_estimate', 0):.4f}")
            
            # Check if this is the expected analyzer
            model_used = analysis.get('model_used', 'unknown')
            if 'gpt-4-turbo' in model_used or 'gpt-3.5-turbo' in model_used:
                print(f"✅ Using GPT AI Analyzer")
            else:
                print(f"❌ Using different analyzer: {model_used}")
            
            # Check response structure
            if 'headline' in analysis:
                print(f"✅ Using Enhanced GPT Analyzer (new structure)")
            elif 'event_summary' in analysis:
                print(f"✅ Using Standard GPT Analyzer")
            else:
                print(f"❌ Unknown analyzer structure")
                
        else:
            print(f"❌ Analysis failed: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            
    except Exception as e:
        print(f"❌ Test error: {e}")
    
    print(f"\n✨ Debug test completed!")
    print(f"==================================================")

if __name__ == "__main__":
    test_debug_analyzer()
