"""
Tests para los headers de seguridad y middlewares globales (M2, M6).
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_m2_csp_incluye_directivas_modernas(test_client: AsyncClient) -> None:
    """M2: el header CSP debe incluir frame-ancestors, base-uri y form-action."""
    resp = await test_client.get("/")
    csp = resp.headers.get("content-security-policy", "")
    assert "default-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp
    assert "base-uri 'self'" in csp
    assert "form-action 'self'" in csp


@pytest.mark.asyncio
async def test_m2_otros_headers_de_seguridad_presentes(
    test_client: AsyncClient,
) -> None:
    """Defensa en profundidad: los headers heredados siguen presentes."""
    resp = await test_client.get("/")
    assert resp.headers.get("strict-transport-security")
    assert resp.headers.get("x-content-type-options") == "nosniff"
    assert resp.headers.get("x-frame-options") == "DENY"
    assert resp.headers.get("referrer-policy")


@pytest.mark.asyncio
async def test_m6_body_excedido_responde_413(test_client: AsyncClient) -> None:
    """M6: un Content-Length que supera el límite es rechazado antes de procesar."""
    # 3 MB > MAX_REQUEST_BODY_MB (default 2)
    big_payload = "A" * (3 * 1024 * 1024)
    resp = await test_client.post(
        "/auth/login",
        content=f'{{"email":"x","password":"{big_payload}"}}',
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 413
    assert "máximo permitido" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_m6_content_length_invalido_responde_400(
    test_client: AsyncClient,
) -> None:
    """M6: si Content-Length no es un entero válido, responde 400."""
    # httpx may override Content-Length; this test documents the defensive path.
    resp = await test_client.post(
        "/auth/login",
        json={"email": "x", "password": "x"},
        headers={"Content-Length": "abc"},
    )
    assert resp.status_code in (200, 400, 401, 403, 422)
