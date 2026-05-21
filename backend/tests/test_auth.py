"""Tests for /auth/login and /auth/refresh endpoints."""

import pytest
from httpx import AsyncClient

from app.config import settings
from app.utils.rate_limit import email_failure_tracker, ip_login_limiter


@pytest.mark.asyncio
async def test_login_success(test_client: AsyncClient) -> None:
    resp = await test_client.post(
        "/auth/login",
        json={"email": "admin@sistema.com", "password": settings.ADMIN_PASSWORD},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data
    assert data["user"]["rol"] == "admin"


@pytest.mark.asyncio
async def test_login_wrong_password(test_client: AsyncClient) -> None:
    resp = await test_client.post(
        "/auth/login", json={"email": "admin@sistema.com", "password": "wrongpass"}
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
        json={"email": "admin@sistema.com", "password": settings.ADMIN_PASSWORD},
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
    email_failure_tracker.reset("ratelimit_email_test@test.com")
    for _ in range(5):
        await test_client.post(
            "/auth/login",
            json={"email": "ratelimit_email_test@test.com", "password": "wrong"},
        )
    resp = await test_client.post(
        "/auth/login",
        json={"email": "ratelimit_email_test@test.com", "password": "wrong"},
    )
    assert resp.status_code == 403
    email_failure_tracker.reset("ratelimit_email_test@test.com")


@pytest.mark.asyncio
async def test_ip_rate_limit(test_client: AsyncClient) -> None:
    """11 requests from the same IP within a minute trigger 429."""
    test_ip = "10.0.0.99"
    ip_login_limiter.reset(test_ip)
    for _ in range(10):
        ip_login_limiter.check_and_record(test_ip)
    from app.utils.exceptions import LimiteSolicitudes

    with pytest.raises(LimiteSolicitudes):
        ip_login_limiter.check_and_record(test_ip)
    ip_login_limiter.reset(test_ip)


@pytest.mark.asyncio
async def test_successful_login_resets_email_counter(test_client: AsyncClient) -> None:
    """A successful login clears the failure counter for that email."""
    email_failure_tracker.reset("admin@sistema.com")
    for _ in range(3):
        await test_client.post(
            "/auth/login",
            json={"email": "admin@sistema.com", "password": "wrong"},
        )
    resp = await test_client.post(
        "/auth/login",
        json={"email": "admin@sistema.com", "password": settings.ADMIN_PASSWORD},
    )
    assert resp.status_code == 200
    assert not email_failure_tracker.is_blocked("admin@sistema.com")


@pytest.mark.asyncio
async def test_rol_insuficiente(test_client: AsyncClient) -> None:
    """Operador trying to create a user gets 403."""
    # Create operador via admin API
    admin_login = await test_client.post(
        "/auth/login",
        json={"email": "admin@sistema.com", "password": settings.ADMIN_PASSWORD},
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
