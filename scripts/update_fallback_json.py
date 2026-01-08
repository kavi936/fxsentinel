#!/usr/bin/env python3
"""
Script to update the fallback JSON file with latest data from Google Sheets
This ensures the fallback data is always up-to-date when API fails
"""
import os
import sys
import json
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

from services.google_sheets_service import GoogleSheetsService
from dotenv import load_dotenv

# Load environment variables
load_dotenv(backend_path / '.env')

def update_fallback_json():
    """Fetch latest data from Google Sheets and update fallback JSON"""
    print("🔄 Updating fallback JSON from Google Sheets...")
    
    # Initialize Google Sheets service
    try:
        service = GoogleSheetsService()
        if not service.is_available():
            print("❌ Google Sheets service not available")
            return False
        print("✅ Google Sheets service initialized")
    except Exception as e:
        print(f"❌ Failed to initialize Google Sheets service: {e}")
        return False
    
    # Countries to fetch
    countries = ['US', 'EUR', 'GBP', 'JPY']
    
    # Fetch data for each country
    all_data = {}
    
    for country_code in countries:
        print(f"\n📊 Fetching data for {country_code}...")
        try:
            # Force fresh fetch (bypass cache)
            indicators = service.get_economy_indicators(country_code)
            
            if indicators:
                all_data[country_code] = {
                    "indicators": indicators
                }
                indicator_count = len(indicators)
                print(f"✅ Fetched {indicator_count} indicators for {country_code}")
            else:
                print(f"⚠️ No indicators found for {country_code}")
        except Exception as e:
            print(f"❌ Error fetching {country_code}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    if not all_data:
        print("\n❌ No data fetched from Google Sheets")
        return False
    
    # Write to JSON file
    json_path = Path(__file__).parent.parent / 'src' / 'data' / 'economyIndicators.json'
    
    try:
        # Preserve centralBankRates from existing JSON
        existing_central_bank_rates = {}
        if json_path.exists():
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    for country_code in countries:
                        if country_code in existing_data:
                            cbr = existing_data[country_code].get('centralBankRates')
                            if cbr:
                                existing_central_bank_rates[country_code] = cbr
                                print(f"📌 Preserving central bank rates for {country_code}")
            except Exception as e:
                print(f"⚠️ Could not read existing JSON to preserve central bank rates: {e}")
        
        # Merge central bank rates with new data
        for country_code in countries:
            if country_code in all_data and country_code in existing_central_bank_rates:
                all_data[country_code]['centralBankRates'] = existing_central_bank_rates[country_code]
        
        # Write merged data
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Successfully updated fallback JSON: {json_path}")
        print(f"📊 Updated {len(all_data)} countries:")
        for country, data in all_data.items():
            indicator_count = len(data.get('indicators', {}))
            has_cbr = 'centralBankRates' in data
            cbr_status = " (with central bank rates)" if has_cbr else ""
            print(f"   - {country}: {indicator_count} indicators{cbr_status}")
        
        return True
    except Exception as e:
        print(f"\n❌ Failed to write JSON file: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = update_fallback_json()
    sys.exit(0 if success else 1)

