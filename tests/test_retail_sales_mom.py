#!/usr/bin/env python3
"""
Test script for Retail Sales MOM and other variations
"""

import sys
import os
sys.path.append('backend')

from services.gpt_ai_analysis import GPTAIAnalyzer

def test_variations():
    """Test different variations of economic indicators"""
    
    # Initialize analyzer
    analyzer = GPTAIAnalyzer()
    
    # Test variations that might fail
    variations = [
        "US Retail Sales MOM",
        "Retail Sales MOM",
        "Retail Sales Month over Month",
        "US Retail Sales YoY",
        "Retail Sales Year over Year",
        "US CPI MOM",
        "CPI Month over Month",
        "US PPI YoY",
        "PPI Year over Year",
        "US NFP Change",
        "Non-Farm Payrolls Change",
        "US Unemployment Claims",
        "Jobless Claims",
        "US Housing Permits",
        "Building Permits",
        "US Trade Deficit",
        "Trade Surplus",
        "US Consumer Spending",
        "Personal Consumption",
        "US Industrial Output",
        "Manufacturing Output"
    ]
    
    print("🔍 Testing Economic Indicator Variations")
    print("=" * 60)
    
    for variation in variations:
        context = analyzer._get_economic_indicator_context(variation)
        print(f"📊 {variation}:")
        print(f"   Context Length: {len(context)} characters")
        print(f"   Contains specific info: {'measures' in context or 'indicator' in context or 'data' in context or 'drivers' in context}")
        print(f"   Sample: {context.strip()[:80]}...")
        print()

if __name__ == "__main__":
    test_variations()
