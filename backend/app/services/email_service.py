"""
app/services/email_service.py

Email service for sending transactional emails using aiosmtplib.
"""

import aiosmtplib
from email.message import EmailMessage
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from typing import Optional, Dict, Any

from app.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.enabled = bool(settings.SMTP_HOST and settings.SMTP_USER)
        self.from_email = settings.EMAILS_FROM_EMAIL or "noreply@jobt.ai"

    async def _send(self, to_email: str, subject: str, body: str, html_body: str = None):
        """
        Internal method to send email.
        """
        if not self.enabled:
            logger.info(f"✉️ [MOCK EMAIL] To: {to_email} | Subject: {subject}")
            logger.debug(f"Body: {body}")
            return True

        message = MIMEMultipart("alternative")
        message["From"] = self.from_email
        message["To"] = to_email
        message["Subject"] = subject

        # Plain text
        message.attach(MIMEText(body, "plain"))

        # HTML
        if html_body:
            message.attach(MIMEText(html_body, "html"))

        try:
            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                use_tls=True if settings.SMTP_PORT == 465 else False,
                start_tls=True if settings.SMTP_PORT == 587 else False,
                timeout=30  # Increase timeout for Render/Cloud environments
            )
            logger.info(f"✓ Email sent to {to_email}: {subject}")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to send email to {to_email}: {e}")
            return False

    async def send_welcome_email(self, user_email: str, user_name: str = "User"):
        """
        Send welcome email to new user.
        """
        subject = "Welcome to Jobt AI Career Coach!"
        
        body = f"""
        Hi {user_name},

        Welcome to Jobt AI! We're excited to help you ace your next interview.

        With Jobt AI, you can:
        - Practice realistic AI interviews
        - Get instant, actionable feedback
        - Track your progress over time

        Log in now to start your first session: http://localhost:3000

        Best regards,
        The Jobt AI Team
        """
        
        html_body = f"""
        <html>
            <body>
                <h2>Welcome to Jobt AI, {user_name}!</h2>
                <p>We're excited to help you ace your next interview.</p>
                <ul>
                    <li>🚀 Practice realistic AI interviews</li>
                    <li>📊 Get instant, actionable feedback</li>
                    <li>📈 Track your progress over time</li>
                </ul>
                <p>
                    <a href="http://localhost:3000">Log in to start your first session</a>
                </p>
                <br>
                <p>Best regards,<br>The Jobt AI Team</p>
            </body>
        </html>
        """
        
        await self._send(user_email, subject, body, html_body)

    async def send_password_reset_email(self, user_email: str, token: str):
        """
        Send password reset email with token.
        """
        # In a real app, this would be a link to the frontend
        reset_link = f"http://localhost:3000/reset-password?token={token}"
        
        subject = "Reset Your Password - Jobt AI"
        
        body = f"""
        We received a request to reset your password.
        
        Click the link below to verify your email and set a new password:
        {reset_link}
        
        This link expires in 1 hour.
        
        If you didn't request this, please ignore this email.
        """
        
        html_body = f"""
        <html>
            <body>
                <h2>Password Reset Request</h2>
                <p>We received a request to reset your associated password.</p>
                <p>
                    <a href="{reset_link}" style="background-color: #4F46E5; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Reset Password</a>
                </p>
                <p>Or paste this link in your browser: {reset_link}</p>
                <p><em>This link expires in 1 hour.</em></p>
            </body>
        </html>
        """

        await self._send(user_email, subject, body, html_body)
