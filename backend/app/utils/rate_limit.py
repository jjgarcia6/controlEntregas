"""Rate limiter respaldado por PostgreSQL con compatibilidad sync/async.

Este módulo expone dos instancias reutilizadas por las pruebas y la app:
- `ip_login_limiter` — para IPs de login.
- `email_failure_tracker` — para emails con fallos de autenticación.

API compatible:
- Sin sesión (sync): `check_and_record(key)`, `reset(key)`, `clear_all()` — usan contador en memoria (útil en tests rápidos).
- Con sesión (async): `await check_and_record(session, key)`, `await reset(session, key)`, `await clear_all(session)` — operan contra la tabla `auth_attempts`.

La implementación busca compatibilidad retroactiva: cuando se llama con `session` (primer arg AsyncSession)
devuelve una coroutine que puede ser `await`-ed; cuando se llama sin sesión realiza la acción sincrónica.
"""

from __future__ import annotations

import threading
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth_attempt import AuthAttempt
from app.utils.exceptions import LimiteSolicitudes


class _SlidingWindow:
    """Sliding-window limiter que soporta APIs sync y async.

    - Si se llama como `check_and_record(session, key)` devuelve una coroutine.
    - Si se llama como `check_and_record(key)` ejecuta el path síncrono en memoria.
    """

    def __init__(
        self,
        max_calls: int,
        window_seconds: int,
        message: str,
        kind: str,
        namespace: str,
    ):
        self._max = max_calls
        self._window = timedelta(seconds=window_seconds)
        self._message = message
        self._kind = kind
        self._namespace = namespace

        # in-memory fallback state for synchronous API (tests, CLI)
        self._lock = threading.Lock()
        self._events: dict[str, list[datetime]] = {}

    def _namespaced(self, key: str) -> str:
        return f"{self._namespace}:{key}"

    # ----- synchronous (in-memory) helpers -----
    def _prune_and_count_sync(self, key: str) -> int:
        now = datetime.now(timezone.utc)
        cutoff = now - self._window
        with self._lock:
            events = self._events.setdefault(key, [])
            # prune
            events[:] = [t for t in events if t >= cutoff]
            return len(events)

    def _record_sync(self, key: str) -> None:
        now = datetime.now(timezone.utc)
        with self._lock:
            self._events.setdefault(key, []).append(now)

    def check_and_record(self, *args: Any) -> Any:
        """Overloaded method:
        - call as `check_and_record(key)` -> performs in-memory check and returns None
        - call as `check_and_record(session, key)` -> returns coroutine to be awaited
        """
        if len(args) == 1:
            key = args[0]
            count = self._prune_and_count_sync(key)
            if count >= self._max:
                raise LimiteSolicitudes(self._message)
            self._record_sync(key)
            return None
        if len(args) == 2:
            session, key = args
            if isinstance(session, AsyncSession):
                return self._check_and_record_async(session, key)
        raise TypeError("check_and_record expects (key) or (session, key)")

    # Backward-compatible aliases expected by services/tests
    def record_failure(self, *args: Any) -> Any:
        """Alias for check_and_record to preserve older callsites."""
        return self.check_and_record(*args)

    def is_blocked(self, *args: Any) -> Any:
        """Check blocked state sync or async.

        - `is_blocked(key)` -> bool
        - `await is_blocked(session, key)` -> bool
        """
        if len(args) == 1:
            key = args[0]
            return self._prune_and_count_sync(key) >= self._max
        if len(args) == 2:
            session, key = args
            if isinstance(session, AsyncSession):
                return self._is_blocked_async(session, key)
        raise TypeError("is_blocked expects (key) or (session, key)")

    async def _is_blocked_async(self, session: AsyncSession, key: str) -> bool:
        cutoff = datetime.now(timezone.utc) - self._window
        count_stmt = (
            select(func.count())
            .select_from(AuthAttempt)
            .where(
                AuthAttempt.key == self._namespaced(key),
                AuthAttempt.created_at >= cutoff,
            )
        )
        result = await session.execute(count_stmt)
        count = int(result.scalar() or 0)
        return count >= self._max

    def reset(self, *args: Any) -> Any:
        """Reset in-memory or async reset against DB depending on signature."""
        if len(args) == 1:
            key = args[0]
            with self._lock:
                self._events.pop(key, None)
            return None
        if len(args) == 2:
            session, key = args
            if isinstance(session, AsyncSession):
                return self._reset_async(session, key)
        raise TypeError("reset expects (key) or (session, key)")

    def clear_all(self) -> None:
        with self._lock:
            self._events.clear()

    # ----- async DB-backed implementations -----

    async def _check_and_record_async(self, session: AsyncSession, key: str) -> None:
        cutoff = datetime.now(timezone.utc) - self._window
        count_stmt = (
            select(func.count())
            .select_from(AuthAttempt)
            .where(
                AuthAttempt.key == self._namespaced(key),
                AuthAttempt.created_at >= cutoff,
            )
        )
        result = await session.execute(count_stmt)
        count = int(result.scalar() or 0)
        if count >= self._max:
            raise LimiteSolicitudes(self._message)
        # insert record; DB commit is managed by caller's transaction
        session.add(AuthAttempt(key=self._namespaced(key), kind=self._kind))

    async def _reset_async(self, session: AsyncSession, key: str) -> None:
        await session.execute(
            delete(AuthAttempt).where(AuthAttempt.key == self._namespaced(key))
        )

    async def clear_all_async(self, session: AsyncSession) -> None:
        await session.execute(delete(AuthAttempt))


# Export two instances used across the app/tests
ip_login_limiter = _SlidingWindow(
    max_calls=10,
    window_seconds=60,
    message="Demasiadas solicitudes desde esta IP, inténtelo más tarde",
    kind="ip_login",
    namespace="ip",
)

email_failure_tracker = _SlidingWindow(
    max_calls=5,
    window_seconds=15 * 60,
    message="Demasiados intentos para este email, inténtelo más tarde",
    kind="email_failure",
    namespace="email",
)
