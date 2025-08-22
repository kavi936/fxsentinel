#!/usr/bin/env python3
"""
Fix .env file with correct developer email
This script will update the root .env file with your actual developer email
"""

import os
import re

def fix_env_file():
    """Fix the .env file with correct developer email"""
    env_file = '.env'
    
    if not os.path.exists(env_file):
        print(f"❌ {env_file} file not found")
        return False
    
    # Read the current .env file
    with open(env_file, 'r') as f:
        content = f.read()
    
    # Check if it already has the correct email
    if 'kavi.cf412@gmail.com' in content:
        print("✅ .env file already has correct developer email")
        return True
    
    # Replace the placeholder emails with your actual email
    old_pattern = r'DEVELOPER_EMAILS=your_email@example\.com,developer@example\.com'
    new_content = 'DEVELOPER_EMAILS=kavi.cf412@gmail.com'
    
    if re.search(old_pattern, content):
        content = re.sub(old_pattern, new_content, content)
        
        # Write the updated content back
        with open(env_file, 'w') as f:
            f.write(content)
        
        print("✅ Updated .env file with correct developer email")
        print("   Changed: DEVELOPER_EMAILS=your_email@example.com,developer@example.com")
        print("   To:      DEVELOPER_EMAILS=kavi.cf412@gmail.com")
        return True
    else:
        print("⚠️  Could not find the DEVELOPER_EMAILS line to update")
        print("   Please manually update your .env file:")
        print("   DEVELOPER_EMAILS=kavi.cf412@gmail.com")
        return False

if __name__ == "__main__":
    print("🔧 Fixing .env file...")
    success = fix_env_file()
    if success:
        print("\n✅ .env file updated successfully!")
        print("   You can now run: python3 test_developer_access.py")
    else:
        print("\n❌ Failed to update .env file")
        print("   Please update it manually")
