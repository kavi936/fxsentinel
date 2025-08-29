#!/usr/bin/env python3
"""
FXSentinel Beta Tester Management Script

This script helps you manage beta tester emails for your FXSentinel application.
It provides an easy way to add, remove, and list beta testers.
"""

import os
import sys
from typing import List, Set

class BetaTesterManager:
    def __init__(self, env_file_path: str = '.env'):
        self.env_file_path = env_file_path
        self.beta_tester_key = 'BETA_TESTER_EMAILS'
        
    def read_current_emails(self) -> Set[str]:
        """Read current beta tester emails from environment file"""
        emails = set()
        
        if not os.path.exists(self.env_file_path):
            print(f"⚠️ Environment file {self.env_file_path} not found")
            return emails
            
        try:
            with open(self.env_file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith(f'{self.beta_tester_key}='):
                        email_list = line.split('=', 1)[1].strip()
                        if email_list:
                            emails = set(email.strip() for email in email_list.split(',') if email.strip())
                        break
        except Exception as e:
            print(f"❌ Error reading environment file: {e}")
            
        return emails
    
    def write_emails(self, emails: Set[str]):
        """Write beta tester emails to environment file"""
        try:
            # Read all lines from the file
            lines = []
            if os.path.exists(self.env_file_path):
                with open(self.env_file_path, 'r') as f:
                    lines = f.readlines()
            
            # Find and update the BETA_TESTER_EMAILS line
            updated = False
            for i, line in enumerate(lines):
                if line.strip().startswith(f'{self.beta_tester_key}='):
                    lines[i] = f'{self.beta_tester_key}={",".join(sorted(emails))}\n'
                    updated = True
                    break
            
            # If not found, add it
            if not updated:
                lines.append(f'{self.beta_tester_key}={",".join(sorted(emails))}\n')
            
            # Write back to file
            with open(self.env_file_path, 'w') as f:
                f.writelines(lines)
                
            print(f"✅ Updated {self.env_file_path} with {len(emails)} beta tester emails")
            
        except Exception as e:
            print(f"❌ Error writing to environment file: {e}")
    
    def add_email(self, email: str):
        """Add a single email to beta testers"""
        emails = self.read_current_emails()
        email = email.lower().strip()
        
        if email in emails:
            print(f"ℹ️ Email {email} is already a beta tester")
            return
            
        emails.add(email)
        self.write_emails(emails)
        print(f"✅ Added {email} as beta tester")
    
    def remove_email(self, email: str):
        """Remove a single email from beta testers"""
        emails = self.read_current_emails()
        email = email.lower().strip()
        
        if email not in emails:
            print(f"ℹ️ Email {email} is not currently a beta tester")
            return
            
        emails.remove(email)
        self.write_emails(emails)
        print(f"✅ Removed {email} from beta testers")
    
    def add_multiple_emails(self, email_list: List[str]):
        """Add multiple emails to beta testers"""
        emails = self.read_current_emails()
        added_count = 0
        
        for email in email_list:
            email = email.lower().strip()
            if email and email not in emails:
                emails.add(email)
                added_count += 1
                print(f"✅ Added {email}")
            elif email in emails:
                print(f"ℹ️ {email} already exists")
        
        self.write_emails(emails)
        print(f"🎯 Added {added_count} new beta testers")
    
    def list_emails(self):
        """List all current beta tester emails"""
        emails = self.read_current_emails()
        
        if not emails:
            print("📝 No beta tester emails found")
            return
            
        print(f"📝 Current beta testers ({len(emails)}):")
        for i, email in enumerate(sorted(emails), 1):
            print(f"  {i}. {email}")
    
    def clear_all(self):
        """Remove all beta tester emails"""
        self.write_emails(set())
        print("🗑️ Cleared all beta tester emails")
    
    def validate_email(self, email: str) -> bool:
        """Basic email validation"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

def print_usage():
    """Print usage instructions"""
    print("""
🎯 FXSentinel Beta Tester Management

Usage:
  python3 manage_beta_testers.py [command] [options]

Commands:
  list                    - List all current beta testers
  add <email>            - Add a single email
  add-multiple <emails>  - Add multiple emails (comma-separated)
  remove <email>         - Remove a single email
  clear                  - Remove all beta testers
  help                   - Show this help

Examples:
  python3 manage_beta_testers.py list
  python3 manage_beta_testers.py add friend@example.com
  python3 manage_beta_testers.py add-multiple "friend1@example.com,friend2@example.com"
  python3 manage_beta_testers.py remove oldfriend@example.com
  python3 manage_beta_testers.py clear

Notes:
  - Emails are automatically converted to lowercase
  - Duplicate emails are ignored
  - Changes are saved to .env file
  - Remember to redeploy after making changes
""")

def main():
    if len(sys.argv) < 2:
        print_usage()
        return
    
    manager = BetaTesterManager()
    command = sys.argv[1].lower()
    
    try:
        if command == 'list':
            manager.list_emails()
            
        elif command == 'add':
            if len(sys.argv) < 3:
                print("❌ Please provide an email address")
                return
            email = sys.argv[2]
            if manager.validate_email(email):
                manager.add_email(email)
            else:
                print(f"❌ Invalid email format: {email}")
                
        elif command == 'add-multiple':
            if len(sys.argv) < 3:
                print("❌ Please provide email addresses (comma-separated)")
                return
            email_list = [email.strip() for email in sys.argv[2].split(',')]
            valid_emails = []
            invalid_emails = []
            
            for email in email_list:
                if manager.validate_email(email):
                    valid_emails.append(email)
                else:
                    invalid_emails.append(email)
            
            if invalid_emails:
                print(f"⚠️ Invalid emails: {', '.join(invalid_emails)}")
            
            if valid_emails:
                manager.add_multiple_emails(valid_emails)
                
        elif command == 'remove':
            if len(sys.argv) < 3:
                print("❌ Please provide an email address")
                return
            email = sys.argv[2]
            manager.remove_email(email)
            
        elif command == 'clear':
            confirm = input("⚠️ Are you sure you want to remove ALL beta testers? (yes/no): ")
            if confirm.lower() == 'yes':
                manager.clear_all()
            else:
                print("❌ Operation cancelled")
                
        elif command == 'help':
            print_usage()
            
        else:
            print(f"❌ Unknown command: {command}")
            print_usage()
            
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
