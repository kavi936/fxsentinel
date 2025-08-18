#!/usr/bin/env python3
"""
Test Optimized Performance
Tests the AI analysis with different event types to verify model selection
"""

import requests
import time
import json
from datetime import datetime

def test_model_selection():
    """Test different event types to verify model selection optimization"""
    
    base_url = "http://localhost:5001"
    
    print(f"🚀 Model Selection Performance Test")
    print(f"==================================================")
    print(f"Testing backend at: {base_url}")
    print(f"Time: {datetime.now()}")
    print()
    
    # Test cases for different event types
    test_cases = [
        {
            "name": "Low Impact Event (Should use GPT-3.5)",
            "event_id": f"retail_sales_{int(time.time())}",
            "expected_model": "gpt-3.5-turbo"
        },
        {
            "name": "High Impact Event (Should use GPT-4)",
            "event_id": f"nfp_{int(time.time())}",
            "expected_model": "gpt-4-turbo"
        }
    ]
    
    for test_case in test_cases:
        print(f"🧪 Testing: {test_case['name']}")
        print(f"Event ID: {test_case['event_id']}")
        print(f"Expected Model: {test_case['expected_model']}")
        
        start_time = time.time()
        try:
            response = requests.get(f"{base_url}/api/enhanced-analysis/{test_case['event_id']}", timeout=120)
            total_time = time.time() - start_time
            
            if response.status_code == 200:
                analysis = response.json()
                model_used = analysis.get('model_used', 'unknown')
                cache_hit = analysis.get('cache_hit', False)
                cost_estimate = analysis.get('cost_estimate', 0)
                
                print(f"✅ Analysis completed: {total_time:.2f}s")
                print(f"📊 Model Used: {model_used}")
                print(f"📊 Cache Hit: {cache_hit}")
                print(f"📊 Cost: ${cost_estimate:.4f}")
                
                # Check if model selection worked
                if model_used == test_case['expected_model']:
                    print(f"✅ Model selection CORRECT")
                else:
                    print(f"❌ Model selection WRONG - Expected {test_case['expected_model']}, got {model_used}")
                
                # Performance assessment
                if total_time < 5:
                    print(f"🎯 Performance: EXCELLENT")
                elif total_time < 15:
                    print(f"🎯 Performance: GOOD")
                elif total_time < 30:
                    print(f"🎯 Performance: ACCEPTABLE")
                else:
                    print(f"🎯 Performance: POOR")
                    
            else:
                print(f"❌ Analysis failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Test error: {e}")
        
        print(f"---")
    
    print(f"✨ Model selection test completed!")
    print(f"==================================================")

if __name__ == "__main__":
    test_model_selection()
