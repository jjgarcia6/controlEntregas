from fastapi import APIRouter, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.db import get_db
from app.schemas.auth import LoginRequest, LoginResponse, RefreshResponse
from app.services import auth_service
from app.utils.exceptions import PermisoInsuficiente
from app.utils.rate_limit import ip_login_limiter
from app.utils.request_meta import get_client_ip

router = APIRouter(prefix="/auth", tags=["auth"])

_bearer = HTTPBearer(auto_error=False)


async def _check_ip_limit(
    request: Request, session: AsyncSession = Depends(get_db)
) -> str | None:
    ip = get_client_ip(request)
    if ip:
        await ip_login_limiter.check_and_record(session, ip)
    return ip


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
    ip: str | None = Depends(_check_ip_limit),
) -> LoginResponse:
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
