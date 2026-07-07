from app.providers.console import ConsoleEmailProvider


def get_email_provider():
    """
    Return the configured email provider.

    Future:
    - Resend
    - SMTP
    - SendGrid
    """
    return ConsoleEmailProvider()
