"""Proveedores de envío de correo (AD-005)."""

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
        print(f"[email] para={to_email} asunto={subject}")