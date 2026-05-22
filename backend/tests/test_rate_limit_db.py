"""
Tests unitarios del rate limiter persistido en PostgreSQL (A4).
Prueban la lógica del _DbSlidingWindow directamente, sin pasar por endpoints.
"""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth_attempt import AuthAttempt
from app.utils.exceptions import LimiteSolicitudes
from app.utils.rate_limit import email_failure_tracker, ip_login_limiter


@pytest.mark.asyncio
async def test_a4_persiste_intentos_en_bd(db_session: AsyncSession) -> None:
    """Cada llamada a check_and_record inserta una fila en auth_attempts."""
    await ip_login_limiter.check_and_record(db_session, "192.0.2.1")

    result = await db_session.execute(
        select(AuthAttempt).where(AuthAttempt.key == "ip:192.0.2.1")
    )
    rows = result.scalars().all()
    assert len(rows) == 1
    assert rows[0].kind == "ip_login"


@pytest.mark.asyncio
async def test_a4_bloquea_al_superar_threshold(db_session: AsyncSession) -> None:
    """Al 11º intento (threshold IP = 10/60s), lanza LimiteSolicitudes."""
    for _ in range(10):
        await ip_login_limiter.check_and_record(db_session, "192.0.2.2")

    with pytest.raises(LimiteSolicitudes):
        await ip_login_limiter.check_and_record(db_session, "192.0.2.2")


@pytest.mark.asyncio
async def test_a4_reset_borra_intentos(db_session: AsyncSession) -> None:
    """reset() borra todos los registros del key y devuelve la cuenta."""
    for _ in range(3):
        await email_failure_tracker.record_failure(db_session, "victima@test.com")
    await db_session.flush()

    eliminados = await email_failure_tracker.reset(db_session, "victima@test.com")
    await db_session.flush()
    assert eliminados == 3

    assert not await email_failure_tracker.is_blocked(db_session, "victima@test.com")


@pytest.mark.asyncio
async def test_a4_namespacing_separa_ip_de_email(db_session: AsyncSession) -> None:
    """
    Los limitadores de IP y email comparten tabla pero usan prefijos distintos
    (ip: vs email:). Bloquear uno no debe afectar al otro.
    """
    for _ in range(5):
        await email_failure_tracker.record_failure(db_session, "ataque@test.com")
    await db_session.flush()

    assert not await ip_login_limiter.is_blocked(db_session, "ataque@test.com")
