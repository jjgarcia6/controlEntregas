from fastapi import APIRouter, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.db import get_db
from app.schemas.auth import LoginRequest, LoginResponse, RefreshResponse
from app.services import auth_service
from app.utils.exceptions import PermisoInsuficiente

router = APIRouter(prefix="/auth", tags=["auth"])

_bearer = HTTPBearer(auto_error=False)


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> LoginResponse:
    ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return await auth_service.login(
        email=str(body.email),
        password=body.password,
        ip=ip,
        user_agent=user_agent,
        session=session,
    )


@router.post("/refresh", response_model=RefreshResponse)
async def refresh(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    session: AsyncSession = Depends(get_db),
) -> RefreshResponse:
    if credentials is None:
        raise PermisoInsuficiente("Token requerido")
    return await auth_service.refresh(token=credentials.credentials, session=session)
