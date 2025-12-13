#!/usr/bin/env python3

import sys
import os
sys.path.append('backend')

try:
    from services.market_sentiment_service import market_sentiment_service
    print("✅ Successfully imported market sentiment service")
    
    # Test market status check
    market_status = market_sentiment_service._check_market_status()
    print(f"Market status: {market_status}")
    
    # Test getting sentiment
    sentiment = market_sentiment_service.get_market_sentiment()
    print(f"Is market closed: {sentiment.get('is_market_closed')}")
    print(f"Market status: {sentiment.get('market_status')}")
    print(f"Market outlook: {sentiment.get('market_outlook', '')[:100]}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
