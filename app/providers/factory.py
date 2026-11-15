from app.core.config import settings
from app.providers.console import ConsoleEmailProvider
from app.providers.resend import ResendEmailProvider
from app.providers.smtp import SmtpEmailProvider


def get_email_provider():
    """
    Return the configured email provider.

    Options:
    - console (default): prints emails to stdout, for dev/test
    - smtp: sends via SMTP
    - resend: sends via Resend API
    """
    provider = settings.email_provider.lower()

    if provider == "smtp":
        return SmtpEmailProvider()

    if provider == "resend":
        return ResendEmailProvider()

    return ConsoleEmailProvider()
