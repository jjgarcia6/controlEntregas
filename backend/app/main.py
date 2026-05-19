from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.routers import (
    audit,
    auth,
    bancos,
    dashboard,
    destinatarios,
    entregas,
    kardex,
    pagos,
    reportes,
    trazabilidad,
    usuarios,
    xmls,
)
from app.schemas.common import HealthCheckResponse
from app.utils.exceptions import (
    ConflictoUnicidad,
    EliminacionBloqueada,
    EntidadNoEncontrada,
    NoAutenticado,
    PermisoInsuficiente,
    SaldoInsuficiente,
    ValidacionDistribucion,
    ValidacionNegocio,
)

app = FastAPI(title="Control de Entregas", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=(
        ["*"] if settings.ENVIRONMENT == "development" else settings.cors_origins_list
    ),
    allow_credentials=settings.ENVIRONMENT != "development",
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(EntidadNoEncontrada)
async def entidad_no_encontrada_handler(
    request: Request, exc: EntidadNoEncontrada
) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": exc.message})


@app.exception_handler(ConflictoUnicidad)
async def conflicto_unicidad_handler(
    request: Request, exc: ConflictoUnicidad
) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": exc.message})


@app.exception_handler(ValidacionNegocio)
async def validacion_negocio_handler(
    request: Request, exc: ValidacionNegocio
) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": exc.message})


@app.exception_handler(SaldoInsuficiente)
async def saldo_insuficiente_handler(
    request: Request, exc: SaldoInsuficiente
) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": exc.message})


@app.exception_handler(EliminacionBloqueada)
async def eliminacion_bloqueada_handler(
    request: Request, exc: EliminacionBloqueada
) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": exc.message})


@app.exception_handler(NoAutenticado)
async def no_autenticado_handler(request: Request, exc: NoAutenticado) -> JSONResponse:
    return JSONResponse(status_code=401, content={"detail": exc.message})


@app.exception_handler(PermisoInsuficiente)
async def permiso_insuficiente_handler(
    request: Request, exc: PermisoInsuficiente
) -> JSONResponse:
    return JSONResponse(status_code=403, content={"detail": exc.message})


@app.exception_handler(ValidacionDistribucion)
async def validacion_distribucion_handler(
    request: Request, exc: ValidacionDistribucion
) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": exc.message})


app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(usuarios.router)
app.include_router(bancos.router)
app.include_router(destinatarios.router)
app.include_router(xmls.router)
app.include_router(kardex.router)
app.include_router(entregas.router)
app.include_router(pagos.router)
app.include_router(trazabilidad.router)
app.include_router(audit.router)
app.include_router(reportes.router)


@app.get("/", response_model=HealthCheckResponse)
async def health_check() -> HealthCheckResponse:
    return HealthCheckResponse(status="ok", version="0.1.0")
