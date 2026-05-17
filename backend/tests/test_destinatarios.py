"""Tests for /destinatarios endpoints."""

import pytest
from httpx import AsyncClient

_CEDULA_VALIDA = "1713175071"  # valid ecuadorian cedula (modulo-10)
_RUC_VALIDO = "1713175071001"  # valid RUC derived from above cedula
_CEDULA_INVALIDA = "1234567890"  # bad checksum


async def _admin_token(test_client: AsyncClient) -> str:
    resp = await test_client.post(
        "/auth/login", json={"email": "admin@sistema.com", "password": "Admin1234!"}
    )
    return str(resp.json()["token"])


@pytest.mark.asyncio
async def test_crear_destinatario_cedula_valida(test_client: AsyncClient) -> None:
    token = await _admin_token(test_client)
    resp = await test_client.post(
        "/destinatarios",
        json={
            "identificacion": _CEDULA_VALIDA,
            "nombre": "Juan Pérez",
            "direccion": "Av. Principal 123",
            "telefono": "0991234567",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["tipo_identificacion"] == "cedula"


@pytest.mark.asyncio
async def test_crear_destinatario_ruc_valido(test_client: AsyncClient) -> None:
    token = await _admin_token(test_client)
    resp = await test_client.post(
        "/destinatarios",
        json={
            "identificacion": _RUC_VALIDO,
            "nombre": "Empresa Test S.A.",
            "direccion": "Calle Industria 456",
            "telefono": "022345678",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["tipo_identificacion"] == "ruc"


@pytest.mark.asyncio
async def test_crear_destinatario_cedula_invalida(test_client: AsyncClient) -> None:
    token = await _admin_token(test_client)
    resp = await test_client.post(
        "/destinatarios",
        json={
            "identificacion": _CEDULA_INVALIDA,
            "nombre": "Inválido",
            "direccion": "Dirección",
            "telefono": "0991234567",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_crear_destinatario_duplicado(test_client: AsyncClient) -> None:
    token = await _admin_token(test_client)
    valid_payload = {
        "identificacion": _CEDULA_VALIDA,
        "nombre": "Dup Test",
        "direccion": "Dir",
        "telefono": "0991234567",
    }
    await test_client.post(
        "/destinatarios",
        json=valid_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = await test_client.post(
        "/destinatarios",
        json=valid_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_buscar_por_identificacion_existente(test_client: AsyncClient) -> None:
    token = await _admin_token(test_client)
    await test_client.post(
        "/destinatarios",
        json={
            "identificacion": _CEDULA_VALIDA,
            "nombre": "Buscar Test",
            "direccion": "Dir",
            "telefono": "0991234567",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = await test_client.get(
        f"/destinatarios/{_CEDULA_VALIDA}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["identificacion"] == _CEDULA_VALIDA


@pytest.mark.asyncio
async def test_buscar_por_identificacion_inexistente(test_client: AsyncClient) -> None:
    token = await _admin_token(test_client)
    resp = await test_client.get(
        "/destinatarios/9999999999",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404
