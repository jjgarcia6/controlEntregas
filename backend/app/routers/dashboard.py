from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.models.usuario import Usuario
from app.schemas.dashboard import DashboardResponse
from app.services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponse)
async def obtener_dashboard(
    _: Usuario = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> DashboardResponse:
    return await dashboard_service.obtener_dashboard(session=session)
