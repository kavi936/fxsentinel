# Environment Variables Setup for Google Sheets Integration

## Required Environment Variables

To enable Google Sheets integration, you need to set these environment variables:

### 1. GOOGLE_SHEETS_CREDENTIALS_JSON

**What it is:** The complete JSON content of your Google Cloud service account credentials file.

**How to get it:**
1. Download the service account JSON key from Google Cloud Console
2. Open the JSON file in a text editor
3. Copy the entire contents (all of it, including `{` and `}`)
4. Paste it as a single-line string (or keep it as multi-line JSON)

**Format:**
```json
{"type":"service_account","project_id":"your-project","private_key_id":"...","private_key":"-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n","client_email":"...","client_id":"...","auth_uri":"...","token_uri":"...","auth_provider_x509_cert_url":"...","client_x509_cert_url":"..."}
```

**Important:** 
- Keep it as a single string (no line breaks in production)
- Escape quotes if needed
- Never commit this to git!

### 2. GOOGLE_SHEETS_SPREADSHEET_ID

**What it is:** The unique ID of your Google Spreadsheet.

**How to get it:**
1. Open your Google Spreadsheet
2. Look at the URL: `https://docs.google.com/spreadsheets/d/SPREADSHEET_ID_HERE/edit`
3. Copy the part between `/d/` and `/edit`

**Example:**
```
URL: https://docs.google.com/spreadsheets/d/1a2b3c4d5e6f7g8h9i0j/edit
ID: 1a2b3c4d5e6f7g8h9i0j
```

### 3. GOOGLE_SHEETS_CACHE_TTL (Optional)

**What it is:** How long to cache data before refreshing (in seconds).

**Default:** 30 (30 seconds)

**Recommended values:**
- Development: 30 (30 seconds) - very frequent updates for testing
- Production: 60-120 (1-2 minutes) - balances freshness with API limits
- For very active data: 30 (30 seconds) - maximum freshness

## Setting Up Environment Variables

### For Local Development

Create or edit `.env` file in the `backend/` directory:

```env
# Google Sheets Integration
# IMPORTANT: Paste the ENTIRE contents of your service account JSON file here
# Open the downloaded JSON file, copy everything, and paste it here as a single line
GOOGLE_SHEETS_CREDENTIALS_JSON='{"type":"service_account","project_id":"your-project","private_key_id":"...","private_key":"-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n","client_email":"...","client_id":"...","auth_uri":"...","token_uri":"...","auth_provider_x509_cert_url":"...","client_x509_cert_url":"..."}'

GOOGLE_SHEETS_SPREADSHEET_ID=1a2b3c4d5e6f7g8h9i0j
GOOGLE_SHEETS_CACHE_TTL=30
```

**Example of what the actual JSON looks like:**
```json
{
  "type": "service_account",
  "project_id": "fxsentinel-123456",
  "private_key_id": "abc123def456...",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC...\n-----END PRIVATE KEY-----\n",
  "client_email": "fxsentinel-sheets@fxsentinel-123456.iam.gserviceaccount.com",
  "client_id": "123456789012345678901",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/fxsentinel-sheets%40fxsentinel-123456.iam.gserviceaccount.com"
}
```

**When pasting into .env file, make it a single line:**
```env
GOOGLE_SHEETS_CREDENTIALS_JSON='{"type":"service_account","project_id":"fxsentinel-123456","private_key_id":"abc123...","private_key":"-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC...\n-----END PRIVATE KEY-----\n","client_email":"fxsentinel-sheets@fxsentinel-123456.iam.gserviceaccount.com","client_id":"123456789012345678901","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url":"https://www.googleapis.com/robot/v1/metadata/x509/fxsentinel-sheets%40fxsentinel-123456.iam.gserviceaccount.com"}'
```

**Note:** For local development, you can also use a file path instead:
```env
GOOGLE_SHEETS_CREDENTIALS_PATH=./credentials.json
```

### For Railway (Production)

1. Go to your Railway project dashboard
2. Click on your backend service
3. Go to "Variables" tab
4. Click "New Variable"
5. Add each variable:

**Variable 1:**
- Name: `GOOGLE_SHEETS_CREDENTIALS_JSON`
- Value: (paste the entire JSON content as a single string)
- Click "Add"

**Variable 2:**
- Name: `GOOGLE_SHEETS_SPREADSHEET_ID`
- Value: (your spreadsheet ID)
- Click "Add"

**Variable 3 (Optional):**
- Name: `GOOGLE_SHEETS_CACHE_TTL`
- Value: `30` (or `60` for production)
- Click "Add"

### For Vercel (Production)

1. Go to your Vercel project dashboard
2. Click on "Settings" → "Environment Variables"
3. Add each variable:

**Variable 1:**
- Key: `GOOGLE_SHEETS_CREDENTIALS_JSON`
- Value: (paste the entire JSON content)
- Environment: Production, Preview, Development (select all)
- Click "Save"

**Variable 2:**
- Key: `GOOGLE_SHEETS_SPREADSHEET_ID`
- Value: (your spreadsheet ID)
- Environment: Production, Preview, Development (select all)
- Click "Save"

**Variable 3 (Optional):**
- Key: `GOOGLE_SHEETS_CACHE_TTL`
- Value: `30` (or `60` for production)
- Environment: Production, Preview, Development (select all)
- Click "Save"

## Formatting JSON for Environment Variables

### Option 1: Single Line (Recommended for Production)

Remove all line breaks and spaces:
```json
{"type":"service_account","project_id":"your-project",...}
```

### Option 2: Escaped Multi-line (If your platform supports it)

Keep the JSON formatted but escape quotes:
```json
{
  "type": "service_account",
  "project_id": "your-project",
  ...
}
```

### Option 3: Base64 Encoded (Advanced)

If your platform has issues with special characters:
```bash
# Encode
cat credentials.json | base64

# Then decode in Python:
import base64
import json
creds_json = base64.b64decode(os.getenv('GOOGLE_SHEETS_CREDENTIALS_B64')).decode('utf-8')
creds_dict = json.loads(creds_json)
```

## Testing Your Setup

### 1. Check if variables are loaded

Add this to your backend code temporarily:
```python
import os
print("GOOGLE_SHEETS_CREDENTIALS_JSON:", "SET" if os.getenv('GOOGLE_SHEETS_CREDENTIALS_JSON') else "NOT SET")
print("GOOGLE_SHEETS_SPREADSHEET_ID:", os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID'))
```

### 2. Test the API endpoint

```bash
# Local
curl http://localhost:5000/api/economy-indicators/US

# Production
curl https://your-backend-url.com/api/economy-indicators/US
```

### 3. Check logs

Look for these messages:
- ✅ "Google Sheets service initialized successfully"
- ✅ "Successfully fetched X indicators for US"
- ⚠️ "Google Sheets service not available" (means credentials missing)

## Troubleshooting

### Issue: "GOOGLE_SHEETS_CREDENTIALS_JSON not set"
**Solution:** Make sure the environment variable is set and the JSON is valid

### Issue: "Failed to parse GOOGLE_SHEETS_CREDENTIALS_JSON"
**Solution:** Check that the JSON is properly formatted and escaped

### Issue: "Sheet 'US_Indicators' not found"
**Solution:** Make sure your Google Sheet has a tab named exactly "US_Indicators" (case-sensitive)

### Issue: "Permission denied"
**Solution:** Make sure you shared the Google Sheet with the service account email

## Security Best Practices

1. ✅ **Never commit credentials to git**
   - Add `.env` to `.gitignore`
   - Never commit `credentials.json`

2. ✅ **Use environment variables in production**
   - Don't hardcode credentials
   - Use platform secrets management (Railway/Vercel)

3. ✅ **Rotate credentials periodically**
   - Create new service account keys every 6-12 months
   - Revoke old keys

4. ✅ **Limit permissions**
   - Service account only needs "Viewer" access to the sheet
   - Don't give it edit permissions unless necessary

5. ✅ **Monitor usage**
   - Check Google Cloud Console for API usage
   - Set up alerts for unusual activity

