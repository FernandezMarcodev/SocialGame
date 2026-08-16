"""Proveedores de envío de correo (AD-005)."""

import base64
import json
import smtplib
import urllib.error
import urllib.parse
import urllib.request
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
            with smtplib.SMTP(self._host, self._port, timeout=15) as server:
                server.starttls()
                if self._user:
                    server.login(self._user, self._password)
                server.send_message(message)
        else:
            with smtplib.SMTP_SSL(self._host, self._port, timeout=15) as server:
                if self._user:
                    server.login(self._user, self._password)
                server.send_message(message)


class GmailApiEmailProvider:
    """Proveedor que envía por la Gmail API (HTTPS 443).

    Render bloquea la salida SMTP, pero sí permite tráfico HTTPS. Usamos
    OAuth2 (refresh token) para enviar como la cuenta configurada, sin
    dominio propio ni App Password.
    """

    TOKEN_URL = "https://oauth2.googleapis.com/token"
    SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"

    def __init__(
        self, client_id: str, client_secret: str, refresh_token: str, frm: str
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._refresh_token = refresh_token
        self._from = frm

    def _access_token(self) -> str:
        body = urllib.parse.urlencode(
            {
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "refresh_token": self._refresh_token,
                "grant_type": "refresh_token",
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            self.TOKEN_URL,
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))["access_token"]

    def send(self, to_email: str, subject: str, body: str) -> None:
        message = (
            f"From: {self._from}\r\n"
            f"To: {to_email}\r\n"
            f"Subject: {subject}\r\n\r\n"
            f"{body}"
        )
        raw = base64.urlsafe_b64encode(message.encode("utf-8")).decode("utf-8")
        payload = json.dumps({"raw": raw}).encode("utf-8")
        access_token = self._access_token()
        request = urllib.request.Request(
            self.SEND_URL,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                response.read()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")
            raise RuntimeError(f"Gmail API error {exc.code}: {detail}") from exc