#!/usr/bin/env python3
"""
Data migration: encrypt existing plaintext PII and populate identificacion_hash.

Run ONCE after applying migration c3d4e5f6a7b8, before deploying the new code:

    cd backend
    source .venv/bin/activate
    python scripts/encrypt_existing_data.py

Idempotent: rows already encrypted (Fernet tokens start with 'gAAAAA') are skipped.
Requires ENCRYPTION_KEY in the environment (loaded from .env).
"""

import asyncio
import sys
from pathlib import Path

# Make app importable from the scripts/ directory
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import NullPool

from app.config import settings
from app.utils.encryption import hmac_hash

_fernet = Fernet(settings.ENCRYPTION_KEY.encode())


def _is_encrypted(value: str | None) -> bool:
    if value is None:
        return True
    try:
        _fernet.decrypt(value.encode())
        return True
    except (InvalidToken, Exception):
        return False


def _encrypt(value: str | None) -> str | None:
    if value is None:
        return None
    if _is_encrypted(value):
        return value  # already encrypted
    return _fernet.encrypt(value.encode()).decode()


async def migrate() -> None:
    engine = create_async_engine(
        settings.DATABASE_URL,
        poolclass=NullPool,
        connect_args={"statement_cache_size": 0},
    )

    async with AsyncSession(engine) as session:
        async with session.begin():
            # --- destinatarios ---
            rows = (
                await session.execute(
                    text(
                        "SELECT id, identificacion, nombre, direccion, telefono, email "
                        "FROM destinatarios"
                    )
                )
            ).fetchall()

            dest_updated = 0
            for row in rows:
                id_, ident, nombre, direccion, telefono, email = row
                if _is_encrypted(ident):
                    continue  # already migrated
                await session.execute(
                    text("""
                    UPDATE destinatarios SET
                        identificacion      = :identificacion,
                        identificacion_hash = :identificacion_hash,
                        nombre              = :nombre,
                        direccion           = :direccion,
                        telefono            = :telefono,
                        email               = :email
                    WHERE id = :id
                """),
                    {
                        "id": id_,
                        "identificacion": _encrypt(ident),
                        "identificacion_hash": hmac_hash(ident),
                        "nombre": _encrypt(nombre),
                        "direccion": _encrypt(direccion),
                        "telefono": _encrypt(telefono),
                        "email": _encrypt(email),
                    },
                )
                dest_updated += 1
            print(f"destinatarios: {dest_updated}/{len(rows)} filas cifradas")

            # --- pagos ---
            rows = (
                await session.execute(text("SELECT id, nombre_titular FROM pagos"))
            ).fetchall()

            pagos_updated = 0
            for row in rows:
                id_, nombre_titular = row
                if _is_encrypted(nombre_titular):
                    continue
                await session.execute(
                    text("UPDATE pagos SET nombre_titular = :v WHERE id = :id"),
                    {"id": id_, "v": _encrypt(nombre_titular)},
                )
                pagos_updated += 1
            print(f"pagos: {pagos_updated}/{len(rows)} filas cifradas")

            # --- entregas (snap fields) ---
            rows = (
                await session.execute(
                    text(
                        "SELECT id, snap_identificacion, snap_nombre, snap_direccion, snap_telefono "
                        "FROM entregas"
                    )
                )
            ).fetchall()

            entregas_updated = 0
            for row in rows:
                id_, snap_id, snap_nom, snap_dir, snap_tel = row
                if _is_encrypted(snap_id):
                    continue
                await session.execute(
                    text("""
                    UPDATE entregas SET
                        snap_identificacion = :snap_id,
                        snap_nombre         = :snap_nom,
                        snap_direccion      = :snap_dir,
                        snap_telefono       = :snap_tel
                    WHERE id = :id
                """),
                    {
                        "id": id_,
                        "snap_id": _encrypt(snap_id),
                        "snap_nom": _encrypt(snap_nom),
                        "snap_dir": _encrypt(snap_dir),
                        "snap_tel": _encrypt(snap_tel),
                    },
                )
                entregas_updated += 1
            print(f"entregas: {entregas_updated}/{len(rows)} filas cifradas")

    await engine.dispose()
    print("Migración completada.")


if __name__ == "__main__":
    asyncio.run(migrate())
