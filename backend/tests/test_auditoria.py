"""Integration tests for /audit endpoints."""

import uuid

import pytest
from httpx import AsyncClient

from app.config import settings

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_token(client: AsyncClient, email: str, password: str) -> str:
    resp = await client.post("/auth/login", json={"email": email, "password": password})
    return str(resp.json()["token"])


async def _admin_token(client: AsyncClient) -> str:
    return await _get_token(client, "admin@sistema.com", settings.ADMIN_PASSWORD)


async def _create_user_token(
    client: AsyncClient, admin_token: str, email: str, rol: str
) -> str:
    await client.post(
        "/usuarios",
        json={"email": email, "password": "Test1234!", "nombre": "Test", "rol": rol},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    return await _get_token(client, email, "Test1234!")


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# GET /audit
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_should_return_paginated_audit_log_for_admin(
    test_client: AsyncClient,
) -> None:
    token = await _admin_token(test_client)
    resp = await test_client.get("/audit", headers=_auth(token))

    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_should_return_403_for_operador_accessing_audit(
    test_client: AsyncClient,
) -> None:
    admin_token = await _admin_token(test_client)
    op_token = await _create_user_token(
        test_client,
        admin_token,
        f"op_audit_{uuid.uuid4().hex[:6]}@test.com",
        "operador",
    )
    resp = await test_client.get("/audit", headers=_auth(op_token))
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_should_return_403_for_lectura_accessing_audit(
    test_client: AsyncClient,
) -> None:
    admin_token = await _admin_token(test_client)
    lec_token = await _create_user_token(
        test_client,
        admin_token,
        f"lec_audit_{uuid.uuid4().hex[:6]}@test.com",
        "lectura",
    )
    resp = await test_client.get("/audit", headers=_auth(lec_token))
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_should_filter_audit_log_by_entidad(
    test_client: AsyncClient,
) -> None:
    token = await _admin_token(test_client)
    resp = await test_client.get(
        "/audit",
        params={"entidad": "banco"},
        headers=_auth(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    for item in data["items"]:
        assert item["entidad"] == "banco"


@pytest.mark.asyncio
async def test_should_filter_audit_log_by_date_range(
    test_client: AsyncClient,
) -> None:
    token = await _admin_token(test_client)
    resp = await test_client.get(
        "/audit",
        params={"fecha_desde": "2020-01-01", "fecha_hasta": "2099-12-31"},
        headers=_auth(token),
    )
    assert resp.status_code == 200
    assert "items" in resp.json()


@pytest.mark.asyncio
async def test_should_return_422_for_page_size_zero(
    test_client: AsyncClient,
) -> None:
    token = await _admin_token(test_client)
    resp = await test_client.get(
        "/audit",
        params={"page_size": 0},
        headers=_auth(token),
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /audit/export
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_should_return_csv_export_with_correct_content_type(
    test_client: AsyncClient,
) -> None:
    token = await _admin_token(test_client)
    resp = await test_client.get(
        "/audit/export",
        params={"formato": "csv"},
        headers=_auth(token),
    )
    assert resp.status_code == 200
    assert "text/csv" in resp.headers.get("content-type", "")
    assert "attachment" in resp.headers.get("content-disposition", "")
    assert resp.content  # non-empty


@pytest.mark.asyncio
async def test_should_return_json_export_with_correct_content_type(
    test_client: AsyncClient,
) -> None:
    token = await _admin_token(test_client)
    resp = await test_client.get(
        "/audit/export",
        params={"formato": "json"},
        headers=_auth(token),
    )
    assert resp.status_code == 200
    assert "application/json" in resp.headers.get("content-type", "")
    assert "attachment" in resp.headers.get("content-disposition", "")
    assert resp.content


@pytest.mark.asyncio
async def test_should_return_422_for_invalid_formato_in_export(
    test_client: AsyncClient,
) -> None:
    token = await _admin_token(test_client)
    resp = await test_client.get(
        "/audit/export",
        params={"formato": "xlsx"},
        headers=_auth(token),
    )
    assert resp.status_code == 422
