# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Sistema web para control de entregas de productos a partir de facturas electrónicas SRI (XML). Flujo principal: **XML SRI → Kardex FIFO → Entregas → Pagos**. Monorepo con `backend/` (FastAPI) y `frontend/` (React).

## Backend Commands

All backend commands run from `backend/` with the virtualenv active (`.venv/`).

```bash
# Activate virtualenv
source backend/.venv/bin/activate

# Run dev server
cd backend && uvicorn app.main:app --reload --port 8000

# Run all tests
cd backend && pytest

# Run a single test file
cd backend && pytest tests/test_fifo.py -v

# Run a single test by name
cd backend && pytest tests/test_fifo.py::test_name -v

# Linting & type checking
cd backend && ruff check app/ tests/
cd backend && mypy app/

# Alembic migrations
cd backend && alembic upgrade head
cd backend && alembic revision --autogenerate -m "description"
```

Backend requires a `.env` file in `backend/` — copy from `.env.example`:
- `DATABASE_URL`: `postgresql+asyncpg://...`
- `JWT_SECRET_KEY`: random secret
- `ENVIRONMENT`: `development` | `production`

Tests use `TEST_DATABASE_URL` env var (defaults to `postgresql+asyncpg://postgres:postgres@localhost:5432/control_entregas_test`).

## Frontend Commands

All frontend commands run from `frontend/`.

```bash
# Dev server (http://localhost:5173)
cd frontend && npm run dev

# Build
cd frontend && npm run build

# Type check
cd frontend && npm run typecheck

# Lint
cd frontend && npm run lint

# Run all tests
cd frontend && npm test

# Run tests in watch mode
cd frontend && npm run test:watch
```

Frontend requires `VITE_API_URL` env var pointing to the backend (e.g., `http://localhost:8000`).

## Architecture

### Backend (`backend/app/`)

- **`main.py`** — FastAPI app, CORS, global exception handlers mapping domain exceptions to HTTP status codes.
- **`config.py`** — Pydantic `Settings` loaded from `.env`.
- **`database.py`** — SQLAlchemy async engine + session factory.
- **`routers/`** — HTTP layer only. Routers receive requests and delegate to services — no business logic here.
- **`services/`** — All business logic lives here. Services are called by routers and decorated with `@auditar`.
- **`models/`** — SQLAlchemy ORM models. All domain models MUST inherit from `AuditMixin` (adds `created_at`, `updated_at`, `deleted_at`, `is_active`, and `soft_delete()` method).
- **`schemas/`** — Pydantic v2 models for request/response contracts. `common.py` has shared types (`PaginatedResponse`, `ApiErrorResponse`).
- **`dependencies/`** — FastAPI `Depends()` providers: `auth.py` (JWT + role check), `db.py` (async session).
- **`utils/fifo.py`** — Pure function FIFO cost calculator. No DB dependency; directly testable. `calcular_consumo_fifo(lotes, cantidad)` raises `SaldoInsuficiente` if stock is insufficient.
- **`utils/audit.py`** — `@auditar(accion, entidad)` decorator. Writes to `audit_log` after the decorated service function. Requires `session`, and optionally `entidad_id`, `usuario_id`, `payload_antes`, `payload_despues` as kwargs.
- **`utils/validaciones.py`** — Ecuadorian cédula/RUC validator using modulo-10 algorithm. Raises `ValidacionNegocio` on failure.
- **`utils/exceptions.py`** — Domain exception classes: `EntidadNoEncontrada` (404), `ConflictoUnicidad` (409), `ValidacionNegocio` (400), `SaldoInsuficiente` (400), `EliminacionBloqueada` (409), `PermisoInsuficiente` (403).
- **`migrations/`** — Alembic. Every model change requires a migration with both `upgrade` and `downgrade`.

### Frontend (`frontend/src/`)

- **`api/client.ts`** — Axios instance. Reads `VITE_API_URL`. Attaches JWT from `authStore` on every request. Redirects to `/login` on 401.
- **`store/authStore.ts`** — Zustand store (persisted to localStorage) for `token` + `user`. Only session state goes here.
- **`store/uiStore.ts`** — Zustand store for UI-only state (sidebar open, etc.).
- **`routes/index.tsx`** — React Router v7 browser router. `ProtectedRoute` wraps authenticated sections. Pages are lazy-loaded.
- **`features/[feature-name]/`** — Feature-driven architecture. Each feature owns its `components/`, `hooks/`, and `types/`. All async logic and API calls go in custom hooks inside `features/`.
- **`pages/`** — Dumb pages: no state logic, no direct API calls. They compose feature components.
- **`components/ui/`** — shadcn/ui primitives (never domain logic).
- **`components/custom/`** — Reusable visual components shared across features (not domain-specific).
- **`shared/`** — Logic shared across two or more features: utilities, types, formatters.

## Critical Business Rules

- **FIFO Kardex**: Stock NEVER goes negative. Consumption always takes from oldest lots first.
- **Soft delete**: All domain queries filter `is_active=True` by default. Deletion via `AuditMixin.soft_delete(usuario_id)`.
- **Delivery reversal**: Blocked if the delivery has payments. Without payments, FIFO reversal must be exact using `entrega_item_fifo_detalle`.
- **Payment reversal**: Must restore `saldo_pendiente` on each affected delivery.
- **XML**: `clave_acceso` must be unique; only `ambiente=2` (production) is accepted.
- **Payments**: `SUM(monto_aplicado)` must equal `valor_total`; amount per delivery cannot exceed `saldo_pendiente`.

## Conventions

- **Language**: Business logic documentation and variable names for domain concepts in Spanish. API routes, code structure, and technical identifiers in English.
- **Transactions**: Every multi-table operation uses `async with session.begin()`. Full rollback on failure.
- **Audit**: The `@auditar` decorator is the only place audit writes happen — never inline.
- **Backend is source of truth**: TypeScript/Zod types in the frontend MUST mirror Pydantic schemas. Never the reverse.
- **Task order when implementing a feature**: Contract (Pydantic + Zod) → Migrations → Backend → Frontend → Security → Tests.
- **mypy**: Strict mode (`strict = true`). Every new module must pass `mypy app/`.
