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
REPLY_TO_EMAIL = 'fxsentinelapp@gmail.com'  # For welcome email replies


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

    # Professional, future-style font for header (matches app landing)
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verify your FXSentinel email</title>
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&display=swap" rel="stylesheet">
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #000000;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #000000; padding: 48px 24px;">
        <tr>
            <td align="center">
                <table role="presentation" width="600" cellspacing="0" cellpadding="0" style="background-color: #0f0f0f; border-radius: 12px; border: 1px solid rgba(255, 68, 68, 0.25); box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6), 0 0 0 1px rgba(255, 68, 68, 0.1);">
                    <!-- Header: Space Grotesk for clean, modern look -->
                    <tr>
                        <td style="padding: 36px 40px 24px; border-bottom: 1px solid rgba(255, 68, 68, 0.2); background-color: #1a0a0a; background: linear-gradient(180deg, #1a0a0a 0%, #0f0f0f 100%); border-radius: 12px 12px 0 0;">
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                                <tr>
                                    <td style="vertical-align: middle;">
                                        <img src="{logo_url}" alt="FXSentinel" width="48" height="48" style="display: block; width: 48px; height: 48px; border-radius: 10px;" />
                                    </td>
                                    <td style="vertical-align: middle; padding-left: 16px;">
                                        <h1 style="margin: 0 0 4px; font-family: 'Space Grotesk', -apple-system, sans-serif; font-size: 26px; font-weight: 700; color: #ffffff; letter-spacing: -0.02em;">FXSentinel</h1>
                                        <p style="margin: 0; font-family: 'Space Grotesk', -apple-system, sans-serif; font-size: 12px; font-weight: 500; color: rgba(255, 255, 255, 0.65); letter-spacing: 0.08em; text-transform: uppercase;">Market Intelligence Platform</p>
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


def send_welcome_email(to_email: str, display_name: str = None) -> dict:
    """
    Send a Zeno-style welcome email to new signups.
    Personal tone, founder story, 3 tips to get started, P.S. encouraging reply.
    Uses Reply-To so replies go to support inbox.

    Args:
        to_email: Recipient email address
        display_name: Optional display name (e.g. "John Smith" -> "John")

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

    # Use first name if available, else "there"
    first_name = 'there'
    if display_name and display_name.strip():
        first_name = display_name.strip().split()[0] if display_name.strip().split() else 'there'

    logo_url = 'https://fxsentinel.io/favicon.png'
    base_url = 'https://fxsentinel.io'

    # Same header font as verification: Space Grotesk for consistent branding
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome to FXSentinel</title>
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&display=swap" rel="stylesheet">
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #000000;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #000000; padding: 48px 24px;">
        <tr>
            <td align="center">
                <table role="presentation" width="600" cellspacing="0" cellpadding="0" style="background-color: #0f0f0f; border-radius: 12px; border: 1px solid rgba(255, 68, 68, 0.25); box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6), 0 0 0 1px rgba(255, 68, 68, 0.1);">
                    <!-- Header: Space Grotesk for clean, modern look -->
                    <tr>
                        <td style="padding: 36px 40px 24px; border-bottom: 1px solid rgba(255, 68, 68, 0.2); background-color: #1a0a0a; background: linear-gradient(180deg, #1a0a0a 0%, #0f0f0f 100%); border-radius: 12px 12px 0 0;">
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                                <tr>
                                    <td style="vertical-align: middle;">
                                        <img src="{logo_url}" alt="FXSentinel" width="48" height="48" style="display: block; width: 48px; height: 48px; border-radius: 10px;" />
                                    </td>
                                    <td style="vertical-align: middle; padding-left: 16px;">
                                        <h1 style="margin: 0 0 4px; font-family: 'Space Grotesk', -apple-system, sans-serif; font-size: 26px; font-weight: 700; color: #ffffff; letter-spacing: -0.02em;">FXSentinel</h1>
                                        <p style="margin: 0; font-family: 'Space Grotesk', -apple-system, sans-serif; font-size: 12px; font-weight: 500; color: rgba(255, 255, 255, 0.65); letter-spacing: 0.08em; text-transform: uppercase;">Market Intelligence Platform</p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <!-- Body -->
                    <tr>
                        <td style="padding: 36px 40px 40px;">
                            <p style="margin: 0 0 20px; font-size: 16px; line-height: 1.7; color: rgba(255, 255, 255, 0.95);">
                                Hey {first_name},
                            </p>
                            <p style="margin: 0 0 20px; font-size: 16px; line-height: 1.7; color: rgba(255, 255, 255, 0.9);">
                                We built FXSentinel because we wanted a better way for retail traders to stay on top of market-moving news—without the noise.
                            </p>
                            <p style="margin: 0 0 20px; font-size: 16px; line-height: 1.7; color: rgba(255, 255, 255, 0.9);">
                                Real-time alerts, AI-powered analysis, and actionable macro insights—all in one place.
                            </p>
                            <p style="margin: 0 0 28px; font-size: 16px; line-height: 1.7; color: rgba(255, 255, 255, 0.9);">
                                Here are 3 tips to get started:
                            </p>
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin: 0 0 28px;">
                                <tr>
                                    <td style="padding: 12px 0; border-bottom: 1px solid rgba(255, 255, 255, 0.08);">
                                        <a href="{base_url}/verify-email" style="color: #ff4444; text-decoration: none; font-weight: 600; font-size: 15px;">1. Verify your email</a>
                                        <p style="margin: 4px 0 0; font-size: 14px; color: rgba(255, 255, 255, 0.6);">Check your inbox and click the link to unlock your dashboard.</p>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 12px 0; border-bottom: 1px solid rgba(255, 255, 255, 0.08);">
                                        <a href="{base_url}/dashboard" style="color: #ff4444; text-decoration: none; font-weight: 600; font-size: 15px;">2. Explore your dashboard</a>
                                        <p style="margin: 4px 0 0; font-size: 14px; color: rgba(255, 255, 255, 0.6);">Live news, economic calendar, and AI analysis at your fingertips.</p>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 12px 0;">
                                        <a href="{base_url}/dashboard" style="color: #ff4444; text-decoration: none; font-weight: 600; font-size: 15px;">3. Set up alerts</a>
                                        <p style="margin: 4px 0 0; font-size: 14px; color: rgba(255, 255, 255, 0.6);">Get Telegram alerts for high-impact events so you never miss a move.</p>
                                    </td>
                                </tr>
                            </table>
                            <p style="margin: 0 0 8px; font-size: 15px; line-height: 1.7; color: rgba(255, 255, 255, 0.9);">
                                <strong>P.S.</strong> Why did you sign up? What brought you here?
                            </p>
                            <p style="margin: 0 0 24px; font-size: 15px; line-height: 1.7; color: rgba(255, 255, 255, 0.9);">
                                Hit "Reply" and let me know. I read and reply to every email.
                            </p>
                            <p style="margin: 0; font-size: 16px; color: rgba(255, 255, 255, 0.95);">
                                Cheers,<br />
                                The FXSentinel Team
                            </p>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 24px 40px; border-top: 1px solid rgba(255, 68, 68, 0.15); background: rgba(0, 0, 0, 0.3); border-radius: 0 0 12px 12px;">
                            <p style="margin: 0; font-size: 12px; color: rgba(255, 255, 255, 0.4);">
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
        params = {
            'from': SENDER_EMAIL,
            'to': [to_email],
            'subject': 'Welcome to FXSentinel',
            'html': html,
            'reply_to': REPLY_TO_EMAIL,
        }
        resend_module.Emails.send(params)
        logger.info(f"Welcome email sent to {to_email}")
        return {'success': True}
    except Exception as e:
        logger.exception(f"Failed to send welcome email to {to_email}: {e}")
        return {'success': False, 'error': str(e)}
