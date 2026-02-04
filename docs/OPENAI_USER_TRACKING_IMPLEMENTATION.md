# OpenAI User Tracking Implementation

## Problem

Previously, all OpenAI API calls were made without user identification, causing all usage to appear under a single account in the OpenAI usage dashboard. This made it impossible to track which individual users were consuming AI Analysis features.

## Solution

Implemented user tracking by adding the `user` parameter to OpenAI API calls. This parameter allows OpenAI to track usage per user in their usage dashboard.

## Changes Made

### 1. Frontend Changes (`src/components/Overview.jsx`)

**Added:**
- Import `useAuth` hook to access current user information
- Extract `currentUser` from auth context
- Include user information in analysis request:
  - `user_id`: Firebase user UID
  - `user_email`: User's email address
  - `user_name`: User's display name

**Code Changes:**
```javascript
// Added import
import { useAuth } from '../contexts/AuthContext';

// Added user context
const { currentUser } = useAuth();

// Updated request body to include user info
body: JSON.stringify({
  event: event,
  analysisType: isPostEvent ? 'post-event' : 'pre-event',
  marketContext: { ... },
  user_id: currentUser?.uid || null,
  user_email: currentUser?.email || null,
  user_name: currentUser?.displayName || null
})
```

### 2. Backend Endpoint Changes (`backend/app.py`)

**Updated `/api/enhanced-analysis/<news_id>` endpoint:**
- Extract user information from request body
- Pass user information to GPT analyzer
- Log user information for debugging

**Code Changes:**
```python
# Extract user information
user_id = request_data.get('user_id')
user_email = request_data.get('user_email')
user_name = request_data.get('user_name')

# Pass to analyzer
user_info = {
    'user_id': user_id,
    'user_email': user_email,
    'user_name': user_name
}
gpt_analysis = gpt_ai_analyzer.analyze_macro_event(
    validated_event, 
    gpt_market_context, 
    analysis_type, 
    user_info=user_info
)
```

### 3. GPT Analyzer Changes (`backend/services/gpt_ai_analysis.py`)

**Updated `GPTAIAnalyzer` class:**
- Modified `analyze_macro_event()` to accept optional `user_info` parameter
- Modified `_generate_enhanced_gpt_analysis()` to accept and use `user_info`
- Added `user` parameter to OpenAI API calls

**Code Changes:**
```python
# Updated method signature
def analyze_macro_event(self, event: Dict, market_context: MarketContext, 
                      analysis_type: str = "pre_event", user_info: Dict = None)

# Prepare user identifier for OpenAI
openai_user = None
if user_info:
    openai_user = user_info.get('user_email') or user_info.get('user_id')
    if openai_user:
        logger.info(f"👤 Tracking OpenAI usage for user: {openai_user}")

# Add user parameter to API call
api_params = {
    "model": model,
    "messages": [...],
    "max_tokens": 2000,
    "temperature": 0.3
}

if openai_user:
    api_params["user"] = openai_user

response = self.client.chat.completions.create(**api_params)
```

## How It Works

1. **User initiates analysis**: User clicks "Generate AI Analysis" in the frontend
2. **Frontend sends request**: Includes user_id, user_email, and user_name in request body
3. **Backend extracts user info**: Endpoint extracts user information from request
4. **Analyzer receives user info**: GPT analyzer receives user information as parameter
5. **OpenAI API call**: User email (or user_id if email unavailable) is passed as `user` parameter
6. **Usage tracking**: OpenAI tracks usage per user in their dashboard

## User Identifier Priority

The system uses the following priority for user identification:
1. **User Email** (preferred) - Most readable in OpenAI dashboard
2. **User ID** (fallback) - Used if email is not available
3. **None** (anonymous) - If no user information is provided

## Viewing Usage in OpenAI Dashboard

1. Go to [https://platform.openai.com/usage](https://platform.openai.com/usage)
2. Use the dropdown next to "Daily usage breakdown"
3. Select a specific user (identified by their email or user_id)
4. View usage statistics for that individual user

## Benefits

1. **Per-User Tracking**: See which users are consuming the most AI Analysis features
2. **Cost Attribution**: Understand costs per user for billing/accounting
3. **Usage Analytics**: Identify power users and usage patterns
4. **Debugging**: Easier to troubleshoot issues for specific users
5. **Compliance**: Better audit trail of API usage

## Notes

- **Privacy**: User emails are only used for OpenAI tracking and are not stored by OpenAI beyond usage statistics
- **Fallback**: If user is not logged in, API calls proceed without user tracking (anonymous usage)
- **Backward Compatible**: Changes are backward compatible - if user_info is not provided, API calls work normally without user parameter

## Other Analyzers

Currently, user tracking is implemented for:
- ✅ `GPTAIAnalyzer` (primary analyzer used by `/api/enhanced-analysis`)

Other analyzers that may need similar updates:
- `MVPNewsAnalyzer` (used by `/api/analysis`)
- `EnhancedTraderAnalyzer`
- `OptimizedChatGPTAnalyzer`
- `ProfessionalAIAnalyzer`

These can be updated following the same pattern if they are actively used.

## Testing

To verify user tracking is working:

1. **Check logs**: Look for log messages like:
   ```
   👤 User info - ID: <user_id>, Email: <email>, Name: <name>
   👤 Tracking OpenAI usage for user: <email>
   ```

2. **Check OpenAI Dashboard**: 
   - Wait a few minutes after making API calls
   - Check OpenAI usage dashboard
   - Verify individual users appear in the user dropdown

3. **Test with different users**:
   - Login as different users
   - Generate AI analyses
   - Verify each user's usage appears separately in dashboard

## Future Enhancements

1. **Add user tracking to other analyzers** if they're actively used
2. **Add user tracking to cached analysis** (currently cached analyses don't track users)
3. **Create internal usage dashboard** showing per-user statistics
4. **Add user tracking to batch operations** if implemented
