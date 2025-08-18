#!/usr/bin/env python3
"""
Clear Analyzed News History Script
Provides options to clear analysis history, news cache, and news history
"""

import sys
import os
import json
from datetime import datetime
from typing import Dict, List, Any

# Add backend to path
sys.path.append('backend')

def clear_analyzed_news_history(clear_type: str = "all", confirm: bool = False) -> Dict[str, Any]:
    """
    Clear analyzed news history and related data
    
    Args:
        clear_type (str): Type of data to clear
            - "analysis": Only clear analysis history
            - "news_cache": Only clear current news cache
            - "news_history": Only clear news history
            - "all": Clear all data (default)
        confirm (bool): If False, will ask for confirmation
    
    Returns:
        Dict with results of the operation
    """
    
    try:
        # Import the services
        from services.analysis_history import analysis_history
        from services.news_cache import news_cache
        
        results = {
            "success": True,
            "cleared_items": [],
            "errors": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # Show what will be cleared
        print(f"\n🗑️  Clear Analyzed News History")
        print("=" * 50)
        
        if clear_type == "analysis":
            print("📊 Will clear: Analysis History")
        elif clear_type == "news_cache":
            print("📰 Will clear: Current News Cache")
        elif clear_type == "news_history":
            print("📚 Will clear: News History")
        elif clear_type == "all":
            print("🧹 Will clear: ALL DATA (Analysis History + News Cache + News History)")
        else:
            results["success"] = False
            results["errors"].append(f"Invalid clear_type: {clear_type}")
            return results
        
        # Get current stats before clearing
        print("\n📈 Current Statistics:")
        print("-" * 30)
        
        # Analysis history stats
        try:
            analysis_stats = analysis_history.get_analysis_stats()
            print(f"📊 Analysis History: {analysis_stats['total_analyses']} analyses")
            print(f"💰 Total Cost: ${analysis_stats['total_cost']}")
            print(f"📊 Average Confidence: {analysis_stats['average_confidence']}%")
        except Exception as e:
            print(f"❌ Error getting analysis stats: {e}")
        
        # News cache stats
        try:
            cache_status = news_cache.get_cache_status()
            if cache_status['exists']:
                print(f"📰 News Cache: {cache_status['news_count']} items (age: {cache_status['age']})")
            else:
                print("📰 News Cache: No cache file")
        except Exception as e:
            print(f"❌ Error getting cache stats: {e}")
        
        # News history stats
        try:
            history_status = news_cache.get_history_status()
            print(f"📚 News History: {history_status['total_items']} items")
        except Exception as e:
            print(f"❌ Error getting history stats: {e}")
        
        # Ask for confirmation if not already confirmed
        if not confirm:
            print(f"\n⚠️  WARNING: This action cannot be undone!")
            response = input(f"\n❓ Are you sure you want to clear the {clear_type} data? (yes/no): ").lower().strip()
            if response not in ['yes', 'y']:
                print("❌ Operation cancelled by user")
                results["success"] = False
                results["errors"].append("Operation cancelled by user")
                return results
        
        print(f"\n🔄 Clearing {clear_type} data...")
        
        # Clear analysis history
        if clear_type in ["analysis", "all"]:
            try:
                if analysis_history.clear_history():
                    results["cleared_items"].append("analysis_history")
                    print("✅ Analysis history cleared successfully")
                else:
                    results["errors"].append("Failed to clear analysis history")
                    print("❌ Failed to clear analysis history")
            except Exception as e:
                results["errors"].append(f"Error clearing analysis history: {e}")
                print(f"❌ Error clearing analysis history: {e}")
        
        # Clear news cache
        if clear_type in ["news_cache", "all"]:
            try:
                if news_cache.clear_cache():
                    results["cleared_items"].append("news_cache")
                    print("✅ News cache cleared successfully")
                else:
                    results["errors"].append("Failed to clear news cache")
                    print("❌ Failed to clear news cache")
            except Exception as e:
                results["errors"].append(f"Error clearing news cache: {e}")
                print(f"❌ Error clearing news cache: {e}")
        
        # Clear news history
        if clear_type in ["news_history", "all"]:
            try:
                if news_cache.clear_history():
                    results["cleared_items"].append("news_history")
                    print("✅ News history cleared successfully")
                else:
                    results["errors"].append("Failed to clear news history")
                    print("❌ Failed to clear news history")
            except Exception as e:
                results["errors"].append(f"Error clearing news history: {e}")
                print(f"❌ Error clearing news history: {e}")
        
        # Show final results
        print(f"\n📋 Operation Summary:")
        print("-" * 30)
        if results["cleared_items"]:
            print(f"✅ Successfully cleared: {', '.join(results['cleared_items'])}")
        if results["errors"]:
            print(f"❌ Errors: {len(results['errors'])}")
            for error in results["errors"]:
                print(f"   - {error}")
        
        print(f"\n🎉 Clear operation completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return results
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you're running this script from the project root directory")
        return {
            "success": False,
            "errors": [f"Import error: {e}"],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return {
            "success": False,
            "errors": [f"Unexpected error: {e}"],
            "timestamp": datetime.now().isoformat()
        }

def show_current_stats() -> None:
    """Show current statistics without clearing anything"""
    try:
        from services.analysis_history import analysis_history
        from services.news_cache import news_cache
        
        print(f"\n📊 Current News Analysis Statistics")
        print("=" * 50)
        
        # Analysis history stats
        try:
            analysis_stats = analysis_history.get_analysis_stats()
            print(f"\n📊 Analysis History:")
            print(f"   Total Analyses: {analysis_stats['total_analyses']}")
            print(f"   Total Cost: ${analysis_stats['total_cost']}")
            print(f"   Average Confidence: {analysis_stats['average_confidence']}%")
            
            if analysis_stats['analysis_types']:
                print(f"   Analysis Types:")
                for analysis_type, count in analysis_stats['analysis_types'].items():
                    print(f"     - {analysis_type}: {count}")
        except Exception as e:
            print(f"❌ Error getting analysis stats: {e}")
        
        # News cache stats
        try:
            cache_status = news_cache.get_cache_status()
            print(f"\n📰 News Cache:")
            if cache_status['exists']:
                print(f"   Status: Active")
                print(f"   Items: {cache_status['news_count']}")
                print(f"   Age: {cache_status['age']}")
                print(f"   Valid: {'Yes' if cache_status['is_valid'] else 'No'}")
                print(f"   Last Updated: {cache_status['last_updated']}")
            else:
                print(f"   Status: No cache file")
        except Exception as e:
            print(f"❌ Error getting cache stats: {e}")
        
        # News history stats
        try:
            history_status = news_cache.get_history_status()
            print(f"\n📚 News History:")
            print(f"   Total Items: {history_status['total_items']}")
            if history_status['oldest_item']:
                print(f"   Oldest Item: {history_status['oldest_item']}")
            if history_status['newest_item']:
                print(f"   Newest Item: {history_status['newest_item']}")
        except Exception as e:
            print(f"❌ Error getting history stats: {e}")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you're running this script from the project root directory")

def main():
    """Main function to handle command line arguments"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Clear analyzed news history")
    parser.add_argument(
        "--type", 
        choices=["analysis", "news_cache", "news_history", "all"],
        default="all",
        help="Type of data to clear (default: all)"
    )
    parser.add_argument(
        "--confirm", 
        action="store_true",
        help="Skip confirmation prompt"
    )
    parser.add_argument(
        "--stats", 
        action="store_true",
        help="Show current statistics without clearing"
    )
    
    args = parser.parse_args()
    
    if args.stats:
        show_current_stats()
    else:
        clear_analyzed_news_history(args.type, args.confirm)

if __name__ == "__main__":
    main()
