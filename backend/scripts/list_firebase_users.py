#!/usr/bin/env python3
"""
Script to list all Firebase Authentication users with their details.
This uses the Firebase Admin SDK to retrieve user information including:
- Display names
- Email addresses
- User IDs (UIDs)
- Creation dates
- Last sign-in dates
- Provider information (email/password, Google, etc.)
"""

import sys
import os
from datetime import datetime

# Add backend directory to path
backend_dir = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, backend_dir)

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    env_path = os.path.join(backend_dir, '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
except ImportError:
    # dotenv not available, skip loading .env file
    pass

try:
    import firebase_admin
    from firebase_admin import auth, credentials, initialize_app
except ImportError:
    print("❌ Error: firebase-admin is not installed")
    print("   Install it with: pip install firebase-admin")
    sys.exit(1)

def initialize_firebase_admin():
    """Initialize Firebase Admin SDK"""
    try:
        # Check if already initialized
        if not firebase_admin._apps:
            # Get project ID from environment or use default
            project_id = os.getenv('FIREBASE_PROJECT_ID') or os.getenv('GOOGLE_CLOUD_PROJECT') or 'fxsentinel'
            
            # Set GOOGLE_CLOUD_PROJECT environment variable if not set (Firebase Admin may need it)
            if not os.getenv('GOOGLE_CLOUD_PROJECT'):
                os.environ['GOOGLE_CLOUD_PROJECT'] = project_id
            
            # Try to use service account key if available
            service_account_path = os.path.join(
                os.path.dirname(__file__), '..', 'firebase-service-account.json'
            )
            
            if os.path.exists(service_account_path):
                cred = credentials.Certificate(service_account_path)
                initialize_app(cred, {'projectId': project_id})
                print(f"✅ Firebase Admin initialized with service account (project: {project_id})")
                return True
            else:
                # Service account file not found - provide clear instructions
                print("\n" + "="*80)
                print("⚠️  Firebase Service Account Key Not Found")
                print("="*80)
                print(f"\n📁 Expected location: {service_account_path}")
                print("\n📥 To download your Firebase service account key:")
                print("   1. Go to: https://console.firebase.google.com/")
                print(f"   2. Select your project: {project_id}")
                print("   3. Click the gear icon ⚙️ → Project Settings")
                print("   4. Go to the 'Service Accounts' tab")
                print("   5. Click 'Generate New Private Key'")
                print("   6. Save the JSON file as: backend/firebase-service-account.json")
                print("\n💡 Alternatively, you can use Application Default Credentials")
                print("   if you're running on Google Cloud Platform or have gcloud configured.")
                print("="*80 + "\n")
                
                # Try default credentials anyway (might work on GCP/Railway)
                try:
                    initialize_app(options={'projectId': project_id})
                    print(f"✅ Firebase Admin initialized with default credentials (project: {project_id})")
                    return True
                except Exception as default_error:
                    print(f"\n❌ Default credentials also failed: {default_error}")
                    print("\n🔧 You need to download the service account key file.")
                    return False
        else:
            print("✅ Firebase Admin already initialized")
            return True
        
    except Exception as e:
        print(f"\n❌ Error initializing Firebase Admin: {e}")
        print(f"\n💡 To fix this:")
        print(f"   1. Download Firebase service account key (see instructions above)")
        print(f"   2. Place it at: backend/firebase-service-account.json")
        print(f"   3. Or set FIREBASE_PROJECT_ID environment variable")
        return False

def list_all_users(max_results=1000):
    """
    List all Firebase Authentication users with pagination.
    
    Args:
        max_results: Maximum number of users to retrieve (default: 1000)
    
    Returns:
        List of user dictionaries with user information
    """
    users = []
    next_page_token = None
    
    try:
        # Firebase Admin SDK allows fetching up to 1000 users per page
        # We'll paginate through all users
        while True:
            # Get next page of users
            if next_page_token:
                result = auth.list_users(max_results=min(1000, max_results - len(users)), 
                                       page_token=next_page_token)
            else:
                result = auth.list_users(max_results=min(1000, max_results - len(users)))
            
            # Process users in this page
            for user in result.users:
                user_info = {
                    'uid': user.uid,
                    'email': user.email or 'No email',
                    'display_name': user.display_name or 'No display name',
                    'phone_number': user.phone_number or 'No phone',
                    'email_verified': user.email_verified if user.email else False,
                    'disabled': user.disabled,
                    'creation_timestamp': user.user_metadata.creation_timestamp,
                    'last_sign_in_timestamp': user.user_metadata.last_sign_in_timestamp,
                    'providers': [provider.provider_id for provider in user.provider_data],
                    'photo_url': user.photo_url or 'No photo'
                }
                users.append(user_info)
            
            # Check if there are more pages
            if result.has_next_page and len(users) < max_results:
                next_page_token = result.next_page_token
            else:
                break
            
            # Safety check to avoid infinite loops
            if len(users) >= max_results:
                break
        
        return users
    
    except Exception as e:
        print(f"❌ Error listing users: {e}")
        raise

def format_timestamp(timestamp_ms):
    """Convert Firebase timestamp (milliseconds) to readable date"""
    if timestamp_ms:
        return datetime.fromtimestamp(timestamp_ms / 1000).strftime('%Y-%m-%d %H:%M:%S')
    return 'Never'

def print_users_table(users):
    """Print users in a formatted table"""
    if not users:
        print("\n📭 No users found")
        return
    
    print(f"\n{'='*120}")
    print(f"Found {len(users)} user(s)")
    print(f"{'='*120}\n")
    
    # Print header
    print(f"{'UID':<30} {'Email':<35} {'Display Name':<25} {'Created':<20} {'Last Sign In':<20}")
    print("-" * 120)
    
    # Print each user
    for user in users:
        uid = user['uid'][:28] + '..' if len(user['uid']) > 30 else user['uid']
        email = (user['email'][:33] + '..') if len(user['email']) > 35 else user['email']
        display_name = (user['display_name'][:23] + '..') if len(user['display_name']) > 25 else user['display_name']
        created = format_timestamp(user['creation_timestamp'])
        last_sign_in = format_timestamp(user['last_sign_in_timestamp'])
        
        print(f"{uid:<30} {email:<35} {display_name:<25} {created:<20} {last_sign_in:<20}")
    
    print("-" * 120)

def export_to_csv(users, filename='firebase_users.csv'):
    """Export users to CSV file"""
    import csv
    
    if not users:
        print("📭 No users to export")
        return
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['uid', 'email', 'display_name', 'phone_number', 'email_verified', 
                         'disabled', 'creation_timestamp', 'last_sign_in_timestamp', 
                         'providers', 'photo_url']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for user in users:
                # Convert list to string for CSV
                user_copy = user.copy()
                user_copy['providers'] = ', '.join(user_copy['providers'])
                writer.writerow(user_copy)
        
        print(f"\n✅ Users exported to {filename}")
    except Exception as e:
        print(f"❌ Error exporting to CSV: {e}")

def print_detailed_user_info(users):
    """Print detailed information for each user"""
    if not users:
        print("\n📭 No users found")
        return
    
    print(f"\n{'='*120}")
    print(f"DETAILED USER INFORMATION ({len(users)} users)")
    print(f"{'='*120}\n")
    
    for i, user in enumerate(users, 1):
        print(f"User {i}:")
        print(f"  UID: {user['uid']}")
        print(f"  Email: {user['email']}")
        print(f"  Display Name: {user['display_name']}")
        print(f"  Phone: {user['phone_number']}")
        print(f"  Email Verified: {user['email_verified']}")
        print(f"  Disabled: {user['disabled']}")
        print(f"  Created: {format_timestamp(user['creation_timestamp'])}")
        print(f"  Last Sign In: {format_timestamp(user['last_sign_in_timestamp'])}")
        print(f"  Providers: {', '.join(user['providers'])}")
        print(f"  Photo URL: {user['photo_url']}")
        print("-" * 120)

def main():
    """Main function"""
    print("=" * 120)
    print("Firebase Authentication Users List")
    print("=" * 120)
    
    # Initialize Firebase Admin
    if not initialize_firebase_admin():
        sys.exit(1)
    
    # Get all users
    print("\n📋 Fetching users from Firebase Authentication...")
    try:
        users = list_all_users()
        print(f"✅ Successfully retrieved {len(users)} user(s)")
    except Exception as e:
        print(f"❌ Failed to retrieve users: {e}")
        sys.exit(1)
    
    # Print summary
    print_users_table(users)
    
    # Ask if user wants detailed view
    if users:
        print("\n" + "=" * 120)
        response = input("\nWould you like to see detailed information for all users? (y/n): ").strip().lower()
        if response == 'y':
            print_detailed_user_info(users)
        
        # Ask if user wants to export to CSV
        response = input("\nWould you like to export users to CSV? (y/n): ").strip().lower()
        if response == 'y':
            filename = input("Enter filename (default: firebase_users.csv): ").strip()
            if not filename:
                filename = 'firebase_users.csv'
            export_to_csv(users, filename)
    
    print("\n✅ Done!")

if __name__ == '__main__':
    main()
