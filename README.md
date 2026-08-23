# 🔐 AuthForge — Production-Ready Auth Platform

> FastAPI + PostgreSQL + Redis + Docker + RBAC + JWT rotation + audit logging. Built for SDE portfolio / production use.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.139-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-blue)
![Redis](https://img.shields.io/badge/Redis-7-red)
![Docker](https://img.shields.io/badge/Docker-Multi--Stage-blue)
![Pytest](https://img.shields.io/badge/Pytest-13%2B-success)
![CI](https://github.com/aaryaa135/AuthForge/actions/workflows/ci.yml/badge.svg)
![Coverage](https://img.shields.io/badge/coverage-70%25-brightgreen)
![License](https://img.shields.io/badge/License-MIT-yellow)

**Live Docs (local):** `http://localhost:8000/docs` · **Health:** `http://localhost:8000/health`

---

## TL;DR

Modular auth service you can drop into any product: registration, email verification, login (rate-limited, blacklisted JWT), refresh rotation, RBAC (Admin/User), password reset/change, Redis caching, audit logs, paginated admin APIs, security headers + request IDs, typed config, migrations, and CI that actually runs tests.

```bash
cp .env.example .env   # set JWT_SECRET_KEY (>=32 chars)
docker compose up --build -d
make migrate seed      # alembic upgrade + seed roles
make test              # pytest with fakeredis fallback
```

---

## ✨ Features

| Domain | Capabilities |
|--------|--------------|
| **Auth** | Register, Login (OAuth2 password flow), JWT access (15m) + refresh (7d) rotation, Logout (Redis blacklist by `jti`), `GET /me` |
| **Account** | Email verification (`token_urlsafe` 24h), resend, forgot/reset (1h), change-password (auth) |
| **AuthZ** | RBAC via `require_role("Admin")`, `role` on `User`, protected `/users`, `/audit` |
| **Security** | bcrypt, JWT `jti` + `type` validation, Redis blacklist, atomic fixed-window rate limit (5/min login), security headers (HSTS, nosniff, DENY), CORS `CORS_ORIGINS`, secret validators |
| **Performance** | Redis `user:email/*` cache (5m), DB `Index` on `email/username/token/created_at`, pagination `?page&page_size`, SQLAlchemy pool `10/20` |
| **Observability** | Request ID `X-Request-ID` on every response, structured logs (JSON in prod), `AuditLog` for register/login/logout/password events, `/health` |
| **DevOps** | Multi-stage non-root Docker + healthcheck, `docker-compose` with Postgres 17 + Redis 7 healthchecks, `Makefile`, `pre-commit` (ruff/black), GitHub Actions (postgres+redis services, migrations, `pytest --cov`), `pyproject.toml` |

---

## 🏗 Architecture

```
Client ──▶ FastAPI (CORS → RequestID → SecurityHeaders → Auth)
              ├─▶ AuthService ─┬─▶ PostgreSQL (users, roles, refresh/email/reset_tokens, audit_logs)
              │                ├─▶ Redis (blacklist:{jti}, login:{id}, user:{email|username})
              │                └─▶ EmailProvider (Console / pluggable Resend/SMTP)
              └─▶ UserService / AuditService
```

**DB Indexes:** `users.email`, `users.username`, `refresh_tokens.token/user_id`, `*_tokens.token`, `audit_logs.user_id/action/created_at`.

**Request lifecycle:** `OAuth2PasswordBearer` → `decode_token` → `type=="access"` → `jti` not blacklisted → `User.is_active` → `require_role` → handler → `X-Request-ID` + security headers.

---

## 🛠 Tech Stack

| Layer | Tech | Purpose |
|-------|------|---------|
| **Runtime** | Python 3.11 · FastAPI 0.139 · Uvicorn · Pydantic v2 | Sync API, validation, OpenAPI |
| **Database** | PostgreSQL 17 · SQLAlchemy 2.0 · Alembic 1.18 · `psycopg2-binary` | `users/roles/tokens/audit`, migrations, pool 10/20 |
| **Cache** | Redis 7/8 · `redis-py` · `fakeredis` | Blacklist `jti`, rate limit 5/min, `user:*` cache |
| **Auth** | `python-jose` HS256 · `passlib[bcrypt]` · `token_urlsafe` | JWT `jti/type` rotation, email/reset tokens |
| **Quality** | `ruff 0.15` · `black 23.11` · `pytest 9.1 + cov 70%` · `pre-commit` | Lint + format + CI |
| **Infra** | Docker multi-stage (non-root) · `docker compose` · GitHub Actions (pg+redis) | Dev & prod parity |
| **Observability** | `X-Request-ID` · Security headers · `AuditLog` · `/health` | Trace + audit |

> **GitHub About →** See [`.github/ABOUT.md`](./.github/ABOUT.md) for exact **Description + 14 Topics** to paste into **Settings → About** gear icon.

---

## 📂 Project Structure

```
app/
  main.py                # FastAPI app, middleware (CORS/RequestID/Security), legacy /users → /api/v1 rewrite
  core/  config.py       # 12-factor settings + validators (secret>=32, env)
         jwt.py          # create_access/refresh, decode (jti/type)
         security.py     # hash/verify
         dependencies.py # require_role → shared.get_current_user
         middleware.py   # RequestID + SecurityHeaders
         exceptions.py   # AppException + validation/500 handlers
         rate_limit.py   # atomic INCR+TTL
         logger.py       # JSON in prod
  cache/ client.py keys.py service.py
  db/    base.py session.py models.py  # pool_size 10/20
  modules/
    auth/  models/schemas/repository/service/routes/dependencies
    users/ models/schemas/repository/service/routes  # paginated
    roles/ models/repository
    audit/ models/schemas/repository/service/routes  # paginated
  providers/ base/console/factory
  shared/ dependencies.py  # canonical get_current_user (blacklist+is_active)
          pagination.py    # PaginationParams + PaginatedResponse
          responses.py
alembic/ versions/  # 5 migrations + indexes
tests/   conftest.py # fakeredis fallback  | test_*.py
scripts/ seed_roles.py seed_admin.py
pyproject.toml  Makefile  .pre-commit-config.yaml  docker-compose.yml  Dockerfile
```

---

## 🔑 Auth Flow

```
Register → EmailVerification (24h) → Login → {access, refresh}
    → GET /api/v1/auth/me (Bearer access) → POST /refresh (rotation) → POST /logout (blacklist jti)
    → forgot → reset (1h) → change-password (auth)
```

---

## 🚀 Getting Started (local, no Docker)

```bash
git clone https://github.com/aaryaa135/AuthForge.git && cd AuthForge
python -m venv .venv
# Windows: .venv\Scripts\activate  | Linux: source .venv/bin/activate
pip install -r requirements.txt && pip install -e ".[dev]"
pre-commit install

cp .env.example .env   # edit DATABASE_URL, JWT_SECRET_KEY, REDIS_HOST
alembic upgrade head
python scripts/seed_roles.py
# optional: python scripts/seed_admin.py  (needs TEST_ADMIN_EMAIL/PASSWORD)

uvicorn app.main:app --reload
# docs: http://localhost:8000/docs
```

**Make shortcuts:**

```bash
make install lint format test run migrate seed docker-up docker-down clean
```

---

## 🐳 Docker (recommended)

```bash
cp .env.example .env
docker compose up --build -d   # api:8000  postgres:5433  redis:6379
docker compose exec api alembic upgrade head
docker compose exec api python scripts/seed_roles.py
curl http://localhost:8000/health
make test   # or USE_FAKE_REDIS=1 pytest
```

`Dockerfile` is multi-stage, non-root `appuser (10001)`, `HEALTHCHECK curl /health`, `PYTHONPATH=/app`.

---

## 🧪 Testing

```bash
pytest -v                          # requires Postgres+Redis (docker compose up)
USE_FAKE_REDIS=1 pytest -v         # no infra needed (fakeredis)
pytest --cov=app --cov-report=term-missing  # fail_under 70 (pyproject.toml)
```

13 integration tests: `register`, `login`, `refresh rotation`, `logout`, `blacklist`, `RBAC (/users)`, `rate limit (429)`, `cache`, `redis`, `forgot-password`, `change-password`. CI runs them with real `postgres:17` + `redis:7` services.

---

## 📬 API Reference (v1)

All versioned under `/api/v1`; legacy `/users`, `/audit` still work via rewrite middleware (deprecated).

**Auth ` /api/v1/auth`**

| Method | Endpoint | Auth | Notes |
|--------|----------|------|-------|
| POST | `/register` | no | `201` `UserResponse` |
| POST | `/login` | no | `OAuth2PasswordRequestForm`, 5/min rate limit |
| POST | `/refresh` | no | body `refresh_token` → rotation |
| POST | `/logout` | Bearer | body `refresh_token` + `Authorization` access → blacklist `jti` |
| GET | `/me` | Bearer | current user |
| POST | `/change-password` | Bearer | `current_password` + `new_password` |
| POST | `/forgot-password` | no | always `200` (no enumeration) |
| POST | `/reset-password` | no | `token` + `new_password` |
| GET | `/verify-email?token=` | no | 24h window |
| POST | `/resend-verification` | no | `email` |

**Users ` /api/v1/users` (Admin)**

| Method | Endpoint | Auth | Query |
|--------|----------|------|-------|
| GET | `/` | Admin | `?page=1&page_size=20` → `PaginatedResponse[UserResponse]` |
| GET | `/{user_id}` | Admin | |
| PATCH | `/{user_id}/role` | Admin | `{role: "Admin"\|"User"\|"Manager"}` |
| PATCH | `/{user_id}/status` | Admin | `{is_active: bool}` |

**Audit ` /api/v1/audit` (Admin)**

| Method | Endpoint | Query |
|--------|----------|-------|
| GET | `/` | `?page&page_size` → `PaginatedResponse[AuditLogResponse]` |

**Ops**

| Method | Endpoint |
|--------|----------|
| GET | `/` |
| GET | `/health` → `{status, application, version, environment}` |

Swagger: `/docs` · ReDoc: `/redoc` · OpenAPI: `/openapi.json`

---

## 🔒 Security Checklist

- [x] `JWT_SECRET_KEY` validator `>=32` chars, rejects placeholder
- [x] `bcrypt` hashing, `jti` per token, `type` check, `exp` enforcement
- [x] Redis blacklist on logout with `remaining_ttl = exp - now`
- [x] `is_active` + optional `require_email_verification` gate on login
- [x] Atomic rate limit (`INCR` + `EXPIRE` pipeline), no `GET-set` race
- [x] `X-Request-ID`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, HSTS on https
- [x] Pydantic `EmailStr`, `Field(min_length)`, `CORS_ORIGINS` allowlist
- [x] No `.env` in git, `DATABASE_URL` sanitized in example

---

## ⚙️ Configuration

See `.env.example` (16 vars). Key: `APP_NAME`, `APP_VERSION`, `ENVIRONMENT` (`development/test/staging/production`), `DATABASE_URL` (or `DB_HOST/PORT/NAME/USER/PASSWORD`), `JWT_SECRET_KEY/ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS`, `REDIS_HOST/PORT/DB/PASSWORD`, `FRONTEND_URL`, `CORS_ORIGINS`, `REQUIRE_EMAIL_VERIFICATION`, `LOG_LEVEL`. Validated at startup.

---

## 📘 Code Guide

See [`GUIDE.md`](./GUIDE.md) — every file explained (`app/main.py:24`, `app/core/*`, `app/modules/*`, `alembic/*`, `tests/*`) with flows, security matrix, and how to extend.

---

# 📈 CI/CD

`.github/workflows/ci.yml` on `push/PR → main/develop/feature/**`: `ruff check` → `black --check` → `alembic upgrade head` → `seed_roles` → `pytest -v --tb=short` (with `postgres:17` + `redis:7` healthchecks). No secrets in logs.

---

## 🗺 Roadmap

- [x] Auth, RBAC, JWT rotation, blacklist, rate limit, email flows, audit, cache, pagination
- [ ] Token cleanup cron (expired `refresh_tokens`)
- [ ] Admin dashboard API (search/filter)
- [ ] Frontend (Next.js) + e2e
- [ ] Deploy (Fly.io / Render) + observability (Sentry, Prometheus)

---

## 🤝 Contributing

See `CONTRIBUTING.md` + `make lint/format/test`. Conventional commits, PR must pass CI.

---

## 📄 License

MIT
