# Firebase User Management Guide

This guide explains how to retrieve information about users who have signed up to your app using Firebase Authentication.

## Overview

Your app uses **Firebase Authentication** for user signups and logins. When users sign up, Firebase stores their information including:
- **Display Name** (set during email/password signup or from Google account)
- **Email Address**
- **User ID (UID)** - unique identifier
- **Creation Date**
- **Last Sign In Date**
- **Authentication Provider** (email/password, Google, etc.)

## Methods to Retrieve User Information

You have **two ways** to retrieve user information:

### 1. Command-Line Script (Recommended for One-Time Checks)

A Python script that lists all users directly from Firebase Authentication.

### 2. API Endpoint (For Integration)

A REST API endpoint you can call from your frontend or other services.

---

## Method 1: Using the Command-Line Script

### Prerequisites

1. **Firebase Admin SDK** must be installed:
   ```bash
   cd backend
   pip install firebase-admin
   ```

2. **Firebase Service Account Key** (optional but recommended):
   - Download your service account key from Firebase Console
   - Place it at: `backend/firebase-service-account.json`
   - Or use default credentials if running on GCP/Railway

### Running the Script

```bash
cd backend
python scripts/list_firebase_users.py
```

### What the Script Does

1. **Initializes Firebase Admin SDK** - Connects to your Firebase project
2. **Fetches all users** - Retrieves up to 1000 users (with pagination support)
3. **Displays user information** in a formatted table:
   - User ID (UID)
   - Email address
   - Display name
   - Creation date
   - Last sign-in date

4. **Optional features**:
   - Detailed view with all user properties
   - CSV export for further analysis

### Example Output

```
================================================================================
Found 15 user(s)
================================================================================

UID                           Email                              Display Name            Created              Last Sign In        
--------------------------------------------------------------------------------------------------------------------
abc123def456ghi789jkl012      user1@example.com                  John Doe                2026-01-15 10:30:00  2026-02-08 14:20:00
xyz789abc123def456ghi012      user2@example.com                  Jane Smith              2026-01-20 09:15:00  2026-02-07 16:45:00
...
```

### Exporting to CSV

The script can export all user data to a CSV file for analysis in Excel or Google Sheets:

```bash
python scripts/list_firebase_users.py
# When prompted, choose 'y' to export to CSV
```

---

## Method 2: Using the API Endpoint

### Endpoint Details

**URL**: `GET /api/auth/users`

**Rate Limit**: 10 requests per minute

**Query Parameters**:
- `max_results` (optional): Maximum number of users to return (default: 1000, max: 1000)
- `format` (optional): Response format - `'summary'` (default) or `'detailed'`

### Example Requests

#### Basic Request (Summary Format)

```bash
curl http://localhost:5001/api/auth/users
```

#### With Parameters

```bash
# Get first 50 users
curl "http://localhost:5001/api/auth/users?max_results=50"

# Get detailed information
curl "http://localhost:5001/api/auth/users?format=detailed"
```

#### From JavaScript/TypeScript

```javascript
// Fetch users from your frontend
async function getUsers() {
  try {
    const response = await fetch('http://localhost:5001/api/auth/users?max_results=100');
    const data = await response.json();
    
    console.log(`Found ${data.total} users`);
    
    data.users.forEach(user => {
      console.log(`${user.display_name} (${user.email}) - Created: ${user.created_at}`);
    });
    
    return data.users;
  } catch (error) {
    console.error('Error fetching users:', error);
  }
}
```

### Response Format

#### Summary Format (default)

```json
{
  "users": [
    {
      "uid": "abc123def456ghi789jkl012",
      "email": "user@example.com",
      "display_name": "John Doe",
      "phone_number": null,
      "email_verified": true,
      "disabled": false,
      "created_at": "2026-01-15T10:30:00",
      "last_sign_in": "2026-02-08T14:20:00",
      "providers": ["password"],
      "photo_url": null
    }
  ],
  "total": 15,
  "has_more": false,
  "timestamp": "2026-02-08T15:30:00"
}
```

#### Detailed Format

Includes additional information:
- `custom_claims`: Custom user claims (if any)
- `provider_data`: Detailed provider information

---

## Understanding User Data

### Display Name

The `display_name` field contains:
- **For email/password signups**: The name set during registration (`firstName lastName`)
- **For Google signups**: The name from the user's Google account
- **If not set**: `null` or `"No display name"`

### Providers

The `providers` array shows how users authenticated:
- `["password"]` - Email/password signup
- `["google.com"]` - Google sign-in
- `["password", "google.com"]` - User linked multiple providers

### Important Notes

1. **Display names are optional** - Some users may not have set a display name
2. **Email addresses are primary identifiers** - Always available for email/password users
3. **UIDs are unique** - Use UIDs for database references, not emails
4. **Pagination** - If you have more than 1000 users, you'll need to implement pagination

---

## Common Use Cases

### 1. Find All Users Who Signed Up This Week

```python
# Using the script
python scripts/list_firebase_users.py
# Then filter the CSV export by creation date

# Or using the API
import requests
from datetime import datetime, timedelta

response = requests.get('http://localhost:5001/api/auth/users?format=detailed')
users = response.json()['users']

week_ago = datetime.now() - timedelta(days=7)
recent_users = [
    user for user in users 
    if user['created_at'] and datetime.fromisoformat(user['created_at']) > week_ago
]
```

### 2. Get User Count

```javascript
const response = await fetch('/api/auth/users');
const data = await response.json();
console.log(`Total users: ${data.total}`);
```

### 3. Find Users by Email Domain

```python
# After fetching users
gmail_users = [u for u in users if u['email'] and '@gmail.com' in u['email']]
```

### 4. Export User List for Marketing

```bash
# Run script and export to CSV
python scripts/list_firebase_users.py
# Choose 'y' when prompted for CSV export
# Open firebase_users.csv in Excel/Sheets
```

---

## Troubleshooting

### Error: "Firebase Admin SDK not initialized"

**Solution**: Ensure Firebase Admin is properly initialized in your backend:
1. Check that `firebase-admin` is installed: `pip install firebase-admin`
2. Verify service account key exists at `backend/firebase-service-account.json`
3. Or ensure you're running on a platform with default credentials (GCP, Railway)

### Error: "Permission denied"

**Solution**: Your service account needs the **Firebase Authentication Admin** role:
1. Go to Firebase Console → Project Settings → Service Accounts
2. Ensure your service account has proper permissions
3. Or download a new service account key

### No Users Returned

**Possible causes**:
1. No users have signed up yet
2. Firebase Admin SDK not properly configured
3. Wrong Firebase project (check your `firebase-service-account.json`)

### Rate Limiting

The API endpoint is rate-limited to **10 requests per minute**. If you hit the limit:
- Wait a minute before retrying
- Use the command-line script for bulk operations
- Consider caching results

---

## Security Considerations

⚠️ **Important**: User data is sensitive information. Follow these security practices:

1. **Protect the API endpoint**:
   - Add authentication/authorization (only admins should access)
   - Use HTTPS in production
   - Consider IP whitelisting

2. **Protect the service account key**:
   - Never commit `firebase-service-account.json` to git
   - Use environment variables in production
   - Rotate keys regularly

3. **Comply with privacy regulations**:
   - Only collect necessary user data
   - Inform users about data collection
   - Allow users to request their data or deletion (GDPR compliance)

---

## Next Steps

1. **Set up authentication** for the `/api/auth/users` endpoint (only allow admins)
2. **Create a dashboard** to view users in your admin panel
3. **Set up automated exports** (e.g., weekly CSV exports)
4. **Implement user analytics** (signup trends, active users, etc.)

---

## Additional Resources

- [Firebase Admin SDK Documentation](https://firebase.google.com/docs/admin/setup)
- [Firebase Authentication User Management](https://firebase.google.com/docs/auth/admin/manage-users)
- [Firebase Console](https://console.firebase.google.com/) - View users directly in the console
