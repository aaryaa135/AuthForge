from app.providers.console import ConsoleEmailProvider
from app.providers.factory import get_email_provider
from app.providers.resend import ResendEmailProvider
from app.providers.smtp import SmtpEmailProvider


def test_get_email_provider_default_returns_console():
    provider = get_email_provider()
    assert isinstance(provider, ConsoleEmailProvider)


def test_smtp_provider_has_send_methods():
    provider = SmtpEmailProvider()
    assert hasattr(provider, "send_verification_email")
    assert hasattr(provider, "send_password_reset_email")


def test_resend_provider_has_send_methods():
    provider = ResendEmailProvider()
    assert hasattr(provider, "send_verification_email")
    assert hasattr(provider, "send_password_reset_email")


def test_console_provider_has_send_methods():
    provider = ConsoleEmailProvider()
    assert hasattr(provider, "send_verification_email")
    assert hasattr(provider, "send_password_reset_email")
