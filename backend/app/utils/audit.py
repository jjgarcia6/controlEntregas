import functools
import uuid
from collections.abc import Callable
from contextvars import ContextVar
from datetime import date, datetime
from decimal import Decimal
from typing import Any, TypeVar
from typing import cast

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog

F = TypeVar("F", bound=Callable[..., Any])

_audit_ctx: ContextVar[dict[str, Any]] = ContextVar("_audit_ctx", default={})


def set_audit_payload(
    *,
    payload_antes: dict[str, Any] | None = None,
    payload_despues: dict[str, Any] | None = None,
) -> None:
    """Call from inside an @auditar-decorated service to record before/after state."""
    ctx = dict(_audit_ctx.get({}))
    if payload_antes is not None:
        ctx["payload_antes"] = payload_antes
    if payload_despues is not None:
        ctx["payload_despues"] = payload_despues
    _audit_ctx.set(ctx)


def _json_safe(val: Any) -> Any:
    """Convert types that are not JSON-serialisable to safe equivalents."""
    if isinstance(val, Decimal):
        return str(val)
    if isinstance(val, uuid.UUID):
        return str(val)
    if isinstance(val, datetime):
        return val.isoformat()
    if isinstance(val, date):
        return val.isoformat()
    return val


def safe_dict(**kwargs: Any) -> dict[str, Any]:
    """Build a payload dict, skipping None values and serialising special types."""
    return {k: _json_safe(v) for k, v in kwargs.items() if v is not None}


def auditar(accion: str, entidad: str) -> Callable[[F], F]:
    """
    Async decorator that writes an audit_log entry after the decorated function.
    The decorated function must receive `session` as a kwarg and optionally
    `entidad_id`, `usuario_id` as kwargs.
    Services should call `set_audit_payload()` to supply before/after state.
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            token = _audit_ctx.set({})
            try:
                result = await func(*args, **kwargs)
            except Exception:
                _audit_ctx.reset(token)
                raise

            ctx = _audit_ctx.get({})
            _audit_ctx.reset(token)

            payload_antes: dict[str, Any] | None = ctx.get(
                "payload_antes"
            ) or kwargs.get("payload_antes")
            payload_despues: dict[str, Any] | None = ctx.get(
                "payload_despues"
            ) or kwargs.get("payload_despues")

            session: AsyncSession | None = kwargs.get("session")
            if session is None:
                return result

            entidad_id: uuid.UUID | None = kwargs.get("entidad_id")
            usuario_id: uuid.UUID | None = kwargs.get("usuario_id")

            log = AuditLog(
                accion=accion,
                entidad=entidad,
                entidad_id=entidad_id,
                payload_antes=payload_antes,
                payload_despues=payload_despues,
                usuario_id=usuario_id,
            )
            session.add(log)

            return result

        return cast(F, wrapper)

    return decorator
