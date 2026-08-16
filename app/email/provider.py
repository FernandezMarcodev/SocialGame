"""Proveedores de envío de correo (AD-005)."""

import smtplib
from email.message import EmailMessage
from typing import Protocol


class EmailProvider(Protocol):
    def send(self, to_email: str, subject: str, body: str) -> None: ...


class ConsoleEmailProvider:
    """Proveedor de desarrollo (AD-005) que imprime y guarda los correos.

    La bandeja enviada queda disponible para inspección en tests.
    """

    def __init__(self, outbox: list[tuple[str, str, str]] | None = None) -> None:
        self._outbox = outbox if outbox is not None else []

    @property
    def outbox(self) -> list[tuple[str, str, str]]:
        return self._outbox

    def send(self, to_email: str, subject: str, body: str) -> None:
        self._outbox.append((to_email, subject, body))
        print(f"[email] para={to_email}")
        print(f"  asunto: {subject}")
        print(body)


class SmtpEmailProvider:
    """Proveedor de producción que envía el correo por SMTP (AD-005)."""

    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        frm: str,
        use_tls: bool = True,
    ) -> None:
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._from = frm
        self._use_tls = use_tls

    def send(self, to_email: str, subject: str, body: str) -> None:
        message = EmailMessage()
        message["From"] = self._from
        message["To"] = to_email
        message["Subject"] = subject
        message.set_content(body)

        if self._use_tls:
            with smtplib.SMTP(self._host, self._port) as server:
                server.starttls()
                if self._user:
                    server.login(self._user, self._password)
                server.send_message(message)
        else:
            with smtplib.SMTP_SSL(self._host, self._port) as server:
                if self._user:
                    server.login(self._user, self._password)
                server.send_message(message)