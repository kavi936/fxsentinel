# Using the Protected `/api/auth/users` Endpoint

## Overview

The `/api/auth/users` endpoint is now **protected** and requires:
1. ✅ Firebase Authentication (valid ID token)
2. ✅ Admin/Developer status (email in `DEVELOPER_EMAILS`)

## How to Use

### From Frontend (JavaScript/React)

```javascript
import { auth } from '../config/firebase';
import { useAuth } from '../contexts/AuthContext';

async function fetchUsers() {
  try {
    // Get current user
    const user = auth.currentUser;
    if (!user) {
      throw new Error('Please sign in first');
    }
    
    // Get Firebase ID token
    const token = await user.getIdToken();
    
    // Make authenticated request
    const response = await fetch('http://localhost:5001/api/auth/users', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      const error = await response.json();
      if (response.status === 401) {
        throw new Error('Authentication failed. Please sign in again.');
      } else if (response.status === 403) {
        throw new Error('Admin access required. Only developers can access this endpoint.');
      }
      throw new Error(error.message || 'Failed to fetch users');
    }
    
    const data = await response.json();
    console.log(`Found ${data.total} users`);
    return data.users;
    
  } catch (error) {
    console.error('Error fetching users:', error);
    throw error;
  }
}

// Usage in React component
function UserList() {
  const { currentUser } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    if (currentUser) {
      setLoading(true);
      fetchUsers()
        .then(setUsers)
        .catch(setError)
        .finally(() => setLoading(false));
    }
  }, [currentUser]);
  
  if (loading) return <div>Loading users...</div>;
  if (error) return <div>Error: {error.message}</div>;
  
  return (
    <div>
      <h2>Users ({users.length})</h2>
      <ul>
        {users.map(user => (
          <li key={user.uid}>
            {user.display_name} ({user.email})
          </li>
        ))}
      </ul>
    </div>
  );
}
```

### From Backend/Python Script

```python
import requests
import firebase_admin
from firebase_admin import auth, credentials

# Initialize Firebase Admin (if not already done)
if not firebase_admin._apps:
    cred = credentials.Certificate('firebase-service-account.json')
    firebase_admin.initialize_app(cred)

# Get ID token for a user (you need to be authenticated)
# This is typically done client-side, but for server-to-server:
# Use the service account or get token from authenticated user

# For testing, you can use the script directly:
# python3 backend/scripts/list_firebase_users.py
```

### Using curl (for testing)

**Note**: You need a Firebase ID token. Get it from your browser's developer console:

1. Open your app in browser
2. Open Developer Console (F12)
3. Run:
   ```javascript
   firebase.auth().currentUser.getIdToken().then(token => console.log(token))
   ```
4. Copy the token
5. Use in curl:
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN_HERE" \
        http://localhost:5001/api/auth/users
   ```

## Error Responses

### 401 Unauthorized
```json
{
  "error": "Unauthorized",
  "message": "Firebase ID token required in Authorization header. Format: Authorization: Bearer <token>"
}
```
**Solution**: Include valid Firebase ID token in Authorization header

### 403 Forbidden
```json
{
  "error": "Forbidden",
  "message": "Admin access required. Only developers can access this endpoint."
}
```
**Solution**: Your email must be in `DEVELOPER_EMAILS` environment variable

### 429 Too Many Requests
```json
{
  "error": "Rate limit exceeded"
}
```
**Solution**: Wait before retrying (limit: 10 requests per minute)

## Security Notes

- ✅ **Always use HTTPS** in production (never HTTP)
- ✅ **Never expose** your Firebase ID token publicly
- ✅ **Rotate tokens** regularly (Firebase tokens expire after 1 hour)
- ✅ **Check permissions** before accessing sensitive endpoints
- ✅ **Log access** for audit purposes

## Troubleshooting

### "Invalid token" error
- Token may be expired (tokens expire after 1 hour)
- Get a new token: `await user.getIdToken(true)` (force refresh)

### "Forbidden" error
- Your email is not in `DEVELOPER_EMAILS`
- Check `backend/.env` file for `DEVELOPER_EMAILS` setting
- Add your email: `DEVELOPER_EMAILS=your@email.com,admin@email.com`

### "Rate limit exceeded"
- You're making too many requests
- Wait 1 minute before retrying
- Consider caching results client-side

## Example: Complete React Hook

```javascript
import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { auth } from '../config/firebase';

export function useFirebaseUsers() {
  const { currentUser } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const fetchUsers = async () => {
    if (!currentUser) {
      setError('Not authenticated');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const token = await currentUser.getIdToken();
      const response = await fetch('/api/auth/users', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Failed to fetch users');
      }
      
      const data = await response.json();
      setUsers(data.users);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  useEffect(() => {
    if (currentUser) {
      fetchUsers();
    }
  }, [currentUser]);
  
  return { users, loading, error, refetch: fetchUsers };
}
```

## See Also

- `docs/API_SECURITY_GUIDE.md` - Complete security implementation guide
- `docs/FIREBASE_USER_MANAGEMENT.md` - User management documentation
- `backend/scripts/list_firebase_users.py` - Command-line script (no auth needed)
