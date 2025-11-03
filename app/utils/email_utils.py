import os
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content
import logging

logger = logging.getLogger(_name_)

def send_verification_email(to_email, token, user_name=None):
    """
    Sends a verification email with a clickable link
    """
    try:
        api_key = os.environ.get('SENDGRID_API_KEY')
        if not api_key:
            logger.error("SENDGRID_API_KEY not found in environment variables")
            raise ValueError("SendGrid API key not configured")

        if len(api_key) < 50 or not api_key.startswith('SG.'):
            logger.error(f"Invalid SendGrid API key format (length: {len(api_key)})")
            raise ValueError("SendGrid API key appears to be invalid. Valid keys start with 'SG.' and are 69+ characters long")

        sg = sendgrid.SendGridAPIClient(api_key=api_key)
        # Use configured sender email from environment
        sender_email = os.environ.get('SENDGRID_SENDER_EMAIL', 'no-reply@projectx.com')
        from_email = Email(sender_email)
        subject = "Verify your email"

        # Use frontend URL from environment or fallback to localhost
        frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:3000")
        verification_link = f"{frontend_url}/verify-email?token={token}"

        content = Content(
            "text/html",
            f"""
            <p>Hello {user_name or 'User'},</p>
            <p>Thank you for registering. Please verify your email by clicking the link below:</p>
            <p><a href="{verification_link}">Verify Email</a></p>
            <p>This link will expire in 24 hours.</p>
            """
        )

        mail = Mail(from_email, To(to_email), subject, content)
        response = sg.send(mail)
        logger.info(f"Verification email sent successfully to {to_email}. Status: {response.status_code}")
        return True
    except Exception as e:
        logger.error(f"Failed to send verification email to {to_email}: {str(e)}")
        raise

def send_invitation_email(to_email, project_name, inviter_name=None, project_id=None, user_id=None):
    """
    Sends a project invitation email notifying user to log in
    """
    try:
        api_key = os.environ.get('SENDGRID_API_KEY')
        if not api_key:
            logger.error("SENDGRID_API_KEY not found in environment variables")
            raise ValueError("SendGrid API key not configured")

        if len(api_key) < 50 or not api_key.startswith('SG.'):
            logger.error(f"Invalid SendGrid API key format (length: {len(api_key)})")
            raise ValueError("SendGrid API key appears to be invalid. Valid keys start with 'SG.' and are 69+ characters long")

        sg = sendgrid.SendGridAPIClient(api_key=api_key)
        # Use configured sender email from environment
        sender_email = os.environ.get('SENDGRID_SENDER_EMAIL', 'no-reply@projectx.com')
        frontend_url = os.environ.get('FRONTEND_URL', 'http://127.0.0.1:5173')
        from_email = Email(sender_email)
        subject = f"Invitation to join project: {project_name}"

        # Create styled HTML email prompting user to log in
        content = Content(
            "text/html",
            f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #4F46E5; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                    .content {{ background-color: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }}
                    .project-name {{ font-size: 20px; font-weight: bold; color: #4F46E5; margin: 15px 0; }}
                    .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #6B7280; }}
                    .highlight {{ background-color: #FEF3C7; padding: 15px; border-left: 4px solid #F59E0B; margin: 20px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎉 Project Invitation</h1>
                    </div>
                    <div class="content">
                        <p>Hello,</p>
                        <p><strong>{inviter_name or 'Someone'}</strong> has invited you to collaborate on the project:</p>
                        <div class="project-name">📋 {project_name}</div>
                        <div class="highlight">
                            <p style="margin: 0; font-weight: bold;">You have a pending invitation waiting for you!</p>
                        </div>
                        <p>To accept or decline this invitation:</p>
                        <ol style="line-height: 2;">
                            <li>Log in to your Moringa Project Planner account</li>
                            <li>Click the notification bell icon in the dashboard header</li>
                            <li>Click Accept or Decline on your invitation</li>
                        </ol>
                    </div>
                    <div class="footer">
                        <p>This is an automated email from Moringa Project Planner. Please do not reply to this email.</p>
                    </div>
                </div>
            </body>
            </html>
            """
        )

        mail = Mail(from_email, To(to_email), subject, content)
        response = sg.send(mail)
        logger.info(f"Invitation email sent successfully to {to_email} for project '{project_name}'. Status: {response.status_code}")
        return True
    except Exception as e:
        logger.error(f"Failed to send invitation email to {to_email} for project '{project_name}': {str(e)}")
        raise

def send_2fa_code_email(to_email, code, user_name=None):
    """
    Sends a 2FA verification code email
    """
    try:
        api_key = os.environ.get('SENDGRID_API_KEY')
        if not api_key:
            logger.error("SENDGRID_API_KEY not found in environment variables")
            raise ValueError("SendGrid API key not configured")

        if len(api_key) < 50 or not api_key.startswith('SG.'):
            logger.error(f"Invalid SendGrid API key format (length: {len(api_key)})")
            raise ValueError("SendGrid API key appears to be invalid. Valid keys start with 'SG.' and are 69+ characters long")

        sg = sendgrid.SendGridAPIClient(api_key=api_key)
        sender_email = os.environ.get('SENDGRID_SENDER_EMAIL', 'no-reply@projectx.com')
        from_email = Email(sender_email)
        subject = "Your 2FA Verification Code"

        content = Content(
            "text/html",
            f"""
            <p>Hello {user_name or 'User'},</p>
            <p>Your 2FA verification code is:</p>
            <h2 style="font-size: 32px; letter-spacing: 5px; text-align: center; color: #4F46E5;">{code}</h2>
            <p>This code will expire in 10 minutes.</p>
            <p>If you didn't request this code, please ignore this email.</p>
            """
        )

        mail = Mail(from_email, To(to_email), subject, content)
        response = sg.send(mail)
        logger.info(f"2FA code email sent successfully to {to_email}. Status: {response.status_code}")
        return True
    except Exception as e:
        logger.error(f"Failed to send 2FA code email to {to_email}: {str(e)}")
        raise