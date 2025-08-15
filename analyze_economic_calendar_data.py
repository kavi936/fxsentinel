#!/usr/bin/env python3
"""
Analyze all economic calendar data to understand what patterns we need to handle
"""

import requests
import json
from collections import Counter
import re

def analyze_economic_calendar_data():
    """Analyze all economic calendar data to find patterns"""
    
    print("🔍 Analyzing Economic Calendar Data Patterns")
    print("=" * 60)
    
    try:
        # Get data from our API
        response = requests.get("http://localhost:5001/api/economic-calendar")
        data = response.json()
        events = data.get('events', [])
        
        print(f"✅ Found {len(events)} events to analyze")
        
        if not events:
            print("❌ No events found")
            return
        
        # Collect all event titles
        all_titles = []
        all_currencies = []
        all_impacts = []
        
        for event in events:
            title = event.get('title', '')
            currency = event.get('currency', '')
            impact = event.get('impact', '')
            
            all_titles.append(title)
            all_currencies.append(currency)
            all_impacts.append(impact)
        
        # Analyze titles
        print("\n📊 Event Title Analysis:")
        print("-" * 40)
        
        title_counter = Counter(all_titles)
        print(f"Total unique titles: {len(title_counter)}")
        
        print("\nTop 20 most common event titles:")
        for title, count in title_counter.most_common(20):
            print(f"  {count:2d}x: {title}")
        
        # Analyze patterns in titles
        print("\n🔍 Title Pattern Analysis:")
        print("-" * 40)
        
        # Look for common patterns
        patterns = {
            'MOM': [],
            'YoY': [],
            'YOY': [],
            'Month over Month': [],
            'Year over Year': [],
            'Change': [],
            'Rate': [],
            'Index': [],
            'Data': [],
            'Release': [],
            'Report': [],
            'Decision': [],
            'Statement': [],
            'Minutes': [],
            'Survey': [],
            'PMI': [],
            'ISM': [],
            'GDP': [],
            'CPI': [],
            'PPI': [],
            'NFP': [],
            'Employment': [],
            'Unemployment': [],
            'Retail': [],
            'Sales': [],
            'Trade': [],
            'Balance': [],
            'Deficit': [],
            'Surplus': [],
            'Housing': [],
            'Building': [],
            'Construction': [],
            'Industrial': [],
            'Manufacturing': [],
            'Production': [],
            'Consumer': [],
            'Confidence': [],
            'Sentiment': [],
            'Spending': [],
            'Consumption': [],
            'Inflation': [],
            'Interest': [],
            'FOMC': [],
            'ECB': [],
            'BOE': [],
            'BOJ': [],
            'RBA': [],
            'BOC': []
        }
        
        for title in all_titles:
            title_lower = title.lower()
            title_upper = title.upper()
            
            for pattern, matches in patterns.items():
                if pattern.lower() in title_lower or pattern in title_upper:
                    matches.append(title)
        
        # Show patterns with matches
        print("Patterns found in titles:")
        for pattern, matches in patterns.items():
            if matches:
                unique_matches = list(set(matches))
                print(f"  {pattern}: {len(unique_matches)} unique titles")
                if len(unique_matches) <= 5:  # Show all if 5 or fewer
                    for match in unique_matches:
                        print(f"    - {match}")
                else:  # Show first 3
                    for match in unique_matches[:3]:
                        print(f"    - {match}")
                    print(f"    ... and {len(unique_matches) - 3} more")
        
        # Analyze currencies
        print("\n💰 Currency Analysis:")
        print("-" * 40)
        currency_counter = Counter(all_currencies)
        for currency, count in currency_counter.most_common():
            print(f"  {currency}: {count} events")
        
        # Analyze impacts
        print("\n⚡ Impact Analysis:")
        print("-" * 40)
        impact_counter = Counter(all_impacts)
        for impact, count in impact_counter.most_common():
            print(f"  {impact}: {count} events")
        
        # Find titles that might not be covered by our current patterns
        print("\n❓ Potentially Uncovered Titles:")
        print("-" * 40)
        
        # Get all unique titles
        unique_titles = list(set(all_titles))
        
        # Check which ones might not be covered
        potentially_uncovered = []
        
        for title in unique_titles:
            title_lower = title.lower()
            
            # Check if our current patterns would catch this
            covered = False
            
            # Our current patterns
            current_patterns = [
                'ppi', 'cpi', 'non-farm', 'nfp', 'employment', 'gdp', 'retail sales',
                'manufacturing', 'ism', 'pmi', 'interest rate', 'fomc', 'unemployment',
                'housing', 'home sales', 'construction', 'building permits', 'trade balance',
                'current account', 'exports', 'imports', 'trade deficit', 'trade surplus',
                'consumer confidence', 'sentiment', 'consumer spending', 'personal consumption',
                'industrial production', 'capacity utilization', 'industrial output',
                'manufacturing output', 'unemployment claims', 'jobless'
            ]
            
            for pattern in current_patterns:
                if pattern in title_lower:
                    covered = True
                    break
            
            if not covered:
                potentially_uncovered.append(title)
        
        if potentially_uncovered:
            print(f"Found {len(potentially_uncovered)} potentially uncovered titles:")
            for title in potentially_uncovered[:20]:  # Show first 20
                print(f"  - {title}")
            if len(potentially_uncovered) > 20:
                print(f"  ... and {len(potentially_uncovered) - 20} more")
        else:
            print("All titles appear to be covered by current patterns!")
        
        # Generate recommendations
        print("\n💡 Recommendations:")
        print("-" * 40)
        
        if potentially_uncovered:
            print("1. Add patterns for uncovered titles")
            print("2. Consider using GPT to identify economic indicator types")
            print("3. Expand pattern matching to handle more variations")
        else:
            print("1. Current patterns appear to cover all titles")
            print("2. Consider adding more specific patterns for better accuracy")
        
        print("3. Consider implementing GPT-based indicator identification as backup")
        
    except Exception as e:
        print(f"❌ Error analyzing data: {e}")

if __name__ == "__main__":
    analyze_economic_calendar_data()
