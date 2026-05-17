import functools
import uuid
from collections.abc import Callable
from typing import Any, TypeVar
from typing import cast

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog

F = TypeVar("F", bound=Callable[..., Any])


def auditar(accion: str, entidad: str) -> Callable[[F], F]:
    """
    Async decorator that writes an audit_log entry after the decorated function.
    The decorated function must receive `session` as a kwarg and optionally
    `entidad_id`, `payload_antes`, `payload_despues`, `usuario_id`.
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = await func(*args, **kwargs)

            session: AsyncSession | None = kwargs.get("session")
            if session is None:
                return result

            entidad_id: uuid.UUID | None = kwargs.get("entidad_id")
            payload_antes: dict[str, Any] | None = kwargs.get("payload_antes")
            payload_despues: dict[str, Any] | None = kwargs.get("payload_despues")
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
