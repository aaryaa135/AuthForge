import smtplib
import ssl
from email.message import EmailMessage

from app.core.config import settings
from app.core.logger import logger
from app.providers.base import EmailProvider


class SmtpEmailProvider(EmailProvider):
    """
    SMTP email provider for verification and password-reset emails.
    Always uses STARTTLS when available and enforces connection timeouts.
    """

    def _build_message(
        self,
        email: str,
        link: str,
        subject: str,
        body_template: str,
    ) -> EmailMessage:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
        msg["To"] = email
        msg.set_content(body_template.format(link=link))
        return msg

    def send_verification_email(
        self,
        email: str,
        verification_link: str,
    ) -> None:
        if not settings.smtp_host or not settings.smtp_from_email:
            logger.warning(
                "SMTP not configured; skipping verification email to %s",
                email,
            )
            return

        msg = self._build_message(
            email,
            verification_link,
            "Verify your email",
            "Click the link to verify your email: {link}",
        )
        self._send(msg)

    def send_password_reset_email(
        self,
        email: str,
        reset_link: str,
    ) -> None:
        if not settings.smtp_host or not settings.smtp_from_email:
            logger.warning(
                "SMTP not configured; skipping password reset email to %s",
                email,
            )
            return

        msg = self._build_message(
            email,
            reset_link,
            "Reset your password",
            "Click the link to reset your password: {link}",
        )
        self._send(msg)

    def _send(self, msg: EmailMessage) -> None:
        context = ssl.create_default_context()
        with smtplib.SMTP(
            settings.smtp_host,
            settings.smtp_port or 587,
            timeout=10,
        ) as server:
            server.starttls(context=context)
            if settings.smtp_user and settings.smtp_password:
                server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)
