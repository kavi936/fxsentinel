#!/usr/bin/env python3
"""
Script to remove FXStreet gold price spam from news cache and history
This script calls the API endpoint to remove items matching the filter phrase
"""

import requests
import json
import sys
import os

# Add parent directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def clear_fxstreet_gold_spam(api_base_url=None, confirm=False):
    """
    Remove FXStreet gold price spam from cache and history
    
    Args:
        api_base_url: Base URL of the API (defaults to localhost:5000)
        confirm: If True, actually perform the removal (default: False)
    """
    if api_base_url is None:
        api_base_url = "http://localhost:5000"
    
    endpoint = f"{api_base_url}/api/remove-filtered-news"
    
    # Filter phrase to match
    filter_phrase = "Gold rises, according to FXStreet data"
    
    payload = {
        "filter_phrase": filter_phrase,
        "confirm": confirm
    }
    
    print(f"🔍 Checking for news items matching: '{filter_phrase}'")
    print(f"📡 API endpoint: {endpoint}")
    print(f"⚠️  Confirm: {confirm}")
    print()
    
    if not confirm:
        print("⚠️  This is a dry run. Set confirm=True to actually remove items.")
        print()
    
    try:
        response = requests.post(endpoint, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success!")
            print(f"   Removed from cache: {result.get('removed_from_cache', 0)} items")
            print(f"   Removed from history: {result.get('removed_from_history', 0)} items")
            print(f"   Total removed: {result.get('total_removed', 0)} items")
            return result
        elif response.status_code == 400:
            result = response.json()
            print("ℹ️  Confirmation required:")
            print(f"   {result.get('message', 'Unknown message')}")
            print()
            print("To actually remove items, run:")
            print("   python3 scripts/clear_fxstreet_gold_spam.py --confirm")
            return result
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"   {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to API")
        print(f"   Make sure the server is running at {api_base_url}")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Remove FXStreet gold price spam from news cache")
    parser.add_argument("--api-url", default="http://localhost:5000", help="API base URL")
    parser.add_argument("--confirm", action="store_true", help="Actually perform the removal (required)")
    
    args = parser.parse_args()
    
    if not args.confirm:
        print("⚠️  WARNING: This script will remove news items from cache and history.")
        print("   Use --confirm flag to actually perform the removal.")
        print()
    
    result = clear_fxstreet_gold_spam(api_base_url=args.api_url, confirm=args.confirm)
    
    if result and result.get('success'):
        sys.exit(0)
    else:
        sys.exit(1)

