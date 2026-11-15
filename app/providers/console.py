from app.core.config import settings
from app.core.logger import logger
from app.providers.base import EmailProvider


class ConsoleEmailProvider(EmailProvider):
    """
    Development email provider.
    Prints links to the console. Not for production use.
    """

    def send_verification_email(
        self,
        email: str,
        verification_link: str,
    ) -> None:
        if settings.environment == "production":
            logger.error(
                "Console email provider used in production; verification link not sent to %s",
                email,
            )
            return
        print("\n" + "=" * 60)
        print("EMAIL VERIFICATION")
        print(f"To: {email}")
        print(verification_link)
        print("=" * 60 + "\n")

    def send_password_reset_email(
        self,
        email: str,
        reset_link: str,
    ) -> None:
        if settings.environment == "production":
            logger.error(
                "Console email provider used in production; reset link not sent to %s",
                email,
            )
            return
        print("\n" + "=" * 60)
        print("PASSWORD RESET")
        print(f"To: {email}")
        print(reset_link)
        print("=" * 60 + "\n")
