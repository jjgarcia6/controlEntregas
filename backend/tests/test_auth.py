"""Tests for /auth/login and /auth/refresh endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings


@pytest.mark.asyncio
async def test_login_success(test_client: AsyncClient) -> None:
    resp = await test_client.post(
        "/auth/login",
        json={"email": settings.ADMIN_EMAIL, "password": settings.ADMIN_PASSWORD},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data
    assert data["user"]["rol"] == "admin"


@pytest.mark.asyncio
async def test_login_wrong_password(test_client: AsyncClient) -> None:
    resp = await test_client.post(
        "/auth/login", json={"email": settings.ADMIN_EMAIL, "password": "wrongpass"}
    )
    assert resp.status_code == 403
    assert "token" not in resp.json()


@pytest.mark.asyncio
async def test_login_nonexistent_user(test_client: AsyncClient) -> None:
    resp = await test_client.post(
        "/auth/login",
        json={"email": "noexiste@example.com", "password": "cualquiera123"},
    )
    assert resp.status_code == 403
    assert "token" not in resp.json()


@pytest.mark.asyncio
async def test_refresh_success(test_client: AsyncClient) -> None:
    login = await test_client.post(
        "/auth/login",
        json={"email": settings.ADMIN_EMAIL, "password": settings.ADMIN_PASSWORD},
    )
    token = login.json()["token"]
    resp = await test_client.post(
        "/auth/refresh", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    assert "token" in resp.json()


@pytest.mark.asyncio
async def test_protected_endpoint_no_auth(test_client: AsyncClient) -> None:
    resp = await test_client.get("/usuarios")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_email_rate_limit(test_client: AsyncClient) -> None:
    """5 consecutive failures for the same email trigger 403 on the 6th attempt."""
    email = "ratelimit_email_test@test.com"
    for _ in range(5):
        await test_client.post(
            "/auth/login", json={"email": email, "password": "wrong"}
        )
    resp = await test_client.post(
        "/auth/login", json={"email": email, "password": "wrong"}
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_ip_rate_limit(test_client: AsyncClient) -> None:
    """11 requests from the same IP within a minute trigger 429 via the endpoint."""
    headers = {"X-Forwarded-For": "10.0.0.99"}
    for _ in range(10):
        await test_client.post(
            "/auth/login",
            json={"email": "any@test.com", "password": "wrong"},
            headers=headers,
        )
    resp = await test_client.post(
        "/auth/login",
        json={"email": "any@test.com", "password": "wrong"},
        headers=headers,
    )
    assert resp.status_code == 429


@pytest.mark.asyncio
async def test_successful_login_resets_email_counter(
    test_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """A successful login clears the failure counter for that email."""
    from app.utils.rate_limit import email_failure_tracker

    for _ in range(3):
        await test_client.post(
            "/auth/login",
            json={"email": settings.ADMIN_EMAIL, "password": "wrong"},
        )
    resp = await test_client.post(
        "/auth/login",
        json={"email": settings.ADMIN_EMAIL, "password": settings.ADMIN_PASSWORD},
    )
    assert resp.status_code == 200
    assert not await email_failure_tracker.is_blocked(
        db_session, settings.ADMIN_EMAIL.lower()
    )


@pytest.mark.asyncio
async def test_rol_insuficiente(test_client: AsyncClient) -> None:
    """Operador trying to create a user gets 403."""
    # Create operador via admin API
    admin_login = await test_client.post(
        "/auth/login",
        json={"email": settings.ADMIN_EMAIL, "password": settings.ADMIN_PASSWORD},
    )
    admin_token = admin_login.json()["token"]
    await test_client.post(
        "/usuarios",
        json={
            "email": "operador_test_rol@test.com",
            "password": "Operador123!",
            "nombre": "Operador Test",
            "rol": "operador",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    op_login = await test_client.post(
        "/auth/login",
        json={"email": "operador_test_rol@test.com", "password": "Operador123!"},
    )
    token = op_login.json()["token"]
    resp = await test_client.post(
        "/usuarios",
        json={
            "email": "nuevo@test.com",
            "password": "Password123!",
            "nombre": "Nuevo",
            "rol": "lectura",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


# ─── A5: X-Forwarded-For ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_a5_x_forwarded_for_se_usa_como_ip(
    test_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """
    A5: cuando llega X-Forwarded-For, el rate limiter usa esa IP, no la del proxy.
    Verificamos que 10 intentos con la misma X-Forwarded-For bloquean la siguiente.
    """
    forwarded_ip = "203.0.113.42"
    for _ in range(10):
        await test_client.post(
            "/auth/login",
            json={"email": "any@test.com", "password": "wrong"},
            headers={"X-Forwarded-For": f"{forwarded_ip}, 10.0.0.1"},
        )
    resp = await test_client.post(
        "/auth/login",
        json={"email": "any@test.com", "password": "wrong"},
        headers={"X-Forwarded-For": f"{forwarded_ip}, 10.0.0.1"},
    )
    assert resp.status_code == 429

    # Verificar que la fila en BD tiene exactamente la primera IP del XFF,
    # no la del proxy
    from app.models.auth_attempt import AuthAttempt
    from sqlalchemy import select

    result = await db_session.execute(
        select(AuthAttempt).where(AuthAttempt.key == f"ip:{forwarded_ip}")
    )
    rows = result.scalars().all()
    assert len(rows) >= 10  # al menos los 10 que insertamos


@pytest.mark.asyncio
async def test_a5_sin_x_forwarded_for_usa_client_host(
    test_client: AsyncClient,
) -> None:
    """A5: sin X-Forwarded-For, get_client_ip cae a request.client.host (no rompe)."""
    # No fallar si el test se ejecuta sin el header
    resp = await test_client.post(
        "/auth/login", json={"email": "any@test.com", "password": "wrong"}
    )
    # No importa el código exacto; importa que el endpoint no rompa por falta del header
    assert resp.status_code in (401, 403, 429)
