"""Tests for /auth/login and /auth/refresh endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_success(test_client: AsyncClient) -> None:
    resp = await test_client.post(
        "/auth/login", json={"email": "admin@sistema.com", "password": "Admin1234!"}
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
        "/auth/login", json={"email": "admin@sistema.com", "password": "Admin1234!"}
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
async def test_rol_insuficiente(test_client: AsyncClient) -> None:
    """Operador trying to create a user gets 403."""
    # Create operador via admin API
    admin_login = await test_client.post(
        "/auth/login", json={"email": "admin@sistema.com", "password": "Admin1234!"}
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
