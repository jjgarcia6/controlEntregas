import os
import bcrypt
from sqlalchemy import text

import pytest_asyncio
from dotenv import load_dotenv
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

load_dotenv()  # must run before os.getenv below

from app.dependencies.db import get_db  # noqa: E402
from app.config import settings  # noqa: E402
from app.main import app  # noqa: E402
from app.models.base import Base  # noqa: E402

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/control_entregas_test",
)

# NullPool + statement_cache_size=0: required for Supabase/PgBouncer transaction mode.
# NullPool prevents SQLAlchemy from holding connections across transactions.
# statement_cache_size=0 disables prepared statements incompatible with PgBouncer.
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool,
    connect_args={"statement_cache_size": 0},
)

# Skip destructive teardown when running against a shared DB such as Supabase.
_SHARED_DB = (
    "localhost" not in TEST_DATABASE_URL and "127.0.0.1" not in TEST_DATABASE_URL
)


@pytest_asyncio.fixture(scope="session")
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        password_hash = bcrypt.hashpw(
            settings.ADMIN_PASSWORD.encode(), bcrypt.gensalt()
        ).decode()
        await conn.execute(
            text(
                """
                INSERT INTO usuarios (email, password_hash, nombre, rol, is_active)
                VALUES (:email, :password_hash, :nombre, :rol, true)
                ON CONFLICT (email) DO NOTHING
                """
            ),
            {
                "email": settings.ADMIN_EMAIL,
                "password_hash": password_hash,
                "nombre": "Administrador",
                "rol": "admin",
            },
        )
    yield
    if not _SHARED_DB:
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_connection(setup_database):
    """One real transaction per test; all requests within a test share this connection."""
    async with test_engine.connect() as conn:
        await conn.begin()
        yield conn
        await conn.rollback()


@pytest_asyncio.fixture
async def db_session(db_connection):
    """Direct session access for tests that need it (most tests use test_client)."""
    session = AsyncSession(db_connection, join_transaction_mode="create_savepoint")
    yield session
    await session.close()


@pytest_asyncio.fixture
async def test_client(db_connection):
    """
    Each HTTP request within a test gets a fresh AsyncSession bound to db_connection.
    Using create_savepoint mode so session.begin_nested() (used by routers) creates
    SAVEPOINTs instead of real transactions. Committing the session releases the
    SAVEPOINT, making writes visible to subsequent requests on the same connection.
    Rolling back on exception undoes the request's savepoint only.
    Everything is rolled back when db_connection teardown calls conn.rollback().
    """

    async def override_get_db():
        session = AsyncSession(db_connection, join_transaction_mode="create_savepoint")
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
    app.dependency_overrides.clear()
