"""
Rate limiter respaldado por PostgreSQL.

Diseñado para funcionar con Cloud Run con min-instances=0 y múltiples
réplicas: el estado vive en la tabla auth_attempts, no en memoria del
proceso. La retención de filas se gestiona con pg_cron en Supabase
(ver DEPLOY.md).
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.models.auth_attempt import AuthAttempt
from app.utils.exceptions import LimiteSolicitudes

# Lazy-initialized session factory backed by a NullPool engine so each autonomous
# commit gets a fresh connection — avoids asyncpg event-loop conflicts and ensures
# the AuthAttempt INSERT survives the caller's rollback on failed login.
_autonomous_maker: async_sessionmaker[AsyncSession] | None = None


def _get_autonomous_maker() -> async_sessionmaker[AsyncSession]:
    global _autonomous_maker
    if _autonomous_maker is None:
        from app.config import settings

        _engine = create_async_engine(
            settings.DATABASE_URL,
            poolclass=NullPool,
            connect_args={"statement_cache_size": 0},
        )
        _autonomous_maker = async_sessionmaker(_engine, expire_on_commit=False)
    return _autonomous_maker


class _DbSlidingWindow:
    """Sliding-window limiter persistido en PostgreSQL."""

    def __init__(
        self,
        max_calls: int,
        window_seconds: int,
        message: str,
        kind: str,
        namespace: str,
    ) -> None:
        self._max = max_calls
        self._window = timedelta(seconds=window_seconds)
        self._message = message
        self._kind = kind
        self._namespace = namespace

    def _namespaced(self, key: str) -> str:
        return f"{self._namespace}:{key}"

    async def check_and_record(self, session: AsyncSession, key: str) -> None:
        """Cuenta intentos en ventana; si excede, lanza LimiteSolicitudes;
        si no, registra el intento en sesión autónoma para sobrevivir rollbacks."""
        if await self._count_in_window(session, key) >= self._max:
            raise LimiteSolicitudes(self._message)
        # Autonomous session: caller may raise after this call (e.g. wrong password),
        # rolling back its own transaction — the AuthAttempt must survive that rollback.
        async with _get_autonomous_maker()() as own_session:
            async with own_session.begin():
                own_session.add(AuthAttempt(key=self._namespaced(key), kind=self._kind))

    async def record_failure(self, session: AsyncSession, key: str) -> None:
        session.add(AuthAttempt(key=self._namespaced(key), kind=self._kind))

    async def is_blocked(self, session: AsyncSession, key: str) -> bool:
        return await self._count_in_window(session, key) >= self._max

    async def reset(self, session: AsyncSession, key: str) -> int:
        """Borra todos los intentos del key. Devuelve cuántos se borraron."""
        result = await session.execute(
            delete(AuthAttempt).where(AuthAttempt.key == self._namespaced(key))
        )
        return int(result.rowcount or 0)  # type: ignore[attr-defined]

    async def _count_in_window(self, session: AsyncSession, key: str) -> int:
        cutoff = datetime.now(timezone.utc) - self._window
        result = await session.execute(
            select(func.count())
            .select_from(AuthAttempt)
            .where(
                AuthAttempt.key == self._namespaced(key),
                AuthAttempt.created_at >= cutoff,
            )
        )
        return int(result.scalar() or 0)


ip_login_limiter = _DbSlidingWindow(
    max_calls=10,
    window_seconds=60,
    message="Demasiadas solicitudes desde esta IP, inténtelo más tarde",
    kind="ip_login",
    namespace="ip",
)

email_failure_tracker = _DbSlidingWindow(
    max_calls=5,
    window_seconds=15 * 60,
    message="Demasiados intentos para este email, inténtelo más tarde",
    kind="email_failure",
    namespace="email",
)
