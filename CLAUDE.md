# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Sistema web para control de entregas de productos a partir de facturas electrónicas SRI (XML).
Flujo principal: **XML SRI → Kardex FIFO → Entregas → Pagos**.
Monorepo con `backend/` (FastAPI + PostgreSQL) y `frontend/` (React + TypeScript).

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
cd backend && black --check app/ tests/   # format check; run without --check to fix
cd backend && mypy app/

# Security scan
cd backend && bandit -r app/

# Alembic migrations
cd backend && alembic upgrade head
cd backend && alembic revision --autogenerate -m "description"
cd backend && alembic downgrade -1   # test reversibility
```

Backend requires a `.env` file in `backend/` — copy from `.env.example`.
**All variables are required** — no defaults in code. Any missing variable causes startup failure.

- `DATABASE_URL`: `postgresql+asyncpg://...`
- `TEST_DATABASE_URL`: separate BD for tests — never the same as `DATABASE_URL`
- `JWT_SECRET_KEY`: min 32 chars. Generate: `python -c 'import secrets; print(secrets.token_urlsafe(48))'`
- `JWT_ALGORITHM`: e.g. `HS256`
- `JWT_EXPIRATION_MINUTES`: token lifetime in minutes (e.g. `60`)
- `JWT_REFRESH_LEEWAY_SECONDS`: silent-refresh window after expiry, 60–3600s (e.g. `900`)
- `CORS_ORIGINS`: JSON array string, e.g. `'["http://localhost:5173"]'`
- `ENVIRONMENT`: `development` | `production` — set to `development` locally for Swagger + open CORS
- `ADMIN_EMAIL`: admin user email
- `ADMIN_PASSWORD`: admin password (8+ chars, uppercase, digit, special char)
- `ENCRYPTION_KEY`: Fernet key for PII column encryption — generate with:
  `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
  **MUST be set. Never commit a real key. Startup fails with placeholder or invalid key.**
- `MAX_XML_UPLOAD_MB`: XML upload size limit in MB, 1–50 (e.g. `1`)
- `MAX_REQUEST_BODY_MB`: global request body size limit in MB, 1–50 (e.g. `2`)

Tests use `TEST_DATABASE_URL`. **IMPORTANT**: must point to a separate database from `DATABASE_URL`.

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
- **`utils/validaciones.py`** — Ecuadorian cédula/RUC validator (módulo 11 algorithm). Raises `ValidacionNegocio` on failure.
- **`utils/exceptions.py`** — Domain exception classes: `EntidadNoEncontrada` (404), `ConflictoUnicidad` (409), `ValidacionNegocio` (400), `SaldoInsuficiente` (400), `EliminacionBloqueada` (409), `PermisoInsuficiente` (403), `LimiteSolicitudes` (429).
- **`utils/encryption.py`** — `EncryptedString` SQLAlchemy `TypeDecorator` (Fernet transparent encrypt/decrypt), `hmac_hash(value)` for deterministic lookup hashes, and `mask_*` helpers for PII-safe audit payloads. Fails loud with `RuntimeError` on `InvalidToken` — no plaintext fallback.
- **`utils/rate_limit.py`** — DB-backed sliding-window rate limiter (async-only). State lives in `auth_attempts` table — survives Cloud Run scale-to-zero and multiple replicas. Two instances: `ip_login_limiter` (10 req/60s per IP, kind=`ip_login`) and `email_failure_tracker` (5 failures/15min per email, kind=`email_failure`). Cleaned in tests via `DELETE FROM auth_attempts` (autouse fixture in `conftest.py`).
- **`utils/uploads.py`** — `read_upload_with_limit(file, max_bytes)` reads an `UploadFile` in 64 KB chunks, aborting as soon as `max_bytes` is exceeded. `read_xml_upload_as_text(file)` applies the `MAX_XML_UPLOAD_MB` limit and decodes UTF-8.
- **`utils/request_meta.py`** — `get_client_ip(request)` returns the real client IP: first entry of `X-Forwarded-For` (Cloud Run sets this), falling back to `request.client.host`.
- **`templates/reportes/`** — Jinja2 + WeasyPrint HTML templates for PDF reports.
- **`migrations/`** — Alembic. Every model change requires a migration with both `upgrade` and `downgrade`.
- **`models/auth_attempt.py`** — Operational table for rate limiting. Does NOT inherit `AuditMixin` — no soft delete, no `created_by`. Rows are purged by pg_cron (`DELETE ... WHERE created_at < now() - interval '24 hours'`). See `backend/DEPLOY.md`.
- **`scripts/unlock_user.py`** — Emergency CLI to unblock a locked-out user directly against the DB: `python scripts/unlock_user.py <email>`. Requires `DATABASE_URL` in env or `backend/.env`.

### Frontend (`frontend/src/`)

- **`api/client.ts`** — Axios instance. Reads `VITE_API_URL`. Attaches JWT from `authStore` on every request. Redirects to `/login` on 401.
- **`store/authStore.ts`** — Zustand store (in-memory only, no `localStorage` persist) for `token` + `user`. Token is lost on page refresh — intentional for security (A1).
- **`store/uiStore.ts`** — Zustand store for UI-only state (sidebar open, etc.).
- **`routes/index.tsx`** — React Router v7 browser router. `ProtectedRoute` wraps authenticated sections. Pages are lazy-loaded.
- **`features/[feature-name]/`** — Feature-driven architecture. Each feature owns its `components/`, `hooks/`, `types/`, and `index.ts`. All async logic and API calls go in custom hooks inside `features/`.
- **`pages/`** — Dumb pages: no state logic, no direct API calls. They compose feature components.
- **`components/ui/`** — shadcn/ui primitives (never domain logic).
- **`components/custom/`** — Reusable visual components shared across features (not domain-specific).
- **`shared/`** — Logic shared across two or more features: utilities, types, formatters.

### Registered Features (11 domains)

`auth`, `usuarios`, `bancos`, `destinatarios`, `xmls`, `kardex`, `entregas`, `pagos`,
`trazabilidad`, `auditoria`, `reportes`

## Critical Business Rules

- **FIFO Kardex**: Stock NEVER goes negative. Consumption always takes from oldest lots first.
- **Soft delete**: All domain queries filter `is_active=True` by default. Deletion via `AuditMixin.soft_delete(usuario_id)`.
- **Delivery reversal**: Blocked if the delivery has payments. Without payments, FIFO reversal must be exact using `entrega_item_fifo_detalle`.
- **Payment reversal**: Must restore `saldo_pendiente` on each affected delivery.
- **XML**: `clave_acceso` must be unique; only `ambiente=2` (production) is accepted.
- **Payments**: `SUM(monto_aplicado)` must equal `valor_total`; amount per delivery cannot exceed `saldo_pendiente`.
- **Traceability**: The chain XML ↔ Kardex ↔ Entrega ↔ Pago must remain navigable in both directions. Trazabilidad endpoints include soft-deleted entities intentionally to show full history.

## Security

### Implemented measures

- **RLS**: All 15 public tables have `ENABLE ROW LEVEL SECURITY`. No permissive policies are defined — the backend connects as `postgres`/`service_role` which bypasses RLS; `anon`/PostgREST access is deny-all by default.
- **Password policy**: Minimum 8 characters, 1 uppercase, 1 digit, 1 special character. Enforced via Pydantic `@field_validator` in `UsuarioCreate` and `PasswordUpdate`.
- **JWT in memory**: Frontend stores token only in Zustand memory (no `localStorage` / `persist`). Prevents XSS token theft. Re-login required after page refresh — acceptable for 3–4 internal users. (A1)
- **JWT expiration**: 60-minute access tokens. Silent refresh allowed within a 15-minute leeway window (`JWT_REFRESH_LEEWAY_SECONDS=900`, max 3600). Frontend queues concurrent requests during refresh. (M4)
- **JWT key strength**: `JWT_SECRET_KEY` must be ≥ 32 characters. Validated at startup; fails loud if shorter. (M3)
- **Login rate limiting**: IP-based (10 req/60s via `ip_login_limiter`) applied in the router; email-based (5 failures/15min via `email_failure_tracker`) applied in `auth_service` — resets on successful login. Both raise `LimiteSolicitudes` → HTTP 429. State persisted in PostgreSQL `auth_attempts` table — survives Cloud Run restarts and multiple replicas. (A4)
- **Real client IP**: `get_client_ip(request)` extracts the first entry of `X-Forwarded-For` (set by GCP load balancer). The rate limiter and audit log use this, not the proxy IP. Dockerfile starts uvicorn with `--proxy-headers --forwarded-allow-ips *`. (A5)
- **Admin unlock endpoint**: `POST /usuarios/{id}/desbloquear` (admin only) clears `auth_attempts` for a user's email and writes to `audit_log` with `accion='UNLOCK_USER'`. Emergency CLI: `python scripts/unlock_user.py <email>`. (A4-bis)
- **XML parser hardened**: `xml.etree.ElementTree` replaced by `defusedxml` — blocks billion-laughs entity expansion, external DTD loading, and other XML DoS vectors. (A3)
- **XML upload size limit**: `read_xml_upload_as_text()` reads in 64 KB chunks and aborts immediately when `MAX_XML_UPLOAD_MB` is exceeded. No full-file load before validation. (A2)
- **Global request body limit**: `limit_request_size` middleware checks `Content-Length` before any processing and returns HTTP 413 if `MAX_REQUEST_BODY_MB` is exceeded. (M6)
- **Security headers**: `_SECURITY_HEADERS` dict applied to every response: `Strict-Transport-Security`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`, and `Content-Security-Policy: default-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'`. (M2)
- **Fail-safe ENVIRONMENT**: `ENVIRONMENT` has no default in code. `_IS_DEVELOPMENT = settings.ENVIRONMENT.strip().lower() == "development"` gates Swagger, open CORS, and debug logging — anything not explicitly `"development"` is treated as production. (B4)
- **Config validation at startup**: `ENCRYPTION_KEY` must be a valid Fernet key (not placeholder); `JWT_SECRET_KEY` must be ≥ 32 chars; `JWT_REFRESH_LEEWAY_SECONDS` must be 60–3600; `MAX_XML_UPLOAD_MB` and `MAX_REQUEST_BODY_MB` must be 1–50. Any violation aborts startup with a clear error. (B3, M3, M4, M6)
- **`audit_log` immutability**: PostgreSQL `BEFORE DELETE` and `BEFORE UPDATE` triggers (`trg_audit_log_no_delete`, `trg_audit_log_no_update`) raise an exception on any attempt to modify the table directly.
- **PII column encryption**: `destinatarios` (identificacion, nombre, direccion, telefono, email), `pagos` (nombre_titular), `entregas` (snap_identificacion, snap_nombre, snap_direccion, snap_telefono) are stored encrypted via `EncryptedString` (Fernet). Decryption fails loud with `RuntimeError` on `InvalidToken` — no plaintext fallback. (B2)
- **Deterministic lookup**: `destinatarios.identificacion_hash` holds an HMAC-SHA256 of the plaintext `identificacion`. All WHERE queries on `identificacion` use the hash column; the encrypted column is display-only.
- **Audit log PII masking**: Service functions pass `_audit_dict()` results (using `mask_*` helpers) to `set_audit_payload` instead of raw field values, so the audit log never stores plaintext PII.
- **cryptography declared**: `cryptography>=42.0,<46` is an explicit dependency in `requirements.txt`, not just a transitive dependency of WeasyPrint. (B1)

### Migration chain (current HEAD)

```text
... → 9f2a1b4c3d55
      → a1b2c3d4e5f6  (enable RLS on all tables)
      → b2c3d4e5f6a7  (audit_log immutable triggers)
      → c3d4e5f6a7b8  (widen PII columns to TEXT + identificacion_hash)
      → d4e5f6a7b8c9  (add auth_attempts table + idx_auth_attempts_lookup)  ← HEAD
```

After applying `c3d4e5f6a7b8` on a database with existing plaintext data, run:

```bash
cd backend && python scripts/encrypt_existing_data.py
```

For production deployment and pg_cron setup for `auth_attempts` cleanup, see `backend/DEPLOY.md`.

### Encrypted field conventions

- **Never use encrypted columns in SQL WHERE clauses** — Fernet is non-deterministic; use the `_hash` companion column for equality, or fetch all and filter in Python for substring search.
- **`snap_nombre` substring search** (`obtener_pendientes`) fetches all from DB, then filters in Python after decryption. Acceptable because the result set is bounded by active deliveries with outstanding balance.
- **Adding a new encrypted field**: use `EncryptedString` as the column type in the model; if it needs equality lookup, add a `_hash VARCHAR(64)` companion column populated with `hmac_hash()`.

## Conventions

- **Language**: Business logic documentation and variable names for domain concepts in Spanish. API routes, code structure, and technical identifiers in English.
- **Transactions**: Services use `async with session.begin_nested()`. The `get_db` dependency commits on success and rolls back on failure. Never use `session.begin()` inside a router or service — `get_db` already starts a transaction via SQLAlchemy autobegin, and calling `begin()` again raises `InvalidRequestError`.
- **Audit**: The `@auditar` decorator is the only place audit writes happen — never inline.
- **Backend is source of truth**: TypeScript/Zod types in the frontend MUST mirror Pydantic schemas. Never the reverse.
- **Task order when implementing a feature**: Contract (Pydantic + Zod) → Migrations → Backend → Frontend → Security → Tests.
- **mypy**: Strict mode (`strict = true`). Every new module must pass `mypy app/`.
- **Monetary values**: Always `NUMERIC(12,2)` or `NUMERIC(12,4)` in PostgreSQL, `Decimal` in Pydantic, `z.number()` in Zod. Never `float`.

## Test Setup (Supabase + PgBouncer)

Tests run against Supabase (PgBouncer in transaction mode). The conftest uses a special pattern
to avoid connection pool conflicts and support prepared-statement-less connections:

```python
# tests/conftest.py pattern
create_async_engine(..., poolclass=NullPool, connect_args={"statement_cache_size": 0})

# Each test gets a fresh session over the same connection, rolled back at the end:
AsyncSession(conn, join_transaction_mode="create_savepoint")
```

This gives cross-request visibility within a test (same connection) with full rollback at test end.

All httpx test requests share IP `"testclient"` via `ASGITransport`. An `autouse=True` async fixture
`reset_rate_limiters()` in `conftest.py` runs `DELETE FROM auth_attempts` before each test to prevent
cross-test rate-limit bleed. Uses `DELETE` (not `TRUNCATE`) because TRUNCATE holds `ACCESS EXCLUSIVE`
for the entire transaction, which would deadlock the autonomous-session INSERTs from `ip_login_limiter`.

The rate limiter uses an autonomous session pattern for IP checks: `ip_login_limiter.check_and_record(session, ip)` commits independently of the caller's transaction so IP attempt rows survive a failed-login rollback. Email failure rows (`email_failure_tracker.record_failure`) use the caller's session and are rolled back on failed logins — tests that need email failure state must insert directly via `db_session.add(AuthAttempt(...))` and `await db_session.flush()`.

## OpenSpec Workflow

Changes to this codebase follow the OpenSpec `spec-driven` schema defined in `openspec/`.

```text
openspec/
├── config.yaml                      # Global context + per-artifact rules
├── schemas/spec-driven/
│   ├── schema.yaml                  # Artifact definitions + dependency chain
│   └── templates/                   # proposal.md, design.md, specs.md, tasks.md
├── specs/{domain}/spec.md           # Consolidated live spec per domain (source of truth)
└── changes/archive/{change}/        # Archived changes (one per feature phase)
    ├── .openspec.yaml               # Schema + change name metadata
    ├── proposal.md
    ├── design.md
    ├── specs/{domain}.md            # Delta spec for this change only
    └── tasks.md
```

**Artifact dependency chain**: `proposal` → `specs` + `design` → `tasks` → `apply`

**Phase order inside `tasks.md`** (non-negotiable):

- 0: Contracts (Pydantic + Zod)
- 1: Migrations (Alembic)
- 2: Backend (services + routers)
- 3: Frontend (hooks + components + pages)
- 4: Security (ruff, mypy, bandit, eslint)
- 5: Tests

Use `/opsx:propose`, `/opsx:explore`, `/opsx:apply`, and `/opsx:archive` slash commands to
work within this workflow.

## CI Pipeline (`.github/workflows/ci.yml`)

All quality checks are **enforced** — no `|| true` suppression. A failing check blocks the pipeline.

### Backend job checks (in order)

1. `ruff check backend/app backend/tests` — style + unused imports
2. `black --check backend/app backend/tests` — format compliance
3. `mypy app` — strict type checking
4. `bandit -r backend/app` — security scan (MEDIUM/HIGH fail the build)
5. `pytest -q` — full test suite

### Frontend job checks (in order)

1. `npm run lint` — ESLint
2. `npm run typecheck` — `tsc --noEmit`
3. `npm run build` — production build
4. `npm test` — Vitest suite

### GitHub secret required

`CI_ADMIN_PASSWORD` must be set in **Settings → Secrets and variables → Actions** before the
backend tests can authenticate as admin. The workflow falls back to `'Admin1234!'` if unset
(for forks/PRs without secrets access), but production CI must always have the secret configured.

## Known Pending Items

- **DB integrity triggers**: `BEFORE DELETE` triggers on `entregas` and `entrega_items` tables
  to block direct SQL deletes (bypassing soft delete). Planned as a future OpenSpec change
  (`proteccion-integridad-bd`).
- **M5 — JSON structured logging**: Deferred by YAGNI. Needed for distributed log correlation
  in production. Postponed until the system has enough traffic to justify it.
- **pg_cron cleanup of `auth_attempts`**: Must be configured manually in Supabase SQL Editor
  (one-time setup). See `backend/DEPLOY.md` for the exact `cron.schedule` call. Until configured,
  the table grows unboundedly (low volume in practice, but should be addressed before scaling).
- **Frontend security tests**: A4-bis UI (DesbloquearButton), A1 (JWT in memory) — validated
  manually only. Vitest coverage deferred.
