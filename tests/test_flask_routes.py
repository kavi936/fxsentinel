#!/usr/bin/env python3
"""
Test script to check Flask app routes
"""
import sys
import os
sys.path.append('backend')

try:
    from app import app
    print("🔍 Flask App Routes:")
    print("=" * 40)
    
    for rule in app.url_map.iter_rules():
        print(f"   {rule.rule} [{', '.join(rule.methods)}]")
        
    print(f"\n📊 Total routes: {len(list(app.url_map.iter_rules()))}")
    
except Exception as e:
    print(f"❌ Error: {e}")
