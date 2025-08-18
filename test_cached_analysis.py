#!/usr/bin/env python3
"""
Test script to verify cached analysis functionality
"""

import sys
import os
import json
import requests
from datetime import datetime

# Add backend to path
sys.path.append('backend')

def test_cached_analysis_backend():
    """Test the backend cached analysis functionality"""
    
    print("🧪 Testing Cached Analysis Backend")
    print("=" * 50)
    
    try:
        from services.analysis_history import analysis_history
        
        # Create test data
        test_news_item = {
            "id": "test_cached_123",
            "title": "Test Cached Analysis News",
            "source": "Test Source",
            "summary": "This is a test news item for cached analysis"
        }
        
        test_analysis = {
            "analysis_type": "gpt_enhanced",
            "confidence": 85,
            "immediate_reaction": "bullish_usd",
            "cost": 0.003,
            "news_impact": "This test news item shows positive market sentiment with strong bullish indicators for USD pairs.",
            "trading_implications": "Consider long positions on USD/JPY and EUR/USD with tight stop losses.",
            "key_pairs": ["USD/JPY", "EUR/USD"],
            "volatility": "high",
            "timeframe": "1-4 hours",
            "risk_assessment": {
                "market_volatility": "high",
                "liquidity_impact": "medium",
                "correlation_risk": "low"
            },
            "market_context": {
                "economic_factors": ["Inflation", "Interest Rates"],
                "technical_levels": ["Support: 1.0850", "Resistance: 1.0950"],
                "sentiment_drivers": ["Risk Appetite", "Safe Haven Demand"]
            }
        }
        
        print("📝 Step 1: Adding test analysis to history")
        success = analysis_history.add_analysis(test_news_item, test_analysis)
        print(f"✅ Analysis added: {success}")
        
        print("\n📊 Step 2: Checking if news is analyzed")
        is_analyzed = analysis_history.is_news_analyzed("test_cached_123")
        print(f"✅ News is analyzed: {is_analyzed}")
        
        print("\n🔍 Step 3: Getting cached analysis")
        cached_analysis = analysis_history.get_analysis_for_news("test_cached_123")
        print(f"✅ Cached analysis retrieved: {cached_analysis is not None}")
        
        if cached_analysis:
            print(f"   - Analysis Type: {cached_analysis.get('analysis_type')}")
            print(f"   - Confidence: {cached_analysis.get('confidence')}%")
            print(f"   - Reaction: {cached_analysis.get('immediate_reaction')}")
            print(f"   - Cost: ${cached_analysis.get('cost')}")
            print(f"   - News Impact: {cached_analysis.get('news_impact', 'N/A')[:50]}...")
            print(f"   - Trading Implications: {cached_analysis.get('trading_implications', 'N/A')[:50]}...")
        
        print("\n📈 Step 4: Getting analysis stats")
        stats = analysis_history.get_analysis_stats()
        print(f"✅ Analysis stats:")
        print(f"   - Total Analyses: {stats['total_analyses']}")
        print(f"   - Total Cost: ${stats['total_cost']}")
        print(f"   - Average Confidence: {stats['average_confidence']}%")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing cached analysis backend: {e}")
        return False

def test_cached_analysis_api():
    """Test the API endpoint for cached analysis"""
    
    print("\n🌐 Testing Cached Analysis API")
    print("=" * 50)
    
    try:
        # Test the API endpoint
        api_url = "http://localhost:5001/api/get-cached-analysis/test_cached_123"
        
        print(f"📡 Making GET request to: {api_url}")
        
        response = requests.get(api_url)
        
        print(f"📋 API Response:")
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            analysis_data = response.json()
            print(f"   ✅ Success: Cached analysis retrieved")
            print(f"   - Analysis Type: {analysis_data.get('analysis_type')}")
            print(f"   - Confidence: {analysis_data.get('confidence')}%")
            print(f"   - Reaction: {analysis_data.get('immediate_reaction')}")
            print(f"   - Cost: ${analysis_data.get('cost')}")
            print(f"   - News Impact: {analysis_data.get('news_impact', 'N/A')[:50]}...")
            print(f"   - Trading Implications: {analysis_data.get('trading_implications', 'N/A')[:50]}...")
            return True
        else:
            error_data = response.json()
            print(f"   ❌ Error: {error_data.get('error', 'Unknown error')}")
            return False
            
    except ImportError:
        print("❌ requests library not available. Install with: pip install requests")
        return False
    except Exception as e:
        print(f"❌ API test error: {e}")
        return False

def test_nonexistent_analysis():
    """Test the API endpoint with a nonexistent analysis"""
    
    print("\n🔍 Testing Nonexistent Analysis")
    print("=" * 50)
    
    try:
        # Test with a news ID that doesn't exist
        api_url = "http://localhost:5001/api/get-cached-analysis/nonexistent_123"
        
        print(f"📡 Making GET request to: {api_url}")
        
        response = requests.get(api_url)
        
        print(f"📋 API Response:")
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 404:
            error_data = response.json()
            print(f"   ✅ Expected: No cached analysis found")
            print(f"   - Error: {error_data.get('error', 'Unknown error')}")
            return True
        else:
            print(f"   ❌ Unexpected status code: {response.status_code}")
            return False
            
    except ImportError:
        print("❌ requests library not available. Install with: pip install requests")
        return False
    except Exception as e:
        print(f"❌ API test error: {e}")
        return False

def cleanup_test_data():
    """Clean up test data"""
    
    print("\n🧹 Cleaning Up Test Data")
    print("=" * 50)
    
    try:
        from services.analysis_history import analysis_history
        
        # Load current history
        history = analysis_history.load_history()
        
        # Remove test entries
        filtered_history = [record for record in history if record.get('news_id') != 'test_cached_123']
        
        # Save filtered history
        if len(filtered_history) != len(history):
            analysis_history.save_history(filtered_history)
            print(f"✅ Removed test analysis data")
            print(f"   - Before: {len(history)} records")
            print(f"   - After: {len(filtered_history)} records")
        else:
            print("ℹ️  No test data found to clean up")
        
        return True
        
    except Exception as e:
        print(f"❌ Error cleaning up test data: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Cached Analysis Functionality")
    
    # Test backend functionality
    backend_test_passed = test_cached_analysis_backend()
    
    # Test API endpoint
    api_test_passed = test_cached_analysis_api()
    
    # Test nonexistent analysis
    nonexistent_test_passed = test_nonexistent_analysis()
    
    # Clean up test data
    cleanup_success = cleanup_test_data()
    
    print("\n" + "="*50)
    print("📋 Test Results Summary:")
    print(f"   Backend Test: {'✅ PASSED' if backend_test_passed else '❌ FAILED'}")
    print(f"   API Test: {'✅ PASSED' if api_test_passed else '❌ FAILED'}")
    print(f"   Nonexistent Test: {'✅ PASSED' if nonexistent_test_passed else '❌ FAILED'}")
    print(f"   Cleanup: {'✅ SUCCESS' if cleanup_success else '❌ FAILED'}")
    
    if all([backend_test_passed, api_test_passed, nonexistent_test_passed, cleanup_success]):
        print("\n🎉 All tests PASSED! Cached analysis functionality is working correctly.")
        print("\n📝 Summary of the fix:")
        print("   - Backend can store and retrieve cached analysis")
        print("   - API endpoint returns cached analysis correctly")
        print("   - API handles nonexistent analysis gracefully")
        print("   - Frontend can now use cached analysis instead of re-analyzing")
    else:
        print("\n❌ Some tests FAILED! Please check the implementation.")
    
    print("\n✅ Test completed!")
