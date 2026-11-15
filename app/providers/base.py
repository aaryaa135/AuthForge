from abc import ABC, abstractmethod


class EmailProvider(ABC):
    """
    Base interface for email providers.
    """

    @abstractmethod
    def send_verification_email(
        self,
        email: str,
        verification_link: str,
    ) -> None:
        ...

    @abstractmethod
    def send_password_reset_email(
        self,
        email: str,
        reset_link: str,
    ) -> None:
        ...
