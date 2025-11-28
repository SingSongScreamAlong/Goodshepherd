"""Email service for authentication-related emails."""

import os
import logging
from typing import Optional
from dataclasses import dataclass

import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


@dataclass
class AuthEmailConfig:
    """Configuration for authentication email service."""
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    from_email: str
    from_name: str
    frontend_url: str
    use_tls: bool = True

    @classmethod
    def from_env(cls) -> "AuthEmailConfig":
        """Create config from environment variables."""
        return cls(
            smtp_host=os.getenv("SMTP_HOST", "localhost"),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            smtp_user=os.getenv("SMTP_USER", ""),
            smtp_password=os.getenv("SMTP_PASSWORD", ""),
            from_email=os.getenv("SMTP_FROM_EMAIL", "noreply@goodshepherd.app"),
            from_name=os.getenv("SMTP_FROM_NAME", "Good Shepherd"),
            frontend_url=os.getenv("FRONTEND_URL", "http://localhost:3000"),
            use_tls=os.getenv("SMTP_USE_TLS", "true").lower() == "true",
        )


class AuthEmailService:
    """Service for sending authentication-related emails."""

    def __init__(self, config: Optional[AuthEmailConfig] = None):
        self.config = config or AuthEmailConfig.from_env()
        self._enabled = bool(self.config.smtp_user and self.config.smtp_password)

    @property
    def is_enabled(self) -> bool:
        """Check if email service is properly configured."""
        return self._enabled

    async def _send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str,
    ) -> bool:
        """Send an email."""
        if not self._enabled:
            logger.warning("Email service not configured, skipping email send")
            return False

        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.config.from_name} <{self.config.from_email}>"
            message["To"] = to_email

            # Add plain text and HTML parts
            message.attach(MIMEText(text_content, "plain"))
            message.attach(MIMEText(html_content, "html"))

            await aiosmtplib.send(
                message,
                hostname=self.config.smtp_host,
                port=self.config.smtp_port,
                username=self.config.smtp_user,
                password=self.config.smtp_password,
                use_tls=self.config.use_tls,
            )

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    async def send_password_reset_email(
        self,
        to_email: str,
        reset_token: str,
        user_name: Optional[str] = None,
    ) -> bool:
        """Send password reset email."""
        reset_url = f"{self.config.frontend_url}/reset-password?token={reset_token}"
        greeting = f"Hi {user_name}," if user_name else "Hi,"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .button {{ 
                    display: inline-block; 
                    padding: 12px 24px; 
                    background-color: #4F46E5; 
                    color: white; 
                    text-decoration: none; 
                    border-radius: 6px;
                    margin: 20px 0;
                }}
                .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Password Reset Request</h2>
                <p>{greeting}</p>
                <p>We received a request to reset your password for your Good Shepherd account.</p>
                <p>Click the button below to reset your password:</p>
                <a href="{reset_url}" class="button">Reset Password</a>
                <p>Or copy and paste this link into your browser:</p>
                <p><a href="{reset_url}">{reset_url}</a></p>
                <p>This link will expire in 24 hours.</p>
                <p>If you didn't request a password reset, you can safely ignore this email.</p>
                <div class="footer">
                    <p>This email was sent by Good Shepherd. Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"""
{greeting}

We received a request to reset your password for your Good Shepherd account.

Click the link below to reset your password:
{reset_url}

This link will expire in 24 hours.

If you didn't request a password reset, you can safely ignore this email.

---
This email was sent by Good Shepherd. Please do not reply to this email.
        """

        return await self._send_email(
            to_email=to_email,
            subject="Reset Your Password - Good Shepherd",
            html_content=html_content,
            text_content=text_content,
        )

    async def send_verification_email(
        self,
        to_email: str,
        verification_token: str,
        user_name: Optional[str] = None,
    ) -> bool:
        """Send email verification email."""
        verify_url = f"{self.config.frontend_url}/verify-email?token={verification_token}"
        greeting = f"Hi {user_name}," if user_name else "Hi,"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .button {{ 
                    display: inline-block; 
                    padding: 12px 24px; 
                    background-color: #10B981; 
                    color: white; 
                    text-decoration: none; 
                    border-radius: 6px;
                    margin: 20px 0;
                }}
                .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Verify Your Email Address</h2>
                <p>{greeting}</p>
                <p>Welcome to Good Shepherd! Please verify your email address to complete your registration.</p>
                <a href="{verify_url}" class="button">Verify Email</a>
                <p>Or copy and paste this link into your browser:</p>
                <p><a href="{verify_url}">{verify_url}</a></p>
                <p>This link will expire in 48 hours.</p>
                <div class="footer">
                    <p>This email was sent by Good Shepherd. Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"""
{greeting}

Welcome to Good Shepherd! Please verify your email address to complete your registration.

Click the link below to verify your email:
{verify_url}

This link will expire in 48 hours.

---
This email was sent by Good Shepherd. Please do not reply to this email.
        """

        return await self._send_email(
            to_email=to_email,
            subject="Verify Your Email - Good Shepherd",
            html_content=html_content,
            text_content=text_content,
        )

    async def send_welcome_email(
        self,
        to_email: str,
        user_name: Optional[str] = None,
    ) -> bool:
        """Send welcome email after successful registration."""
        greeting = f"Hi {user_name}," if user_name else "Hi,"
        login_url = f"{self.config.frontend_url}/login"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .button {{ 
                    display: inline-block; 
                    padding: 12px 24px; 
                    background-color: #4F46E5; 
                    color: white; 
                    text-decoration: none; 
                    border-radius: 6px;
                    margin: 20px 0;
                }}
                .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Welcome to Good Shepherd!</h2>
                <p>{greeting}</p>
                <p>Thank you for joining Good Shepherd. Your account has been successfully created.</p>
                <p>You can now access all features of the platform:</p>
                <ul>
                    <li>Real-time situational awareness</li>
                    <li>Geofencing and location tracking</li>
                    <li>Automated alerts and notifications</li>
                    <li>Intelligence reports and digests</li>
                </ul>
                <a href="{login_url}" class="button">Go to Dashboard</a>
                <div class="footer">
                    <p>This email was sent by Good Shepherd. Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"""
{greeting}

Thank you for joining Good Shepherd. Your account has been successfully created.

You can now access all features of the platform:
- Real-time situational awareness
- Geofencing and location tracking
- Automated alerts and notifications
- Intelligence reports and digests

Go to your dashboard: {login_url}

---
This email was sent by Good Shepherd. Please do not reply to this email.
        """

        return await self._send_email(
            to_email=to_email,
            subject="Welcome to Good Shepherd!",
            html_content=html_content,
            text_content=text_content,
        )


# Global instance
auth_email_service = AuthEmailService()
