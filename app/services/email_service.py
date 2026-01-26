"""Email service for sending emails via SMTP"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails using SMTP"""
    
    def __init__(self):
        """Initialize SMTP configuration"""
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_username = settings.smtp_username
        self.smtp_password = settings.smtp_password
        self.sender_email = settings.smtp_sender_email
        self.sender_name = settings.smtp_sender_name
    
    def _get_otp_email_template(self, otp_code: str, username: str = "User") -> str:
        """Generate HTML email template for OTP"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f9f9f9;
                }}
                .header {{
                    background-color: #4CAF50;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 5px 5px 0 0;
                }}
                .content {{
                    background-color: white;
                    padding: 30px;
                    border-radius: 0 0 5px 5px;
                }}
                .otp-code {{
                    font-size: 32px;
                    font-weight: bold;
                    color: #4CAF50;
                    text-align: center;
                    padding: 20px;
                    background-color: #f0f0f0;
                    border-radius: 5px;
                    letter-spacing: 5px;
                    margin: 20px 0;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 20px;
                    color: #777;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Kidic AI Authentication</h1>
                </div>
                <div class="content">
                    <p>Hello {username},</p>
                    <p>Thank you for using Kidic AI! Your One-Time Password (OTP) for authentication is:</p>
                    <div class="otp-code">{otp_code}</div>
                    <p>This OTP will expire in {settings.otp_expire_minutes} minutes.</p>
                    <p>If you didn't request this code, please ignore this email.</p>
                    <p>Best regards,<br>Kidic AI Team</p>
                </div>
                <div class="footer">
                    <p>This is an automated email. Please do not reply.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def send_otp_email(
        self, 
        recipient_email: str, 
        otp_code: str,
        username: str = "User"
    ) -> bool:
        """
        Send OTP email to recipient via SMTP
        
        Args:
            recipient_email: Email address to send to
            otp_code: OTP code to include in email
            username: Username for personalization
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Create message container
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f'Your Kidic AI OTP: {otp_code}'
            msg['From'] = f"{self.sender_name} <{self.sender_email}>"
            msg['To'] = recipient_email
            
            # Create plain text and HTML versions
            text_body = f'Your Kidic AI OTP is: {otp_code}. This code will expire in {settings.otp_expire_minutes} minutes.'
            html_body = self._get_otp_email_template(otp_code, username)
            
            # Attach parts to message
            part1 = MIMEText(text_body, 'plain')
            part2 = MIMEText(html_body, 'html')
            msg.attach(part1)
            msg.attach(part2)
            
            # Send email via SMTP
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()  # Enable TLS encryption
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"OTP email sent successfully to {recipient_email} via SMTP")
            return True
            
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error sending OTP email to {recipient_email}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending OTP email to {recipient_email}: {str(e)}")
            return False


# Global email service instance
email_service = EmailService()
