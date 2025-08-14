#!/usr/bin/env python3
"""
Script to clear the GPT analyzer cache
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to the path so we can import our modules
sys.path.append('.')

from services.gpt_ai_analysis import gpt_ai_analyzer

def clear_gpt_cache():
    """Clear the GPT analyzer cache"""
    
    print("🧹 Clearing GPT Analyzer Cache")
    print("=" * 40)
    
    # Clear in-memory cache
    if hasattr(gpt_ai_analyzer, 'memory_cache'):
        gpt_ai_analyzer.memory_cache.clear()
        print("✅ In-memory cache cleared")
    
    if hasattr(gpt_ai_analyzer, 'cache_timestamps'):
        gpt_ai_analyzer.cache_timestamps.clear()
        print("✅ Cache timestamps cleared")
    
    # Clear Redis cache if available
    if gpt_ai_analyzer.redis_client:
        try:
            gpt_ai_analyzer.redis_client.flushdb()
            print("✅ Redis cache cleared")
        except Exception as e:
            print(f"⚠️ Could not clear Redis cache: {e}")
    
    # Reset rate limiting
    if hasattr(gpt_ai_analyzer, 'api_calls_this_hour'):
        gpt_ai_analyzer.api_calls_this_hour = 0
        print("✅ Rate limiting reset")
    
    print("🎉 Cache clearing completed!")

if __name__ == "__main__":
    clear_gpt_cache()
