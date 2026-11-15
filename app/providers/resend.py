from app.core.config import settings
from app.core.logger import logger
from app.providers.base import EmailProvider


class ResendEmailProvider(EmailProvider):
    """
    Resend email provider for verification and password-reset emails.
    """

    def _client(self):
        try:
            import resend
        except ImportError as exc:  # pragma: no cover - optional dependency
            logger.error("resend package not installed")
            raise exc

        resend.api_key = settings.resend_api_key
        return resend

    def send_verification_email(
        self,
        email: str,
        verification_link: str,
    ) -> None:
        if not settings.resend_api_key or not settings.resend_from_email:
            logger.warning(
                "Resend not configured; skipping verification email to %s",
                email,
            )
            return

        resend = self._client()
        resend.Emails.send(
            {
                "from": settings.resend_from_email,
                "to": [email],
                "subject": "Verify your email",
                "text": f"Click the link to verify your email: {verification_link}",
            }
        )

    def send_password_reset_email(
        self,
        email: str,
        reset_link: str,
    ) -> None:
        if not settings.resend_api_key or not settings.resend_from_email:
            logger.warning(
                "Resend not configured; skipping password reset email to %s",
                email,
            )
            return

        resend = self._client()
        resend.Emails.send(
            {
                "from": settings.resend_from_email,
                "to": [email],
                "subject": "Reset your password",
                "text": f"Click the link to reset your password: {reset_link}",
            }
        )
