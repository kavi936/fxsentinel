#!/usr/bin/env python3
"""
Run Economic Data Extraction Script
This script extracts all available economic calendar data from Finnhub API
and stores it in a local SQLite database for continued use after API expiration.
"""

import sys
import os
from datetime import datetime

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.economic_data_extractor import EconomicDataExtractor

def main():
    """Main function to run the data extraction"""
    print("🚀 FXSentinel Economic Data Extraction")
    print("=" * 50)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Check if API key is available
        api_key = os.getenv('FINNHUB_API_KEY')
        if not api_key:
            print("❌ ERROR: FINNHUB_API_KEY environment variable not set!")
            print("Please set your Finnhub API key in the .env file before running this script.")
            return 1
        
        print("✅ Finnhub API key found")
        print()
        
        # Initialize extractor
        print("🔧 Initializing data extractor...")
        extractor = EconomicDataExtractor()
        
        # Show current database stats
        print("📊 Current database statistics:")
        stats = extractor.get_database_stats()
        if 'error' not in stats:
            print(f"   Total events: {stats['total_events']}")
            if stats['date_range']['earliest']:
                print(f"   Date range: {stats['date_range']['earliest']} to {stats['date_range']['latest']}")
            else:
                print("   Date range: No data yet")
        print()
        
        # Ask user for extraction parameters
        print("📋 Extraction Options:")
        print("1. Quick extraction (3 months historical + 3 months future)")
        print("2. Standard extraction (12 months historical + 6 months future)")
        print("3. Comprehensive extraction (24 months historical + 12 months future)")
        print("4. Custom extraction")
        print()
        
        choice = input("Select extraction option (1-4): ").strip()
        
        if choice == "1":
            print("🚀 Starting quick extraction...")
            results = extractor.extract_comprehensive_data(historical_months=3, future_months=3)
        elif choice == "2":
            print("🚀 Starting standard extraction...")
            results = extractor.extract_comprehensive_data(historical_months=12, future_months=6)
        elif choice == "3":
            print("🚀 Starting comprehensive extraction...")
            results = extractor.extract_comprehensive_data(historical_months=24, future_months=12)
        elif choice == "4":
            try:
                hist_months = int(input("Historical months to extract: "))
                future_months = int(input("Future months to extract: "))
                print(f"🚀 Starting custom extraction ({hist_months} historical + {future_months} future)...")
                results = extractor.extract_comprehensive_data(historical_months=hist_months, future_months=future_months)
            except ValueError:
                print("❌ Invalid input. Using standard extraction instead.")
                results = extractor.extract_comprehensive_data(historical_months=12, future_months=6)
        else:
            print("❌ Invalid choice. Using standard extraction instead.")
            results = extractor.extract_comprehensive_data(historical_months=12, future_months=6)
        
        print()
        print("📈 Extraction Results:")
        print("-" * 30)
        
        if 'summary' in results:
            print(f"✅ Total events found: {results['summary']['total_events_found']}")
            print(f"💾 Total events stored: {results['summary']['total_events_stored']}")
            print(f"🗄️ Database location: {results['summary']['database_path']}")
            
            if results['historical']:
                print(f"📚 Historical events: {results['historical']['events_stored']} stored")
            if results['future']:
                print(f"🔮 Future events: {results['future']['events_stored']} stored")
        else:
            print("❌ Extraction failed or incomplete")
            if 'error' in results:
                print(f"Error: {results['error']}")
        
        print()
        print("📊 Updated database statistics:")
        final_stats = extractor.get_database_stats()
        if 'error' not in final_stats:
            print(f"   Total events: {final_stats['total_events']}")
            print(f"   Date range: {final_stats['date_range']['earliest']} to {final_stats['date_range']['latest']}")
            
            if final_stats['currency_distribution']:
                top_currencies = list(final_stats['currency_distribution'].keys())[:5]
                print(f"   Top currencies: {', '.join(top_currencies)}")
            
            if final_stats['impact_distribution']:
                print(f"   Impact distribution: {final_stats['impact_distribution']}")
        
        print()
        print("✅ Data extraction completed successfully!")
        print()
        print("💡 Next steps:")
        print("   1. Your economic calendar data is now cached locally")
        print("   2. The system will automatically use cached data when API is unavailable")
        print("   3. You can continue development without the $300/month API cost")
        print("   4. Consider finding a cheaper alternative provider for future updates")
        print()
        print("🔧 To update the cache in the future:")
        print("   python3 backend/run_data_extraction.py")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️ Extraction interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Extraction failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
