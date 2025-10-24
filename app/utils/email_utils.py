import os
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content

def send_verification_email(to_email, token, user_name=None):
    """
    Sends a verification email with a clickable link
    """
    sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
    from_email = Email("no-reply@projectx.com")
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
    sg.send(mail)

def send_invitation_email(to_email, project_name, inviter_name=None):
    """
    Sends a project invitation email
    """
    sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
    from_email = Email("no-reply@projectx.com")
    subject = f"Invitation to join project: {project_name}"

    content = Content(
        "text/html",
        f"""
        <p>Hello,</p>
        <p>{inviter_name or 'Someone'} has invited you to join the project '{project_name}'.</p>
        <p>Please respond via the app to accept or decline the invitation.</p>
        """
    )

    mail = Mail(from_email, To(to_email), subject, content)
    sg.send(mail)