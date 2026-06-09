import smtplib
from email.message import EmailMessage

from app.core.config import settings


def send_password_reset_email(email: str, otp: str) -> None:
    if not settings.smtp_host:
        raise ValueError("SMTP host is not configured")

    message = EmailMessage()
    message["Subject"] = "Your password reset OTP"
    message["From"] = settings.email_from
    message["To"] = email
    message.set_content(
        f"Your password reset OTP is:\n\n"
        f"{otp}\n\n"
        "Valid for 10 minutes.\n\n"
        "If you did not request this, please ignore this email.\n"
    )

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
        if settings.smtp_starttls:
            smtp.starttls()
        if settings.smtp_user and settings.smtp_password:
            smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(message)
