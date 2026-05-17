"""
Seed script — run once after migrations to populate admin user and initial banks.
Safe to re-run: uses INSERT ... ON CONFLICT DO NOTHING.

Usage:
    cd backend && python seed.py
"""

import asyncio
import uuid

import bcrypt

from app.config import settings
from app.database import AsyncSessionLocal


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            from sqlalchemy import text

            admin_id = uuid.uuid4()
            password_hash = bcrypt.hashpw(
                settings.ADMIN_PASSWORD.encode(), bcrypt.gensalt()
            ).decode()

            await session.execute(
                text(
                    """
                    INSERT INTO usuarios (id, email, password_hash, nombre, rol, is_active)
                    VALUES (:id, :email, :password_hash, :nombre, :rol, true)
                    ON CONFLICT (email) DO NOTHING
                    """
                ),
                {
                    "id": admin_id,
                    "email": settings.ADMIN_EMAIL,
                    "password_hash": password_hash,
                    "nombre": "Administrador",
                    "rol": "admin",
                },
            )

            bancos = [
                "Banco Pichincha",
                "Banco Guayaquil",
                "Banco del Pacífico",
                "Produbanco",
                "Banco Internacional",
                "Banco Bolivariano",
                "Banco de Machala",
                "Banco del Austro",
                "Banco General Rumiñahui",
                "Cooperativa JEP",
                "Cooperativa 29 de Octubre",
                "BIESS",
            ]

            for nombre in bancos:
                await session.execute(
                    text(
                        """
                        INSERT INTO bancos (id, nombre, is_active)
                        VALUES (gen_random_uuid(), :nombre, true)
                        ON CONFLICT (nombre) DO NOTHING
                        """
                    ),
                    {"nombre": nombre},
                )

    print(f"Seed complete — admin: {settings.ADMIN_EMAIL}, banks: {len(bancos)}")


if __name__ == "__main__":
    asyncio.run(seed())
