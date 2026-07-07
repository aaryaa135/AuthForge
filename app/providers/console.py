from app.providers.base import EmailProvider


class ConsoleEmailProvider(EmailProvider):
    """
    Development email provider.
    Prints links to the console.
    """

    def send_verification_email(
        self,
        email: str,
        verification_link: str,
    ) -> None:
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
        print("\n" + "=" * 60)
        print("PASSWORD RESET")
        print(f"To: {email}")
        print(reset_link)
        print("=" * 60 + "\n")
