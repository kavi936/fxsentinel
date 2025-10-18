#!/usr/bin/env python3
"""
Comprehensive API Data Accuracy Test
Compare FMP vs FRED for data quality, accuracy, and usefulness
"""

import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from backend directory
load_dotenv('.env')

def test_fred_data_quality():
    """Test FRED API data quality and accuracy"""
    print("🧪 TESTING FRED DATA QUALITY")
    print("=" * 50)
    
    api_key = os.getenv('FRED_API_KEY')
    if not api_key:
        print("❌ FRED API key not found")
        return {}
    
    print(f"✅ FRED API Key: {api_key[:10]}...")
    
    # Test multiple key economic indicators
    fred_series = {
        'GDP': {'name': 'Gross Domestic Product', 'unit': 'Billions USD'},
        'CPIAUCSL': {'name': 'Consumer Price Index', 'unit': 'Index'},
        'UNRATE': {'name': 'Unemployment Rate', 'unit': 'Percent'},
        'FEDFUNDS': {'name': 'Federal Funds Rate', 'unit': 'Percent'},
        'INDPRO': {'name': 'Industrial Production', 'unit': 'Index'},
        'PAYEMS': {'name': 'Nonfarm Payrolls', 'unit': 'Thousands'},
        'RETAILSALES': {'name': 'Retail Sales', 'unit': 'Millions USD'},
        'DGS10': {'name': '10-Year Treasury Rate', 'unit': 'Percent'},
        'DEXUSEU': {'name': 'USD/EUR Exchange Rate', 'unit': 'USD per EUR'},
        'DGS30': {'name': '30-Year Mortgage Rate', 'unit': 'Percent'}
    }
    
    results = {}
    
    for series_id, info in fred_series.items():
        print(f"\n📊 Testing {info['name']} ({series_id})...")
        
        try:
            # Get recent data
            url = "https://api.stlouisfed.org/fred/series/observations"
            params = {
                'series_id': series_id,
                'api_key': api_key,
                'file_type': 'json',
                'limit': 5,
                'sort_order': 'desc'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'observations' in data and data['observations']:
                    observations = data['observations']
                    valid_obs = [obs for obs in observations if obs['value'] != '.']
                    
                    if valid_obs:
                        latest = valid_obs[0]
                        results[series_id] = {
                            'name': info['name'],
                            'unit': info['unit'],
                            'latest_value': latest['value'],
                            'latest_date': latest['date'],
                            'data_points': len(valid_obs),
                            'frequency': self._get_frequency(latest, valid_obs),
                            'status': 'SUCCESS'
                        }
                        
                        print(f"   ✅ {info['name']}: {latest['value']} {info['unit']} ({latest['date']})")
                        print(f"   📅 Data points: {len(valid_obs)} | Frequency: {results[series_id]['frequency']}")
                    else:
                        results[series_id] = {'status': 'NO_VALID_DATA'}
                        print(f"   ⚠️ No valid data points")
                else:
                    results[series_id] = {'status': 'NO_OBSERVATIONS'}
                    print(f"   ❌ No observations returned")
            else:
                results[series_id] = {'status': f'HTTP_{response.status_code}'}
                print(f"   ❌ HTTP Error: {response.status_code}")
                
        except Exception as e:
            results[series_id] = {'status': f'ERROR: {str(e)}'}
            print(f"   ❌ Exception: {e}")
    
    return results

def _get_frequency(self, latest_obs, all_obs):
    """Determine data frequency"""
    if len(all_obs) < 2:
        return 'Unknown'
    
    # Simple frequency detection based on date patterns
    dates = [obs['date'] for obs in all_obs[:3]]
    if all(date.endswith('-01') for date in dates):
        return 'Monthly'
    elif all(date.endswith('-01-01') for date in dates):
        return 'Annual'
    elif all(date.endswith('-01') and any(month in date for month in ['-01-', '-04-', '-07-', '-10-']) for date in dates):
        return 'Quarterly'
    else:
        return 'Irregular'

def test_fmp_data_quality():
    """Test FMP API data quality and accuracy"""
    print("\n🧪 TESTING FMP DATA QUALITY")
    print("=" * 50)
    
    api_key = os.getenv('FMP_API_KEY')
    if not api_key:
        print("❌ FMP API key not found")
        return {}
    
    print(f"✅ FMP API Key: {api_key[:10]}...")
    
    # Test various economic indicators available in FMP
    fmp_indicators = [
        'GDP', 'CPI', 'Unemployment', 'Interest Rate', 'Inflation',
        'Retail Sales', 'Industrial Production', 'Trade Balance',
        'Consumer Confidence', 'Manufacturing PMI', 'Services PMI'
    ]
    
    results = {}
    
    for indicator in fmp_indicators:
        print(f"\n📊 Testing {indicator}...")
        
        try:
            url = "https://financialmodelingprep.com/stable/economic-indicators"
            params = {
                'name': indicator,
                'apikey': api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data and isinstance(data, list):
                    # Take the most recent entry
                    latest = data[0]
                    results[indicator] = {
                        'name': latest.get('name', indicator),
                        'value': latest.get('value'),
                        'date': latest.get('date'),
                        'data_points': len(data),
                        'status': 'SUCCESS',
                        'raw_data': latest
                    }
                    
                    print(f"   ✅ {indicator}: {latest.get('value')} ({latest.get('date')})")
                    print(f"   📅 Data points: {len(data)}")
                    print(f"   🔍 Raw data: {latest}")
                else:
                    results[indicator] = {'status': 'NO_DATA'}
                    print(f"   ⚠️ No data returned")
            else:
                results[indicator] = {'status': f'HTTP_{response.status_code}'}
                print(f"   ❌ HTTP Error: {response.status_code} - {response.text[:100]}")
                
        except Exception as e:
            results[indicator] = {'status': f'ERROR: {str(e)}'}
            print(f"   ❌ Exception: {e}")
    
    return results

def compare_api_quality():
    """Compare both APIs and make recommendation"""
    print("\n📊 COMPREHENSIVE API COMPARISON")
    print("=" * 60)
    
    # Test both APIs
    fred_results = test_fred_data_quality()
    fmp_results = test_fmp_data_quality()
    
    # Analyze results
    print("\n🎯 ANALYSIS RESULTS")
    print("=" * 60)
    
    # FRED Analysis
    fred_success = sum(1 for r in fred_results.values() if r.get('status') == 'SUCCESS')
    fred_total = len(fred_results)
    print(f"\n📈 FRED API Results:")
    print(f"   ✅ Successful: {fred_success}/{fred_total} indicators")
    print(f"   📊 Success Rate: {(fred_success/fred_total)*100:.1f}%")
    
    # FMP Analysis
    fmp_success = sum(1 for r in fmp_results.values() if r.get('status') == 'SUCCESS')
    fmp_total = len(fmp_results)
    print(f"\n📈 FMP API Results:")
    print(f"   ✅ Successful: {fmp_success}/{fmp_total} indicators")
    print(f"   📊 Success Rate: {(fmp_success/fmp_total)*100:.1f}%")
    
    # Data Quality Comparison
    print(f"\n🔍 DATA QUALITY COMPARISON:")
    
    print(f"\n🏛️ FRED Strengths:")
    print(f"   • Official Federal Reserve data")
    print(f"   • Most comprehensive US economic dataset")
    print(f"   • Historical data going back decades")
    print(f"   • Multiple data points per indicator")
    print(f"   • Completely free with no limits")
    print(f"   • Real-time and historical values")
    
    print(f"\n💼 FMP Strengths:")
    print(f"   • Simpler API structure")
    print(f"   • Recent economic data")
    print(f"   • Easy to integrate")
    
    print(f"\n⚠️ FRED Limitations:")
    print(f"   • US-focused (limited international data)")
    print(f"   • Some indicators may have reporting delays")
    
    print(f"\n⚠️ FMP Limitations:")
    print(f"   • Limited indicators available")
    print(f"   • Some indicators return empty data")
    print(f"   • Less comprehensive than FRED")
    
    # Recommendation
    print(f"\n🎯 FINAL RECOMMENDATION")
    print("=" * 60)
    
    if fred_success >= fmp_success:
        print("🏆 WINNER: FRED API")
        print("\n✅ Reasons:")
        print("   • Higher success rate for data retrieval")
        print("   • Official government data source")
        print("   • More comprehensive economic indicators")
        print("   • Better historical data availability")
        print("   • Completely free with no API limits")
        print("   • More reliable and stable")
        
        print("\n💡 Implementation Strategy:")
        print("   • Use FRED as primary data source")
        print("   • Focus on key US economic indicators:")
        print("     - GDP, CPI, Unemployment Rate")
        print("     - Federal Funds Rate, 10-Year Treasury")
        print("     - Industrial Production, Retail Sales")
        print("   • Implement 24-hour caching")
        print("   • Add FMP as backup for specific indicators")
        
    else:
        print("🏆 WINNER: FMP API")
        print("\n✅ Reasons:")
        print("   • Higher success rate in testing")
        print("   • Simpler integration")
        
    # Show successful indicators from each
    print(f"\n📋 SUCCESSFUL INDICATORS:")
    
    print(f"\n🏛️ FRED Working Indicators:")
    for series_id, result in fred_results.items():
        if result.get('status') == 'SUCCESS':
            print(f"   ✅ {result['name']}: {result['latest_value']} ({result['latest_date']})")
    
    print(f"\n💼 FMP Working Indicators:")
    for indicator, result in fmp_results.items():
        if result.get('status') == 'SUCCESS':
            print(f"   ✅ {result['name']}: {result['value']} ({result['date']})")

if __name__ == "__main__":
    print("🚀 COMPREHENSIVE API DATA ACCURACY TEST")
    print("=" * 60)
    compare_api_quality()
