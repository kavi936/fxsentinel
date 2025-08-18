#!/usr/bin/env python3
"""
Comprehensive Backend Services Test Script
Tests all main services: news, forex prices, AI analysis, live news, GPT connection
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

class ServiceTester:
    def __init__(self):
        self.results = {}
        self.start_time = datetime.now()
        
    def log_test(self, service_name, status, details=""):
        """Log test results"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        status_icon = "✅" if status else "❌"
        print(f"{timestamp} {status_icon} {service_name}: {'PASS' if status else 'FAIL'}")
        if details:
            print(f"    Details: {details}")
        
        self.results[service_name] = {
            "status": status,
            "details": details,
            "timestamp": timestamp
        }
    
    def test_server_health(self):
        """Test if the Flask server is running"""
        try:
            response = requests.get(f"{BASE_URL}/api/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log_test("Server Health", True, f"Status: {data.get('status', 'unknown')}")
                return True
            else:
                self.log_test("Server Health", False, f"Status code: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            self.log_test("Server Health", False, f"Connection error: {str(e)}")
            return False
    
    def test_api_status(self):
        """Test API status endpoint"""
        try:
            response = requests.get(f"{API_BASE}/api-status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log_test("API Status", True, f"APIs: {len(data.get('apis', []))} available")
                return True
            else:
                self.log_test("API Status", False, f"Status code: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            self.log_test("API Status", False, f"Connection error: {str(e)}")
            return False
    
    def test_cache_status(self):
        """Test cache status"""
        try:
            response = requests.get(f"{API_BASE}/cache-status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log_test("Cache Status", True, f"Cache entries: {len(data.get('caches', {}))}")
                return True
            else:
                self.log_test("Cache Status", False, f"Status code: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            self.log_test("Cache Status", False, f"Connection error: {str(e)}")
            return False
    
    def test_gpt_stats(self):
        """Test GPT connection and stats"""
        try:
            response = requests.get(f"{API_BASE}/gpt-stats", timeout=15)
            if response.status_code == 200:
                data = response.json()
                api_key_status = data.get('api_key_status', 'unknown')
                self.log_test("GPT Connection", api_key_status == 'valid', 
                             f"API Key: {api_key_status}, Calls: {data.get('total_calls', 0)}")
                return api_key_status == 'valid'
            else:
                self.log_test("GPT Connection", False, f"Status code: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            self.log_test("GPT Connection", False, f"Connection error: {str(e)}")
            return False
    
    def test_news_service(self):
        """Test news aggregation service"""
        try:
            response = requests.get(f"{API_BASE}/news", timeout=15)
            if response.status_code == 200:
                data = response.json()
                news_count = len(data.get('news', []))
                self.log_test("News Service", news_count > 0, f"Retrieved {news_count} news items")
                return news_count > 0
            else:
                self.log_test("News Service", False, f"Status code: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            self.log_test("News Service", False, f"Connection error: {str(e)}")
            return False
    
    def test_news_history(self):
        """Test news history service"""
        try:
            response = requests.get(f"{API_BASE}/news-history", timeout=10)
            if response.status_code == 200:
                data = response.json()
                history_count = len(data.get('news_history', []))
                self.log_test("News History", True, f"History entries: {history_count}")
                return True
            else:
                self.log_test("News History", False, f"Status code: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            self.log_test("News History", False, f"Connection error: {str(e)}")
            return False
    
    def test_forex_prices(self):
        """Test forex prices service"""
        try:
            response = requests.get(f"{API_BASE}/forex-prices", timeout=15)
            if response.status_code == 200:
                data = response.json()
                pairs_count = len(data.get('pairs', []))
                self.log_test("Forex Prices", pairs_count > 0, f"Retrieved {pairs_count} currency pairs")
                return pairs_count > 0
            else:
                self.log_test("Forex Prices", False, f"Status code: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            self.log_test("Forex Prices", False, f"Connection error: {str(e)}")
            return False
    
    def test_trading_data(self):
        """Test trading data service"""
        try:
            response = requests.get(f"{API_BASE}/trading-data", timeout=15)
            if response.status_code == 200:
                data = response.json()
                self.log_test("Trading Data", True, f"Data available: {len(data)} items")
                return True
            else:
                self.log_test("Trading Data", False, f"Status code: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            self.log_test("Trading Data", False, f"Connection error: {str(e)}")
            return False
    
    def test_economic_calendar(self):
        """Test economic calendar service"""
        try:
            response = requests.get(f"{API_BASE}/economic-calendar", timeout=15)
            if response.status_code == 200:
                data = response.json()
                events_count = len(data.get('events', []))
                self.log_test("Economic Calendar", events_count > 0, f"Retrieved {events_count} economic events")
                return events_count > 0
            else:
                self.log_test("Economic Calendar", False, f"Status code: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            self.log_test("Economic Calendar", False, f"Connection error: {str(e)}")
            return False
    
    def test_ai_analysis(self):
        """Test AI analysis service with a sample news item"""
        try:
            # First get a news item
            news_response = requests.get(f"{API_BASE}/news", timeout=10)
            if news_response.status_code == 200:
                news_data = news_response.json()
                news_items = news_data.get('news', [])
                
                if news_items:
                    # Test with the first news item
                    news_id = news_items[0].get('id', 1)
                    response = requests.get(f"{API_BASE}/enhanced-analysis/{news_id}", timeout=30)
                    
                    if response.status_code == 200:
                        data = response.json()
                        analysis_available = bool(data.get('analysis', {}))
                        self.log_test("AI Analysis", analysis_available, 
                                     f"Analysis generated for news ID {news_id}")
                        return analysis_available
                    else:
                        self.log_test("AI Analysis", False, f"Status code: {response.status_code}")
                        return False
                else:
                    self.log_test("AI Analysis", False, "No news items available for testing")
                    return False
            else:
                self.log_test("AI Analysis", False, "Could not fetch news for testing")
                return False
        except requests.exceptions.RequestException as e:
            self.log_test("AI Analysis", False, f"Connection error: {str(e)}")
            return False
    
    def test_ai_insights(self):
        """Test AI insights service"""
        try:
            response = requests.get(f"{API_BASE}/ai-insights", timeout=20)
            if response.status_code == 200:
                data = response.json()
                insights_count = len(data.get('insights', []))
                self.log_test("AI Insights", insights_count > 0, f"Generated {insights_count} insights")
                return insights_count > 0
            else:
                self.log_test("AI Insights", False, f"Status code: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            self.log_test("AI Insights", False, f"Connection error: {str(e)}")
            return False
    
    def test_dashboard_data(self):
        """Test dashboard data service"""
        try:
            response = requests.get(f"{API_BASE}/dashboard-data", timeout=15)
            if response.status_code == 200:
                data = response.json()
                self.log_test("Dashboard Data", True, f"Dashboard data available")
                return True
            else:
                self.log_test("Dashboard Data", False, f"Status code: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            self.log_test("Dashboard Data", False, f"Connection error: {str(e)}")
            return False
    
    def test_alerts_service(self):
        """Test alerts service"""
        try:
            response = requests.get(f"{API_BASE}/alerts", timeout=10)
            if response.status_code == 200:
                data = response.json()
                alerts_count = len(data.get('alerts', []))
                self.log_test("Alerts Service", True, f"Alerts available: {alerts_count}")
                return True
            else:
                self.log_test("Alerts Service", False, f"Status code: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            self.log_test("Alerts Service", False, f"Connection error: {str(e)}")
            return False
    
    def test_finnhub_connection(self):
        """Test Finnhub API connection"""
        try:
            response = requests.get(f"{API_BASE}/finnhub-test", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log_test("Finnhub Connection", True, f"Finnhub API working")
                return True
            else:
                self.log_test("Finnhub Connection", False, f"Status code: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            self.log_test("Finnhub Connection", False, f"Connection error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all service tests"""
        print("🚀 Starting Comprehensive Backend Services Test")
        print("=" * 60)
        
        # Core server tests
        if not self.test_server_health():
            print("❌ Server is not running. Please start the Flask server first.")
            return False
        
        # API and cache tests
        self.test_api_status()
        self.test_cache_status()
        
        # GPT and AI tests
        self.test_gpt_stats()
        
        # Data services tests
        self.test_news_service()
        self.test_news_history()
        self.test_forex_prices()
        self.test_trading_data()
        self.test_economic_calendar()
        
        # AI analysis tests
        self.test_ai_analysis()
        self.test_ai_insights()
        
        # Dashboard and alerts
        self.test_dashboard_data()
        self.test_alerts_service()
        
        # External API tests
        self.test_finnhub_connection()
        
        # Summary
        self.print_summary()
        
        return True
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results.values() if result['status'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for service, result in self.results.items():
                if not result['status']:
                    print(f"  - {service}: {result['details']}")
        
        print(f"\n⏱️  Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️  Total duration: {datetime.now() - self.start_time}")

def main():
    """Main function"""
    tester = ServiceTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
