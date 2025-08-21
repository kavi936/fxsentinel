#!/usr/bin/env python3
"""
Test Process Monitoring and Alert Quality Enhancement Systems
Comprehensive testing of both new systems
"""

import requests
import json
import time
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BASE_URL = "http://localhost:5001"
API_BASE = f"{BASE_URL}/api"

def test_process_monitoring():
    """Test the process monitoring system"""
    print("\n🔍 TESTING PROCESS MONITORING SYSTEM")
    print("=" * 50)
    
    # Test 1: Basic health check
    print("\n1️⃣ Testing Basic Health Check")
    try:
        response = requests.get(f"{API_BASE}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Basic Health: {data['status']}")
        else:
            print(f"❌ Basic Health Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Basic Health Error: {e}")
    
    # Test 2: Alert system health
    print("\n2️⃣ Testing Alert System Health")
    try:
        response = requests.get(f"{API_BASE}/health/alerts", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Alert System: {data['status']}")
            print(f"   Telegram Bot: {data.get('telegram_bot', 'unknown')}")
            print(f"   Firebase: {data.get('firebase', 'unknown')}")
        else:
            print(f"❌ Alert System Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Alert System Error: {e}")
    
    # Test 3: Telegram monitor health
    print("\n3️⃣ Testing Telegram Monitor Health")
    try:
        response = requests.get(f"{API_BASE}/health/telegram", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Telegram Monitor: {data['status']}")
            print(f"   Monitor Status: {data.get('monitor_status', 'unknown')}")
        else:
            print(f"❌ Telegram Monitor Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Telegram Monitor Error: {e}")
    
    # Test 4: Economic calendar health
    print("\n4️⃣ Testing Economic Calendar Health")
    try:
        response = requests.get(f"{API_BASE}/health/calendar", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Economic Calendar: {data['status']}")
        else:
            print(f"❌ Economic Calendar Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Economic Calendar Error: {e}")
    
    # Test 5: News aggregator health
    print("\n5️⃣ Testing News Aggregator Health")
    try:
        response = requests.get(f"{API_BASE}/health/news", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ News Aggregator: {data['status']}")
        else:
            print(f"❌ News Aggregator Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ News Aggregator Error: {e}")
    
    # Test 6: AI analysis health
    print("\n6️⃣ Testing AI Analysis Health")
    try:
        response = requests.get(f"{API_BASE}/health/ai", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ AI Analysis: {data['status']}")
        else:
            print(f"❌ AI Analysis Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ AI Analysis Error: {e}")
    
    # Test 7: Complete system health
    print("\n7️⃣ Testing Complete System Health")
    try:
        response = requests.get(f"{API_BASE}/health/system", timeout=15)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ System Health: {data['status']}")
            
            summary = data.get('summary', {})
            print(f"   Total Processes: {summary.get('total_processes', 0)}")
            print(f"   Running Processes: {summary.get('running_processes', 0)}")
            print(f"   Critical Processes: {summary.get('critical_processes', 0)}")
            print(f"   Critical Running: {summary.get('critical_running', 0)}")
            
            # Show individual process status
            processes = data.get('processes', {})
            for process_id, process_data in processes.items():
                status_icon = "✅" if process_data.get('is_running', False) else "❌"
                print(f"   {status_icon} {process_data.get('name', process_id)}: {process_data.get('status_message', 'Unknown')}")
        else:
            print(f"❌ System Health Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ System Health Error: {e}")

def test_alert_quality_enhancement():
    """Test the alert quality enhancement system"""
    print("\n🎯 TESTING ALERT QUALITY ENHANCEMENT SYSTEM")
    print("=" * 50)
    
    # Import the quality enhancer
    try:
        import sys
        sys.path.append('backend')
        from services.alert_quality_enhancer import alert_quality_enhancer
        
        print("✅ Alert Quality Enhancer imported successfully")
    except Exception as e:
        print(f"❌ Failed to import Alert Quality Enhancer: {e}")
        return
    
    # Test 1: High-quality news evaluation
    print("\n1️⃣ Testing High-Quality News Evaluation")
    high_quality_news = {
        'id': 'test_high_001',
        'title': 'Federal Reserve Raises Interest Rates by 25 Basis Points',
        'summary': 'The Federal Reserve announced a 25-basis-point rate hike, bringing the target range to 5.25%-5.50%.',
        'content': 'The Federal Reserve has raised interest rates by 25 basis points in a move that was widely expected by markets. This dovish hike suggests the Fed is nearing the end of its tightening cycle.',
        'source': 'Reuters',
        'published_at': datetime.now().isoformat(),
        'impact': 'high',
        'type': 'liveNews'
    }
    
    user_preferences = {
        'user_id': 'test_user_001',
        'currencyPairs': ['EUR/USD', 'USD/JPY', 'GBP/USD'],
        'impactLevels': {'high': True, 'medium': True, 'low': False},
        'alertTypes': {'liveNews': True, 'preNews': True, 'postNews': True},
        'quietHours': {'enabled': False}
    }
    
    try:
        quality_score = alert_quality_enhancer.evaluate_alert_quality(high_quality_news, user_preferences)
        
        print(f"✅ High-Quality News Score: {quality_score.overall_score:.2f}")
        print(f"   Relevance: {quality_score.relevance_score:.2f}")
        print(f"   Urgency: {quality_score.urgency_score:.2f}")
        print(f"   Credibility: {quality_score.credibility_score:.2f}")
        print(f"   Actionability: {quality_score.actionability_score:.2f}")
        
        should_send, reason = alert_quality_enhancer.should_send_alert(quality_score, user_preferences)
        print(f"   Should Send: {'✅ Yes' if should_send else '❌ No'}")
        print(f"   Reason: {reason}")
        
        # Get quality insights
        insights = alert_quality_enhancer.get_quality_insights(quality_score)
        print(f"   Quality Level: {insights['overall_quality']}")
        if insights['strengths']:
            print(f"   Strengths: {', '.join(insights['strengths'])}")
        
    except Exception as e:
        print(f"❌ High-Quality News Test Error: {e}")
    
    # Test 2: Low-quality news evaluation
    print("\n2️⃣ Testing Low-Quality News Evaluation")
    low_quality_news = {
        'id': 'test_low_001',
        'title': 'Daily Market Wrap: Stocks End Mixed',
        'summary': 'A summary of today\'s market activity with no specific forex implications.',
        'content': 'Markets were mixed today with no significant forex movements. Regular daily update.',
        'source': 'unknown_source',
        'published_at': datetime.now().isoformat(),
        'impact': 'low',
        'type': 'liveNews'
    }
    
    try:
        quality_score = alert_quality_enhancer.evaluate_alert_quality(low_quality_news, user_preferences)
        
        print(f"✅ Low-Quality News Score: {quality_score.overall_score:.2f}")
        print(f"   Relevance: {quality_score.relevance_score:.2f}")
        print(f"   Urgency: {quality_score.urgency_score:.2f}")
        print(f"   Credibility: {quality_score.credibility_score:.2f}")
        print(f"   Actionability: {quality_score.actionability_score:.2f}")
        
        should_send, reason = alert_quality_enhancer.should_send_alert(quality_score, user_preferences)
        print(f"   Should Send: {'✅ Yes' if should_send else '❌ No'}")
        print(f"   Reason: {reason}")
        
    except Exception as e:
        print(f"❌ Low-Quality News Test Error: {e}")
    
    # Test 3: User feedback recording
    print("\n3️⃣ Testing User Feedback Recording")
    try:
        # Record some test feedback
        alert_quality_enhancer.record_user_feedback('test_news_001', 'test_user_001', 0.9)
        alert_quality_enhancer.record_user_feedback('test_news_001', 'test_user_001', 0.8)
        alert_quality_enhancer.record_user_feedback('test_news_002', 'test_user_001', 0.3)
        
        print("✅ User feedback recorded successfully")
        
        # Test feedback score retrieval
        feedback_score = alert_quality_enhancer._get_user_feedback_score('test_news_001', 'test_user_001')
        print(f"   Feedback Score for test_news_001: {feedback_score:.2f}")
        
    except Exception as e:
        print(f"❌ User Feedback Test Error: {e}")
    
    # Test 4: Source credibility scoring
    print("\n4️⃣ Testing Source Credibility Scoring")
    try:
        sources = ['reuters', 'bloomberg', 'cnbc', 'unknown_source']
        
        for source in sources:
            credibility = alert_quality_enhancer.source_credibility.get(source, 0.5)
            print(f"   {source}: {credibility:.2f}")
        
        print("✅ Source credibility scoring working")
        
    except Exception as e:
        print(f"❌ Source Credibility Test Error: {e}")

def test_integration():
    """Test integration between monitoring and quality systems"""
    print("\n🔗 TESTING SYSTEM INTEGRATION")
    print("=" * 50)
    
    # Test 1: Process monitor with quality enhancer
    print("\n1️⃣ Testing Process Monitor with Quality Enhancer")
    try:
        import sys
        sys.path.append('backend')
        from services.process_monitor import process_monitor
        from services.alert_quality_enhancer import alert_quality_enhancer
        
        # Get system status
        system_status = process_monitor.get_system_status()
        print(f"✅ System Status: {system_status['overall_status']}")
        print(f"   Critical Processes Running: {system_status['critical_running']}/{system_status['critical_processes']}")
        
        # Test quality enhancer is working
        test_news = {
            'id': 'integration_test',
            'title': 'ECB Interest Rate Decision',
            'summary': 'European Central Bank announces monetary policy decision',
            'source': 'Reuters',
            'published_at': datetime.now().isoformat()
        }
        
        test_preferences = {
            'user_id': 'integration_user',
            'currencyPairs': ['EUR/USD'],
            'impactLevels': {'high': True},
            'alertTypes': {'liveNews': True}
        }
        
        quality_score = alert_quality_enhancer.evaluate_alert_quality(test_news, test_preferences)
        print(f"✅ Quality Enhancement Working: Score {quality_score.overall_score:.2f}")
        
    except Exception as e:
        print(f"❌ Integration Test Error: {e}")

def main():
    """Main test function"""
    print("🚀 FXSentinel Process Monitoring & Alert Quality Enhancement Test")
    print("=" * 70)
    print(f"Test started at: {datetime.now().isoformat()}")
    
    # Test process monitoring
    test_process_monitoring()
    
    # Test alert quality enhancement
    test_alert_quality_enhancement()
    
    # Test integration
    test_integration()
    
    print("\n" + "=" * 70)
    print("✅ All tests completed!")
    print(f"Test finished at: {datetime.now().isoformat()}")

if __name__ == "__main__":
    main()
