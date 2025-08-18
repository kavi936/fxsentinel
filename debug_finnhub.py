#!/usr/bin/env python3
"""
Debug script for Finnhub historical service
"""

import os
import sys
sys.path.append('backend')

from services.finnhub_historical import FinnhubHistoricalService

def debug_finnhub_service():
    """Debug the Finnhub historical service"""
    print("🔍 Debugging Finnhub Historical Service...")
    
    # Set API key
    api_key = os.getenv('FINNHUB_API_KEY')
    if not api_key:
        print("❌ FINNHUB_API_KEY environment variable not set!")
        return
    os.environ['FINNHUB_API_KEY'] = api_key
    
    # Create service
    service = FinnhubHistoricalService()
    
    # Test different indicators
    test_indicators = ['CPI', 'GDP', 'Unemployment', 'Employment', 'Retail Sales']
    
    for indicator in test_indicators:
        print(f"\n📊 Testing {indicator}:")
        try:
            data = service.get_historical_data_for_indicator(indicator, 12)
            print(f"✅ Found {len(data)} data points for {indicator}")
            
            if data:
                print("Sample data:")
                for i, point in enumerate(data[:3]):
                    print(f"  {i+1}. {point['date']}: {point['value']} {point['unit']} ({point['event_name']})")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_finnhub_service()
