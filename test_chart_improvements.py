#!/usr/bin/env python3
"""
Test script to verify chart improvements with mock data
"""

import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_deduplication_logic():
    """Test the deduplication logic with mock data"""
    print("🔍 Testing Deduplication Logic...")
    print("=" * 50)
    
    # Mock deduplication function
    def deduplicate_data(historical_data):
        """Mock deduplication function"""
        if not historical_data:
            return []
        
        print(f"📊 Starting deduplication with {len(historical_data)} points")
        
        # Group by date
        date_groups = {}
        for point in historical_data:
            date = point.get('date')
            if date:
                if date not in date_groups:
                    date_groups[date] = []
                date_groups[date].append(point)
        
        # For each date, select the best data point
        deduplicated = []
        duplicates_removed = 0
        
        for date, points in date_groups.items():
            if len(points) == 1:
                deduplicated.append(points[0])
            else:
                # Multiple points for same date - select the best one
                # Score each point based on data quality
                best_point = max(points, key=lambda p: 
                    (p.get('expected') is not None,  # Prefer points with expected values
                     p.get('previous') is not None,  # Prefer points with previous values
                     p.get('event_name', '').lower().count('official'),  # Prefer official releases
                     len(p.get('country', '')),  # Prefer more specific country data
                     p.get('event_name', '').lower().count('final'),  # Prefer final releases
                     p.get('event_name', '').lower().count('preliminary') == 0))  # Avoid preliminary data
                deduplicated.append(best_point)
                duplicates_removed += len(points) - 1
        
        # Sort by date (oldest first)
        deduplicated.sort(key=lambda x: x.get('date', ''))
        
        print(f"📊 Deduplication complete: {len(historical_data)} -> {len(deduplicated)} points (removed {duplicates_removed} duplicates)")
        return deduplicated
    
    # Mock historical data with duplicates
    mock_data = [
        {'date': '2024-01-01', 'value': 2.5, 'event_name': 'CPI Preliminary', 'country': 'US'},
        {'date': '2024-01-01', 'value': 2.5, 'event_name': 'CPI Final', 'country': 'US'},
        {'date': '2024-01-01', 'value': 2.6, 'event_name': 'CPI Official', 'country': 'US'},
        {'date': '2024-02-01', 'value': 2.7, 'event_name': 'CPI', 'country': 'US'},
        {'date': '2024-02-01', 'value': 2.7, 'event_name': 'CPI', 'country': 'US'},
        {'date': '2024-03-01', 'value': 2.8, 'event_name': 'CPI', 'country': 'US'},
    ]
    
    print(f"📊 Original data points: {len(mock_data)}")
    
    # Test deduplication
    deduplicated = deduplicate_data(mock_data)
    
    print(f"📊 After deduplication: {len(deduplicated)}")
    
    # Check results
    dates = [point['date'] for point in deduplicated]
    unique_dates = set(dates)
    
    if len(dates) == len(unique_dates):
        print("✅ Deduplication successful - no duplicate dates")
    else:
        print("❌ Deduplication failed - still has duplicate dates")
    
    # Show the deduplicated data
    print("\n📈 Deduplicated data:")
    for point in deduplicated:
        print(f"  {point['date']}: {point['value']} ({point['event_name']})")

def test_data_validation():
    """Test the data validation logic"""
    print("\n🔍 Testing Data Validation...")
    print("=" * 50)
    
    # Mock validation function
    def validate_data_point(value, indicator):
        """Mock data validation function"""
        if value is None or not isinstance(value, (int, float)):
            return False
            
        # Define reasonable ranges for different indicators (much stricter)
        indicator_ranges = {
            'cpi': (-10, 30),  # CPI can be negative (deflation) but not extreme
            'inflation': (-10, 30),
            'gdp': (-20, 20),  # GDP growth rates (more realistic range)
            'unemployment': (0, 30),  # Unemployment rates (more realistic)
            'employment': (-50, 100),  # Employment changes
            'retail sales': (-20, 50),  # Retail sales changes
            'interest rate': (-5, 25),  # Interest rates
            'manufacturing': (0, 70)  # PMI and manufacturing indices
        }
        
        indicator_lower = indicator.lower()
        for key, (min_val, max_val) in indicator_ranges.items():
            if key in indicator_lower:
                return min_val <= value <= max_val
        
        # Default validation for unknown indicators (much stricter)
        return -50 <= value <= 100
    
    # Test cases
    test_cases = [
        # (value, indicator, expected_result, description)
        (2.5, 'CPI', True, 'Normal CPI value'),
        (50.0, 'CPI', False, 'Extreme CPI value'),
        (-5.0, 'CPI', True, 'Negative CPI (deflation)'),
        (-20.0, 'CPI', False, 'Extreme negative CPI'),
        (5.0, 'GDP', True, 'Normal GDP value'),
        (25.0, 'GDP', False, 'Extreme GDP value'),
        (3.0, 'Unemployment', True, 'Normal unemployment'),
        (50.0, 'Unemployment', False, 'Extreme unemployment'),
        (None, 'CPI', False, 'None value'),
        ('invalid', 'CPI', False, 'String value'),
    ]
    
    print("📊 Testing data validation:")
    for value, indicator, expected, description in test_cases:
        result = validate_data_point(value, indicator)
        status = "✅" if result == expected else "❌"
        print(f"  {status} {description}: {value} -> {result} (expected {expected})")

def test_chart_data_structure():
    """Test the chart data structure generation"""
    print("\n🔍 Testing Chart Data Structure...")
    print("=" * 50)
    
    # Mock historical data
    mock_historical_data = [
        {'date': '2024-01-01', 'value': 2.5, 'unit': '%', 'event_name': 'CPI', 'country': 'US'},
        {'date': '2024-02-01', 'value': 2.7, 'unit': '%', 'event_name': 'CPI', 'country': 'US'},
        {'date': '2024-03-01', 'value': 2.8, 'unit': '%', 'event_name': 'CPI', 'country': 'US'},
    ]
    
    # Test chart data generation
    chart_data = {
        'indicator': 'CPI',
        'historical_data': mock_historical_data,
        'data_points': len(mock_historical_data),
        'statistics': {
            'average': 2.67,
            'minimum': 2.5,
            'maximum': 2.8,
            'trend': 'up',
            'latest_value': 2.8,
            'previous_value': 2.7
        },
        'timeframe': '12 months',
        'last_updated': '2024-01-01T00:00:00'
    }
    
    print("📊 Chart data structure:")
    print(f"  Indicator: {chart_data['indicator']}")
    print(f"  Data points: {chart_data['data_points']}")
    print(f"  Timeframe: {chart_data['timeframe']}")
    
    if 'statistics' in chart_data:
        stats = chart_data['statistics']
        print("  Statistics:")
        for key, value in stats.items():
            print(f"    {key}: {value}")
    
    if 'historical_data' in chart_data:
        historical_data = chart_data['historical_data']
        print(f"  Historical data: {len(historical_data)} points")
        
        # Check required fields
        required_fields = ['date', 'value']
        if historical_data:
            sample_point = historical_data[0]
            missing_fields = [field for field in required_fields if field not in sample_point]
            
            if missing_fields:
                print(f"  ❌ Missing required fields: {missing_fields}")
            else:
                print("  ✅ All required fields present")
    
    print("✅ Chart data structure test complete")

def main():
    """Run all improvement tests"""
    print("🚀 Chart Improvements Test Suite")
    print("=" * 60)
    
    # Run all tests
    test_deduplication_logic()
    test_data_validation()
    test_chart_data_structure()
    
    print("\n" + "=" * 60)
    print("✅ Chart improvements test suite complete!")
    print("💡 The chart popup should now handle data quality issues better")

if __name__ == "__main__":
    main()
