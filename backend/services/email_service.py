"""
Email service for FXSentinel - sends branded emails via Resend.
Used for verification emails and other transactional emails.
"""
import os
import logging

logger = logging.getLogger(__name__)

# Resend API key - required for sending
RESEND_API_KEY = os.getenv('RESEND_API_KEY')
SENDER_EMAIL = 'FXSentinel <no-reply@fxsentinel.io>'


def _get_resend_client():
    """Lazy import to avoid failure if resend not installed."""
    try:
        import resend
        return resend
    except ImportError:
        return None


def send_verification_email(to_email: str, verification_url: str, display_name: str = None) -> dict:
    """
    Send branded email verification email via Resend.
    
    Args:
        to_email: Recipient email address
        verification_url: Firebase-generated verification link
        display_name: Optional display name for personalization
        
    Returns:
        dict with 'success' (bool) and optional 'error' (str)
    """
    resend_module = _get_resend_client()
    if not resend_module:
        logger.error("Resend package not installed")
        return {'success': False, 'error': 'Email service not configured'}
    
    if not RESEND_API_KEY:
        logger.error("RESEND_API_KEY not set")
        return {'success': False, 'error': 'Email service not configured'}
    
    name = display_name or 'there'
    logo_url = 'https://fxsentinel.io/favicon.png'

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verify your FXSentinel email</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #000000;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #000000; padding: 48px 24px;">
        <tr>
            <td align="center">
                <table role="presentation" width="600" cellspacing="0" cellpadding="0" style="background-color: #0f0f0f; border-radius: 12px; border: 1px solid rgba(255, 68, 68, 0.25); box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6), 0 0 0 1px rgba(255, 68, 68, 0.1);">
                    <!-- Header with logo and branding -->
                    <tr>
                        <td style="padding: 36px 40px 24px; border-bottom: 1px solid rgba(255, 68, 68, 0.2); background-color: #1a0a0a; background: linear-gradient(180deg, #1a0a0a 0%, #0f0f0f 100%); border-radius: 12px 12px 0 0;">
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                                <tr>
                                    <td style="vertical-align: middle;">
                                        <img src="{logo_url}" alt="FXSentinel" width="48" height="48" style="display: block; width: 48px; height: 48px; border-radius: 10px;" />
                                    </td>
                                    <td style="vertical-align: middle; padding-left: 16px;">
                                        <h1 style="margin: 0 0 4px; font-size: 26px; font-weight: 700; color: #ffffff; letter-spacing: -0.5px;">FXSentinel</h1>
                                        <p style="margin: 0; font-size: 13px; color: rgba(255, 255, 255, 0.6); letter-spacing: 0.5px;">Market Intelligence Platform</p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <!-- Body -->
                    <tr>
                        <td style="padding: 36px 40px 40px;">
                            <h2 style="margin: 0 0 20px; font-size: 22px; font-weight: 600; color: #ffffff;">Verify your email</h2>
                            <p style="margin: 0 0 20px; font-size: 16px; line-height: 1.65; color: rgba(255, 255, 255, 0.9);">
                                Hi {name},
                            </p>
                            <p style="margin: 0 0 28px; font-size: 16px; line-height: 1.65; color: rgba(255, 255, 255, 0.85);">
                                Thanks for signing up for FXSentinel. Please verify your email address by clicking the button below to access your dashboard.
                            </p>
                            <table role="presentation" cellspacing="0" cellpadding="0" style="margin: 0 0 28px;">
                                <tr>
                                    <td>
                                        <a href="{verification_url}" style="display: inline-block; padding: 16px 32px; background-color: #ff4444; background: linear-gradient(135deg, #ff4444 0%, #cc2222 100%); color: #ffffff !important; text-decoration: none; font-weight: 600; font-size: 16px; border-radius: 8px; box-shadow: 0 4px 14px rgba(255, 68, 68, 0.4);">Verify email</a>
                                    </td>
                                </tr>
                            </table>
                            <p style="margin: 0; font-size: 13px; color: rgba(255, 255, 255, 0.55);">
                                If the button doesn't work, copy and paste this link into your browser:
                            </p>
                            <p style="margin: 8px 0 0; font-size: 12px; word-break: break-all; color: rgba(255, 255, 255, 0.45); line-height: 1.5;">
                                {verification_url}
                            </p>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 24px 40px; border-top: 1px solid rgba(255, 68, 68, 0.15); background: rgba(0, 0, 0, 0.3); border-radius: 0 0 12px 12px;">
                            <p style="margin: 0; font-size: 12px; color: rgba(255, 255, 255, 0.5);">
                                If you didn't create an FXSentinel account, you can safely ignore this email.
                            </p>
                            <p style="margin: 12px 0 0; font-size: 12px; color: rgba(255, 255, 255, 0.4);">
                                © FXSentinel · fxsentinel.io
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
    
    try:
        resend_module.api_key = RESEND_API_KEY
        resend_module.Emails.send({
            'from': SENDER_EMAIL,
            'to': [to_email],
            'subject': 'Verify your FXSentinel email',
            'html': html
        })
        logger.info(f"Verification email sent to {to_email}")
        return {'success': True}
    except Exception as e:
        logger.exception(f"Failed to send verification email to {to_email}: {e}")
        return {'success': False, 'error': str(e)}
