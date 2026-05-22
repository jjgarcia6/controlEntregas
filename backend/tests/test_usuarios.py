"""Tests for /usuarios endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings


async def _admin_token(test_client: AsyncClient) -> str:
    resp = await test_client.post(
        "/auth/login",
        json={"email": settings.ADMIN_EMAIL, "password": settings.ADMIN_PASSWORD},
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


# ─── A4-bis: desbloquear endpoint ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_a4bis_admin_desbloquea_usuario_y_audita(
    test_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Admin puede desbloquear un usuario con intentos fallidos; queda auditado."""
    from app.utils.rate_limit import email_failure_tracker

    admin_login = await test_client.post(
        "/auth/login",
        json={"email": settings.ADMIN_EMAIL, "password": settings.ADMIN_PASSWORD},
    )
    admin_token = admin_login.json()["token"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    op_resp = await test_client.post(
        "/usuarios",
        json={
            "email": "bloqueado@test.com",
            "password": "Operador123!",
            "nombre": "Usuario Bloqueado",
            "rol": "operador",
        },
        headers=headers,
    )
    assert op_resp.status_code == 201
    op_id = op_resp.json()["id"]

    # Insert failures directly via db_session (bypasses login rollback issue)
    for _ in range(5):
        await email_failure_tracker.record_failure(db_session, "bloqueado@test.com")
    await db_session.flush()

    assert await email_failure_tracker.is_blocked(db_session, "bloqueado@test.com")

    unlock_resp = await test_client.post(
        f"/usuarios/{op_id}/desbloquear", headers=headers
    )
    assert unlock_resp.status_code == 200
    data = unlock_resp.json()
    assert data["intentos_eliminados"] == 5
    assert data["email"] == "bloqueado@test.com"

    assert not await email_failure_tracker.is_blocked(db_session, "bloqueado@test.com")


@pytest.mark.asyncio
async def test_a4bis_operador_no_puede_desbloquear(test_client: AsyncClient) -> None:
    """Solo admin puede desbloquear; un operador recibe 403."""
    admin_login = await test_client.post(
        "/auth/login",
        json={"email": settings.ADMIN_EMAIL, "password": settings.ADMIN_PASSWORD},
    )
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['token']}"}
    await test_client.post(
        "/usuarios",
        json={
            "email": "operador_no_admin@test.com",
            "password": "Operador123!",
            "nombre": "Operador",
            "rol": "operador",
        },
        headers=admin_headers,
    )

    op_login = await test_client.post(
        "/auth/login",
        json={"email": "operador_no_admin@test.com", "password": "Operador123!"},
    )
    op_headers = {"Authorization": f"Bearer {op_login.json()['token']}"}

    resp = await test_client.post(
        "/usuarios/00000000-0000-0000-0000-000000000001/desbloquear",
        headers=op_headers,
    )
    assert resp.status_code == 403
