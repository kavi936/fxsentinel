# Refund Request Email Setup Guide

## Overview

The refund request functionality now sends actual emails to the support team when users submit refund requests. This guide explains how to set it up.

## Current Implementation

### What Works Now

✅ **Backend Endpoint**: `/api/request-refund` endpoint created  
✅ **Frontend Integration**: Refund form now calls the backend  
✅ **Database Storage**: Refund requests stored in Firebase  
✅ **Email Framework**: SMTP email sending implemented  
✅ **Validation**: Proper form validation and error handling  
✅ **Rate Limiting**: 5 requests per hour limit  

### What You Need to Configure

🔧 **Email Settings**: SMTP credentials for sending emails  
🔧 **Firebase**: Ensure Firebase is properly configured  

## Email Setup

### Option 1: Gmail SMTP (Recommended for Testing)

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate App Password**:
   - Go to Google Account Settings
   - Security → 2-Step Verification → App passwords
   - Generate a new app password for "Mail"
3. **Add to .env file**:

```env
# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password_here
```

### Option 2: Other SMTP Providers

For other providers (SendGrid, AWS SES, etc.), update the SMTP settings:

```env
# Example for SendGrid
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=your_sendgrid_api_key

# Example for AWS SES
SMTP_SERVER=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USERNAME=your_ses_username
SMTP_PASSWORD=your_ses_password
```

## Testing the Refund Request

### 1. Test Backend Endpoint

```bash
# Run the test script
python3 test_refund_request.py
```

### 2. Test Frontend Form

1. Open the app and go to Profile → Support → Request Refund
2. Fill out the form and submit
3. Check the backend console for logs
4. Check your email (if configured)

### 3. Check Database

If Firebase is configured, refund requests are stored in the `refund_requests` collection with:
- `user_email`: User's email address
- `reason`: Selected refund reason
- `details`: Additional details provided
- `status`: Request status (pending/approved/denied)
- `created_at`: Timestamp of request
- `processed_at`: Timestamp when processed

## Email Content

The refund request emails include:

```
Subject: Refund Request - user@example.com

New refund request received:

User Email: user@example.com
Reason: not-satisfied
Additional Details: User provided details here

Request submitted at: 2024-01-15 14:30:25

Please review and process this refund request.
```

## Fallback Behavior

If email is not configured:
- ✅ Request is still logged to console
- ✅ Request is still stored in database (if Firebase available)
- ✅ User gets success message
- ✅ No functionality is broken

## Security Features

- **Rate Limiting**: 5 refund requests per hour per user
- **Validation**: Email and reason are required
- **Logging**: All requests are logged for audit trail
- **Error Handling**: Graceful fallbacks if email fails

## Production Recommendations

For production deployment:

1. **Use Professional Email Service**: Consider SendGrid, AWS SES, or Mailgun
2. **Add Email Templates**: Create professional HTML email templates
3. **Add Admin Dashboard**: Create interface to manage refund requests
4. **Add Notifications**: Send confirmation emails to users
5. **Add Tracking**: Add refund request tracking numbers

## Troubleshooting

### Email Not Sending

1. Check SMTP credentials in `.env`
2. Verify 2FA is enabled for Gmail
3. Check firewall/network restrictions
4. Review backend console logs

### Database Not Working

1. Check Firebase configuration
2. Verify Firebase service account key
3. Check network connectivity to Firebase

### Frontend Issues

1. Check browser console for errors
2. Verify API endpoint URL in config
3. Check CORS settings

## Support

If you need help setting up email functionality:

1. Check the backend console logs
2. Run the test script: `python3 test_refund_request.py`
3. Verify your `.env` configuration
4. Test with a simple SMTP provider first
