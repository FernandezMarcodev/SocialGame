"""Errores de API con formato estándar (Apéndice B.5 del DDD)."""

from typing import Any

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ApiError(Exception):
    """Error de negocio con código máquina estable y HTTP status."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or {}


def _error_body(code: str, message: str, details: dict[str, Any]) -> dict[str, Any]:
    return {"error": {"code": code, "message": message, "details": details}}


def _validation_field(error: dict[str, Any]) -> str:
    loc = error.get("loc", ())
    for part in reversed(loc):
        if isinstance(part, str) and part not in ("body", "query", "path", "header"):
            return part
    return "body"


async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body(exc.code, exc.message, exc.details),
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    details: dict[str, Any] = {}
    for error in exc.errors():
        field = _validation_field(error)
        details[field] = error.get("msg", "valor inválido")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=_error_body("VALIDATION_ERROR", "Los datos enviados no son válidos.", details),
    )


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_error_body("INTERNAL_ERROR", "Error interno del servidor.", {}),
    )