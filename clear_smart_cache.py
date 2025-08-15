#!/usr/bin/env python3
"""
Clear Smart Cache
Clear the smart cache to force fresh ChatGPT analysis
"""

import requests
import json

def clear_smart_cache():
    """Clear the smart cache to force fresh analysis"""
    
    print("🧹 CLEARING SMART CACHE")
    print("=" * 40)
    
    base_url = "http://localhost:5001"
    
    # Try to clear cache by calling the endpoint with a cache-busting parameter
    test_event = {
        'title': 'Unemployment Rate',
        'currency': 'GBP',
        'actual': '4.7%',
        'expected': '4.7%',
        'previous': '4.7%',
        'impact': 'High',
        'date': 'Tue, Aug 12',
        'time': '10:00 GST',
        'id': '8673173089515658000',
        'cache_bust': 'true'  # Add cache busting parameter
    }
    
    try:
        print("🚀 Calling enhanced-analysis endpoint with cache busting...")
        response = requests.post(
            f"{base_url}/api/enhanced-analysis/{test_event['id']}_fresh",
            json={'event': test_event},
            timeout=30
        )
        
        print(f"📡 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            analysis = response.json()
            metadata = analysis.get('metadata', {})
            cache_status = metadata.get('cache_status', 'unknown')
            
            print(f"💰 Cache Status: {cache_status}")
            
            if cache_status == 'fresh':
                print("✅ Successfully got fresh analysis!")
                print("   - Cache was cleared or bypassed")
                print("   - New ChatGPT analysis generated")
            else:
                print("⚠️ Still using cached analysis")
                print("   - Try using a different event ID")
                print("   - Or restart the backend server")
                
        else:
            print(f"❌ Failed to get analysis: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    clear_smart_cache()
