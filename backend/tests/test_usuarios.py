"""Tests for /usuarios endpoints."""

import pytest
from httpx import AsyncClient


async def _admin_token(test_client: AsyncClient) -> str:
    resp = await test_client.post(
        "/auth/login", json={"email": "admin@sistema.com", "password": "Admin1234!"}
    )
    return str(resp.json()["token"])


@pytest.mark.asyncio
async def test_crear_usuario_success(test_client: AsyncClient) -> None:
    token = await _admin_token(test_client)
    resp = await test_client.post(
        "/usuarios",
        json={
            "email": "nuevo_usuario@test.com",
            "password": "Password123!",
            "nombre": "Nuevo Usuario",
            "rol": "lectura",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["email"] == "nuevo_usuario@test.com"


@pytest.mark.asyncio
async def test_crear_usuario_email_duplicado(test_client: AsyncClient) -> None:
    token = await _admin_token(test_client)
    payload = {
        "email": "dup_test@test.com",
        "password": "Password123!",
        "nombre": "Dup",
        "rol": "lectura",
    }
    await test_client.post(
        "/usuarios", json=payload, headers={"Authorization": f"Bearer {token}"}
    )
    resp = await test_client.post(
        "/usuarios", json=payload, headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_crear_usuario_password_invalida(test_client: AsyncClient) -> None:
    token = await _admin_token(test_client)
    resp = await test_client.post(
        "/usuarios",
        json={
            "email": "short_pass@test.com",
            "password": "short",
            "nombre": "Bad Pass",
            "rol": "lectura",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_desactivar_usuario(test_client: AsyncClient) -> None:
    token = await _admin_token(test_client)
    create_resp = await test_client.post(
        "/usuarios",
        json={
            "email": "to_delete@test.com",
            "password": "Password123!",
            "nombre": "To Delete",
            "rol": "lectura",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    user_id = create_resp.json()["id"]

    del_resp = await test_client.delete(
        f"/usuarios/{user_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert del_resp.status_code == 200

    list_resp = await test_client.get(
        "/usuarios", headers={"Authorization": f"Bearer {token}"}
    )
    ids = [u["id"] for u in list_resp.json()]
    assert user_id not in ids


@pytest.mark.asyncio
async def test_cambiar_password(test_client: AsyncClient) -> None:
    token = await _admin_token(test_client)
    create_resp = await test_client.post(
        "/usuarios",
        json={
            "email": "change_pass@test.com",
            "password": "OldPassword123!",
            "nombre": "Change Pass",
            "rol": "lectura",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    user_id = create_resp.json()["id"]

    patch_resp = await test_client.patch(
        f"/usuarios/{user_id}/password",
        json={"nueva_password": "NewPassword456!"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert patch_resp.status_code == 200

    login_resp = await test_client.post(
        "/auth/login",
        json={"email": "change_pass@test.com", "password": "NewPassword456!"},
    )
    assert login_resp.status_code == 200
    assert "token" in login_resp.json()
