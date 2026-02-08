# API Security Guide: Protecting User Data Endpoints

## 🚨 Why This Matters

The `/api/auth/users` endpoint currently exposes **sensitive user information** without authentication:
- User email addresses
- Display names
- User IDs (UIDs)
- Account creation dates
- Last sign-in timestamps
- Authentication providers

### Security Risks

**Without protection, anyone can:**

1. **Enumerate all users** - See who has signed up for your app
2. **Harvest email addresses** - Collect emails for spam/marketing
3. **Track user activity** - See when users last logged in
4. **Identify user patterns** - Analyze signup trends, active users
5. **Privacy violations** - Access personal information without consent
6. **GDPR/CCPA violations** - Expose user data without authorization (legal risk)
7. **Competitive intelligence** - Competitors can see your user base size

### Real-World Impact

- **Data breach**: User emails leaked publicly
- **Legal liability**: GDPR fines up to 4% of annual revenue
- **User trust**: Users lose confidence in your security
- **Reputation damage**: Public security incident

---

## 🔒 Security Solutions

### Option 1: Firebase ID Token Verification (Recommended)

**Best for**: When users are already authenticated in your frontend

**How it works**: Frontend sends Firebase ID token, backend verifies it

#### Implementation

**Step 1: Create Authentication Helper**

Add to `backend/app.py`:

```python
from firebase_admin import auth
from functools import wraps

def verify_firebase_token(f):
    """Decorator to verify Firebase ID token"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                'error': 'Missing or invalid authorization header',
                'message': 'Please provide a valid Firebase ID token'
            }), 401
        
        token = auth_header.split('Bearer ')[1]
        
        try:
            # Verify the token
            decoded_token = auth.verify_id_token(token)
            # Add user info to request context
            request.current_user = decoded_token
            request.user_id = decoded_token['uid']
            return f(*args, **kwargs)
        except auth.InvalidIdTokenError:
            return jsonify({
                'error': 'Invalid token',
                'message': 'The provided token is invalid or expired'
            }), 401
        except auth.ExpiredIdTokenError:
            return jsonify({
                'error': 'Expired token',
                'message': 'Please sign in again'
            }), 401
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return jsonify({
                'error': 'Authentication failed',
                'message': 'Unable to verify authentication'
            }), 401
    
    return decorated_function

def require_admin(f):
    """Decorator to require admin/developer role"""
    @wraps(f)
    @verify_firebase_token
    def decorated_function(*args, **kwargs):
        user_id = request.user_id
        
        # Check if user is developer/admin
        # You can check custom claims or your developer list
        developer_emails = os.getenv('DEVELOPER_EMAILS', '').split(',')
        user_email = request.current_user.get('email', '')
        
        if user_email not in developer_emails:
            # Check custom claims for admin role
            custom_claims = request.current_user.get('custom_claims', {})
            if not custom_claims.get('admin', False):
                return jsonify({
                    'error': 'Forbidden',
                    'message': 'Admin access required'
                }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function
```

**Step 2: Protect the Endpoint**

```python
@app.route('/api/auth/users', methods=['GET'])
@limiter.limit("10 per minute")
@require_admin  # Only admins can access
def get_firebase_auth_users():
    # ... existing code ...
```

**Step 3: Frontend Usage**

```javascript
import { auth } from '../config/firebase';
import { useAuth } from '../contexts/AuthContext';

async function getUsers() {
  const user = auth.currentUser;
  if (!user) {
    throw new Error('Not authenticated');
  }
  
  // Get Firebase ID token
  const token = await user.getIdToken();
  
  // Make authenticated request
  const response = await fetch('/api/auth/users', {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  
  if (!response.ok) {
    if (response.status === 403) {
      throw new Error('Admin access required');
    }
    throw new Error('Failed to fetch users');
  }
  
  return response.json();
}
```

---

### Option 2: API Key Authentication

**Best for**: Server-to-server communication, admin tools, scripts

**How it works**: Require a secret API key in the request header

#### Implementation

**Step 1: Add API Key to Environment**

```bash
# backend/.env
ADMIN_API_KEY=your-secret-api-key-here-change-this-in-production
```

**Step 2: Create API Key Decorator**

```python
from functools import wraps

def require_api_key(f):
    """Decorator to require API key authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        expected_key = os.getenv('ADMIN_API_KEY')
        
        if not expected_key:
            logger.error("ADMIN_API_KEY not configured")
            return jsonify({
                'error': 'Server configuration error'
            }), 500
        
        if not api_key or api_key != expected_key:
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Valid API key required'
            }), 401
        
        return f(*args, **kwargs)
    
    return decorated_function
```

**Step 3: Protect the Endpoint**

```python
@app.route('/api/auth/users', methods=['GET'])
@limiter.limit("10 per minute")
@require_api_key
def get_firebase_auth_users():
    # ... existing code ...
```

**Step 4: Usage**

```bash
# Using curl
curl -H "X-API-Key: your-secret-api-key-here" \
     http://localhost:5001/api/auth/users

# Or as query parameter
curl "http://localhost:5001/api/auth/users?api_key=your-secret-api-key-here"
```

---

### Option 3: IP Whitelisting

**Best for**: Restricting access to specific servers/IPs

**How it works**: Only allow requests from trusted IP addresses

#### Implementation

```python
from functools import wraps

ALLOWED_IPS = [
    '127.0.0.1',  # Localhost
    '::1',        # IPv6 localhost
    # Add your production server IPs
    # '123.456.789.0',  # Your server IP
]

def require_whitelisted_ip(f):
    """Decorator to require whitelisted IP address"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = request.remote_addr
        
        # Check if IP is whitelisted
        if client_ip not in ALLOWED_IPS:
            logger.warning(f"Blocked request from unauthorized IP: {client_ip}")
            return jsonify({
                'error': 'Forbidden',
                'message': 'Access denied from this IP address'
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function

# Use it
@app.route('/api/auth/users', methods=['GET'])
@require_whitelisted_ip
def get_firebase_auth_users():
    # ... existing code ...
```

**Note**: IP whitelisting alone is not sufficient - combine with other methods.

---

### Option 4: Role-Based Access Control (RBAC)

**Best for**: Different permission levels (admin, moderator, viewer)

**How it works**: Check user's role/permissions before allowing access

#### Implementation

```python
def require_role(*allowed_roles):
    """Decorator factory for role-based access"""
    def decorator(f):
        @wraps(f)
        @verify_firebase_token
        def decorated_function(*args, **kwargs):
            user_id = request.user_id
            
            # Get user's role from custom claims or database
            custom_claims = request.current_user.get('custom_claims', {})
            user_role = custom_claims.get('role', 'user')
            
            if user_role not in allowed_roles:
                return jsonify({
                    'error': 'Forbidden',
                    'message': f'Required role: {", ".join(allowed_roles)}'
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

# Usage
@app.route('/api/auth/users', methods=['GET'])
@require_role('admin', 'moderator')
def get_firebase_auth_users():
    # ... existing code ...
```

**Setting Custom Claims** (one-time setup):

```python
# Run this once to set admin role for a user
from firebase_admin import auth

user = auth.get_user_by_email('admin@example.com')
auth.set_custom_user_claims(user.uid, {'role': 'admin', 'admin': True})
```

---

## 🎯 Recommended Approach: Multi-Layer Security

**Best Practice**: Combine multiple methods for defense in depth:

```python
@app.route('/api/auth/users', methods=['GET'])
@limiter.limit("10 per minute")  # Rate limiting
@verify_firebase_token           # Authentication
@require_admin                   # Authorization
def get_firebase_auth_users():
    # Additional security: Log access
    logger.info(f"User {request.user_id} accessed user list")
    
    # ... existing code ...
```

---

## 📊 Security Comparison

| Method | Security Level | Complexity | Use Case |
|--------|---------------|-----------|----------|
| **Firebase Token** | ⭐⭐⭐⭐⭐ | Medium | User-facing admin panel |
| **API Key** | ⭐⭐⭐⭐ | Low | Server-to-server, scripts |
| **IP Whitelist** | ⭐⭐⭐ | Low | Fixed server locations |
| **RBAC** | ⭐⭐⭐⭐⭐ | High | Complex permission systems |
| **Combined** | ⭐⭐⭐⭐⭐ | High | Production (recommended) |

---

## 🚀 Quick Implementation

### For Your Current Setup

Since you already have Firebase Auth and developer email checking, here's the quickest implementation:

**1. Add to `backend/app.py`** (after Firebase initialization):

```python
from functools import wraps

def require_admin_auth(f):
    """Require Firebase authentication + admin/developer status"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get Firebase ID token from header
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Firebase ID token required in Authorization header'
            }), 401
        
        token = auth_header.split('Bearer ')[1]
        
        try:
            # Verify token
            decoded_token = auth.verify_id_token(token)
            user_email = decoded_token.get('email', '')
            
            # Check if user is developer/admin
            developer_emails = os.getenv('DEVELOPER_EMAILS', '').split(',')
            developer_emails = [e.strip() for e in developer_emails if e.strip()]
            
            if user_email not in developer_emails:
                return jsonify({
                    'error': 'Forbidden',
                    'message': 'Admin access required'
                }), 403
            
            # Store user info for use in endpoint
            request.current_user = decoded_token
            request.user_id = decoded_token['uid']
            
            return f(*args, **kwargs)
            
        except auth.InvalidIdTokenError:
            return jsonify({
                'error': 'Invalid token',
                'message': 'The authentication token is invalid'
            }), 401
        except Exception as e:
            logger.error(f"Auth error: {e}")
            return jsonify({
                'error': 'Authentication failed',
                'message': str(e)
            }), 401
    
    return decorated_function
```

**2. Protect your endpoint**:

```python
@app.route('/api/auth/users', methods=['GET'])
@limiter.limit("10 per minute")
@require_admin_auth  # Add this decorator
def get_firebase_auth_users():
    # ... existing code ...
```

**3. Update frontend** (if calling from frontend):

```javascript
const token = await auth.currentUser.getIdToken();
const response = await fetch('/api/auth/users', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```

---

## ✅ Security Checklist

Before deploying to production:

- [ ] ✅ Add authentication (Firebase token or API key)
- [ ] ✅ Add authorization (admin/role check)
- [ ] ✅ Enable rate limiting (already done)
- [ ] ✅ Log access attempts
- [ ] ✅ Use HTTPS only (no HTTP in production)
- [ ] ✅ Validate all inputs
- [ ] ✅ Sanitize output (don't expose sensitive fields)
- [ ] ✅ Set up monitoring/alerts for unauthorized access
- [ ] ✅ Review and rotate API keys regularly
- [ ] ✅ Document who has access and why

---

## 📝 Additional Considerations

### Data Minimization

Only return necessary fields:

```python
# Instead of returning everything, filter sensitive data
user_info = {
    'uid': user.uid,
    'email': user.email,  # Only if needed
    'display_name': user.display_name,
    'created_at': ...,
    # Don't include: phone_number, photo_url, etc. unless needed
}
```

### Audit Logging

Log all access attempts:

```python
logger.info(f"Admin {request.user_id} accessed user list at {datetime.now()}")
# Store in database for audit trail
```

### Response Caching

Consider caching responses for admin users to reduce load:

```python
from functools import lru_cache
from datetime import datetime, timedelta

# Cache for 5 minutes
@lru_cache(maxsize=1)
def get_cached_users(cache_key):
    # ... fetch users ...
    return users
```

---

## 🔗 Related Documentation

- [Firebase Admin SDK Auth](https://firebase.google.com/docs/auth/admin)
- [OWASP API Security](https://owasp.org/www-project-api-security/)
- [GDPR Compliance](https://gdpr.eu/)

---

## Need Help?

If you need assistance implementing any of these security measures, refer to:
- `docs/FIREBASE_USER_MANAGEMENT.md` - User management guide
- `backend/app.py` - See existing auth patterns
- Firebase Console - Manage user roles and permissions
