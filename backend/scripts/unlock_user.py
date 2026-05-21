#!/usr/bin/env python3
"""
Script de emergencia: desbloquea los intentos fallidos de un usuario.

Uso:
    cd backend
    python scripts/unlock_user.py <email>

Ejemplo:
    python scripts/unlock_user.py admin@sistema.com

Este script bypasea el sistema de auth y borra directamente los registros
de auth_attempts asociados al email. Útil solo en caso de emergencia (todos
los admins bloqueados, sin acceso a la UI).

Requiere DATABASE_URL en el entorno o en backend/.env.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()  # noqa: E402

from app.config import settings  # noqa: E402
from app.models.auth_attempt import AuthAttempt  # noqa: E402
from sqlalchemy import delete  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402
from sqlalchemy.pool import NullPool  # noqa: E402


async def unlock(email: str) -> None:
    if not email or "@" not in email:
        print(f"ERROR: '{email}' no parece un email válido", file=sys.stderr)
        sys.exit(1)

    engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
    SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

    try:
        async with SessionLocal() as session:
            async with session.begin():
                key = f"email:{email.lower()}"
                result = await session.execute(
                    delete(AuthAttempt).where(AuthAttempt.key == key)
                )
                # Result.rowcount is not well-typed by SQLAlchemy stubs; use getattr
                deleted = int(getattr(result, "rowcount", 0) or 0)

        if deleted == 0:
            print(f"No había intentos registrados para {email}.")
        else:
            print(f"OK: {deleted} intento(s) eliminado(s) para {email}.")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Uso: python {sys.argv[0]} <email>", file=sys.stderr)
        sys.exit(1)
    asyncio.run(unlock(sys.argv[1]))
