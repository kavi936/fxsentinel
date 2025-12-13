#!/usr/bin/env python3
"""
Test script for Analysis History functionality
"""

import sys
import os
sys.path.append('backend')

from services.analysis_history import analysis_history

def test_analysis_history():
    """Test the analysis history functionality"""
    
    print("🧪 Testing Analysis History System")
    print("=" * 50)
    
    # Test data
    test_news_item = {
        "id": "test_123",
        "title": "Test News Item",
        "source": "Test Source",
        "summary": "This is a test news item"
    }
    
    test_analysis = {
        "analysis_type": "free_enhanced",
        "confidence": 75,
        "immediate_reaction": "bullish_usd",
        "cost": 0.0,
        "news_impact": "Test news impact paragraph",
        "trading_implications": "Test trading implications paragraph"
    }
    
    # Test 1: Add analysis record
    print("\n📝 Test 1: Adding analysis record")
    success = analysis_history.add_analysis(test_news_item, test_analysis)
    print(f"✅ Analysis record added: {success}")
    
    # Test 2: Check if news is analyzed
    print("\n🔍 Test 2: Checking if news is analyzed")
    is_analyzed = analysis_history.is_news_analyzed("test_123")
    print(f"✅ News is analyzed: {is_analyzed}")
    
    # Test 3: Get analysis for news
    print("\n📊 Test 3: Getting analysis for news")
    analysis_data = analysis_history.get_analysis_for_news("test_123")
    print(f"✅ Analysis data retrieved: {analysis_data is not None}")
    if analysis_data:
        print(f"   - Type: {analysis_data.get('analysis_type')}")
        print(f"   - Confidence: {analysis_data.get('confidence')}")
        print(f"   - Reaction: {analysis_data.get('immediate_reaction')}")
    
    # Test 4: Get analysis history
    print("\n📈 Test 4: Getting analysis history")
    history = analysis_history.get_analysis_history(hours=24)
    print(f"✅ History items: {len(history)}")
    
    # Test 5: Get analysis stats
    print("\n📊 Test 5: Getting analysis stats")
    stats = analysis_history.get_analysis_stats()
    print(f"✅ Analysis stats:")
    print(f"   - Total analyses: {stats.get('total_analyses')}")
    print(f"   - Analysis types: {stats.get('analysis_types')}")
    print(f"   - Total cost: ${stats.get('total_cost')}")
    print(f"   - Average confidence: {stats.get('average_confidence')}%")
    
    # Test 6: Get analyzed news IDs
    print("\n🆔 Test 6: Getting analyzed news IDs")
    analyzed_ids = analysis_history.get_analyzed_news_ids()
    print(f"✅ Analyzed news IDs: {analyzed_ids}")
    
    print("\n" + "=" * 50)
    print("🎉 Analysis History Tests Completed!")

if __name__ == "__main__":
    test_analysis_history()
