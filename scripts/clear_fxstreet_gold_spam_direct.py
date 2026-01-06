#!/usr/bin/env python3
"""
Direct script to remove FXStreet gold price spam from news cache and history
This script accesses Firebase directly, so it doesn't require the API server to be running
"""

import sys
import os

# Add backend directory to path
backend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend')
sys.path.insert(0, backend_dir)

def clear_fxstreet_gold_spam_direct(confirm=False):
    """
    Remove FXStreet gold price spam from cache and history directly via Firebase
    
    Args:
        confirm: If True, actually perform the removal (default: False)
    """
    filter_phrase = "Gold rises, according to FXStreet data"
    
    print(f"🔍 Checking for news items matching: '{filter_phrase}'")
    print(f"⚠️  Confirm: {confirm}")
    print()
    
    if not confirm:
        print("⚠️  This is a dry run. Set confirm=True to actually remove items.")
        print()
    
    try:
        # Import the persistent news cache service
        from services.persistent_news_cache import get_persistent_news_cache
        news_cache = get_persistent_news_cache()
        
        # First, let's check what would be removed (dry run)
        print("📊 Analyzing cache and history...")
        
        # Load cache to see what would be removed
        cached_news = news_cache.load_news(allow_stale=True) or []
        matching_cache = [item for item in cached_news if filter_phrase in item.get('title', '')]
        
        # Load history to see what would be removed
        history = news_cache.load_history()
        matching_history = [item for item in history if filter_phrase in item.get('title', '')]
        
        print(f"📦 Found {len(matching_cache)} matching items in cache")
        print(f"📚 Found {len(matching_history)} matching items in history")
        print(f"📊 Total items that would be removed: {len(matching_cache) + len(matching_history)}")
        print()
        
        if len(matching_cache) > 0:
            print("📦 Cache items that would be removed:")
            for i, item in enumerate(matching_cache[:10], 1):  # Show first 10
                title = item.get('title', 'No title')
                source = item.get('source', 'Unknown')
                print(f"   {i}. [{source}] {title[:80]}")
            if len(matching_cache) > 10:
                print(f"   ... and {len(matching_cache) - 10} more")
            print()
        
        if len(matching_history) > 0:
            print("📚 History items that would be removed:")
            for i, item in enumerate(matching_history[:10], 1):  # Show first 10
                title = item.get('title', 'No title')
                source = item.get('source', 'Unknown')
                print(f"   {i}. [{source}] {title[:80]}")
            if len(matching_history) > 10:
                print(f"   ... and {len(matching_history) - 10} more")
            print()
        
        if not confirm:
            print("⚠️  DRY RUN - No items were removed.")
            print("   To actually remove items, run:")
            print("   python3 scripts/clear_fxstreet_gold_spam_direct.py --confirm")
            return {
                'success': False,
                'dry_run': True,
                'removed_from_cache': 0,
                'removed_from_history': 0,
                'total_removed': 0,
                'would_remove_from_cache': len(matching_cache),
                'would_remove_from_history': len(matching_history),
                'total_would_remove': len(matching_cache) + len(matching_history)
            }
        
        # Actually remove the items
        print("🗑️  Removing items from cache and history...")
        result = news_cache.remove_filtered_items(filter_phrase)
        
        if result.get('success'):
            print("✅ Success!")
            print(f"   Removed from cache: {result.get('removed_from_cache', 0)} items")
            print(f"   Removed from history: {result.get('removed_from_history', 0)} items")
            print(f"   Total removed: {result.get('total_removed', 0)} items")
            return result
        else:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")
            return result
            
    except ImportError as e:
        print(f"❌ Error importing services: {e}")
        print("   Make sure you're running this from the project root directory")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Remove FXStreet gold price spam from news cache (direct Firebase access)")
    parser.add_argument("--confirm", action="store_true", help="Actually perform the removal (required)")
    
    args = parser.parse_args()
    
    if not args.confirm:
        print("⚠️  WARNING: This script will remove news items from cache and history.")
        print("   Use --confirm flag to actually perform the removal.")
        print()
    
    result = clear_fxstreet_gold_spam_direct(confirm=args.confirm)
    
    if result and (result.get('success') or result.get('dry_run')):
        sys.exit(0)
    else:
        sys.exit(1)

