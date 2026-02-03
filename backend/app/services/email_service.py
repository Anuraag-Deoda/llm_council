"""
Email service for sending authentication emails via Gmail SMTP
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SMTP"""

    def __init__(self):
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_username = settings.smtp_username
        self.smtp_password = settings.smtp_password
        self.from_email = settings.smtp_from_email or settings.smtp_username
        self.frontend_url = settings.frontend_url

    def _create_smtp_connection(self) -> smtplib.SMTP:
        """Create and authenticate SMTP connection"""
        server = smtplib.SMTP(self.smtp_host, self.smtp_port)
        server.starttls()
        if self.smtp_username and self.smtp_password:
            server.login(self.smtp_username, self.smtp_password)
        return server

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """Send an email"""
        if not self.smtp_username or not self.smtp_password:
            logger.warning("SMTP credentials not configured, skipping email send")
            logger.info(f"Would send email to {to_email}: {subject}")
            return True  # Return True to allow flow to continue in development

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_email
            msg["To"] = to_email

            # Add plain text version
            if text_content:
                part1 = MIMEText(text_content, "plain")
                msg.attach(part1)

            # Add HTML version
            part2 = MIMEText(html_content, "html")
            msg.attach(part2)

            # Send email
            with self._create_smtp_connection() as server:
                server.sendmail(self.from_email, to_email, msg.as_string())

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    def send_magic_link(self, to_email: str, token: str, is_login: bool = True) -> bool:
        """Send a magic link email for login or verification"""
        action = "sign in" if is_login else "verify your email"
        link = f"{self.frontend_url}/verify/{token}"

        subject = f"LLM Council - {'Sign In' if is_login else 'Verify Email'}"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 24px;">LLM Council</h1>
            </div>
            <div style="background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #e5e7eb; border-top: none;">
                <h2 style="margin-top: 0; color: #1f2937;">Click to {action}</h2>
                <p style="color: #6b7280;">
                    Click the button below to {action} to LLM Council. This link will expire in {settings.magic_link_expire_minutes} minutes.
                </p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{link}" style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 14px 30px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
                        {'Sign In' if is_login else 'Verify Email'}
                    </a>
                </div>
                <p style="color: #9ca3af; font-size: 14px;">
                    If you didn't request this email, you can safely ignore it.
                </p>
                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
                <p style="color: #9ca3af; font-size: 12px; margin-bottom: 0;">
                    Or copy and paste this link into your browser:<br>
                    <a href="{link}" style="color: #667eea; word-break: break-all;">{link}</a>
                </p>
            </div>
        </body>
        </html>
        """

        text_content = f"""
        LLM Council - {'Sign In' if is_login else 'Verify Email'}

        Click the link below to {action}:
        {link}

        This link will expire in {settings.magic_link_expire_minutes} minutes.

        If you didn't request this email, you can safely ignore it.
        """

        return self.send_email(to_email, subject, html_content, text_content)

    def send_welcome_email(self, to_email: str, display_name: Optional[str] = None) -> bool:
        """Send a welcome email to new users"""
        name = display_name or "there"

        subject = "Welcome to LLM Council"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 24px;">Welcome to LLM Council</h1>
            </div>
            <div style="background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #e5e7eb; border-top: none;">
                <h2 style="margin-top: 0; color: #1f2937;">Hi {name}!</h2>
                <p style="color: #6b7280;">
                    Thanks for joining LLM Council. You now have access to collective intelligence from multiple AI models.
                </p>
                <h3 style="color: #1f2937;">What you can do:</h3>
                <ul style="color: #6b7280;">
                    <li>Chat with multiple AI models simultaneously</li>
                    <li>See how different models approach your questions</li>
                    <li>Get consensus responses from the council</li>
                    <li>Access your knowledge base with RAG</li>
                </ul>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{self.frontend_url}/dashboard" style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 14px 30px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
                        Go to Dashboard
                    </a>
                </div>
                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
                <p style="color: #9ca3af; font-size: 12px; margin-bottom: 0;">
                    Questions? Just reply to this email.
                </p>
            </div>
        </body>
        </html>
        """

        text_content = f"""
        Welcome to LLM Council

        Hi {name}!

        Thanks for joining LLM Council. You now have access to collective intelligence from multiple AI models.

        What you can do:
        - Chat with multiple AI models simultaneously
        - See how different models approach your questions
        - Get consensus responses from the council
        - Access your knowledge base with RAG

        Get started: {self.frontend_url}/dashboard
        """

        return self.send_email(to_email, subject, html_content, text_content)


# Singleton instance
email_service = EmailService()
