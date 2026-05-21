"""Tests for /bancos endpoints."""

import pytest
from httpx import AsyncClient

from app.config import settings


async def _token(test_client: AsyncClient, email: str, password: str) -> str:
    resp = await test_client.post(
        "/auth/login", json={"email": email, "password": password}
    )
    return str(resp.json()["token"])


async def _admin_token(test_client: AsyncClient) -> str:
    return await _token(test_client, "admin@sistema.com", settings.ADMIN_PASSWORD)


async def _create_operador(test_client: AsyncClient, admin_token: str) -> str:
    await test_client.post(
        "/usuarios",
        json={
            "email": "operador_banco@test.com",
            "password": "Operador123!",
            "nombre": "Operador Banco",
            "rol": "operador",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    return await _token(test_client, "operador_banco@test.com", "Operador123!")


async def _create_lectura(test_client: AsyncClient, admin_token: str) -> str:
    await test_client.post(
        "/usuarios",
        json={
            "email": "lectura_banco@test.com",
            "password": "Lectura123!",
            "nombre": "Lectura Banco",
            "rol": "lectura",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    return await _token(test_client, "lectura_banco@test.com", "Lectura123!")


@pytest.mark.asyncio
async def test_crear_banco_success(test_client: AsyncClient) -> None:
    token = await _admin_token(test_client)
    resp = await test_client.post(
        "/bancos",
        json={"nombre": "Banco Test Nuevo"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["nombre"] == "Banco Test Nuevo"


@pytest.mark.asyncio
async def test_crear_banco_nombre_duplicado(test_client: AsyncClient) -> None:
    token = await _admin_token(test_client)
    await test_client.post(
        "/bancos",
        json={"nombre": "Banco Duplicado"},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = await test_client.post(
        "/bancos",
        json={"nombre": "Banco Duplicado"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_operador_puede_crear_banco(test_client: AsyncClient) -> None:
    admin_token = await _admin_token(test_client)
    op_token = await _create_operador(test_client, admin_token)
    resp = await test_client.post(
        "/bancos",
        json={"nombre": "Banco Por Operador"},
        headers={"Authorization": f"Bearer {op_token}"},
    )
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_lectura_no_puede_crear_banco(test_client: AsyncClient) -> None:
    admin_token = await _admin_token(test_client)
    lec_token = await _create_lectura(test_client, admin_token)
    resp = await test_client.post(
        "/bancos",
        json={"nombre": "Banco No Autorizado"},
        headers={"Authorization": f"Bearer {lec_token}"},
    )
    assert resp.status_code == 403
