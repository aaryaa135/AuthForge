# AuthForge

**Production-ready Authentication Platform** — FastAPI + PostgreSQL + Redis + Docker + JWT rotation + RBAC + audit logging

AuthForge is a modular-authentication platform designed for SaaS products, internal tools, and developer prototypes. It provides a complete authentication stack out of the box, including user registration, login, password management, email verification, JWT access/refresh token rotation, TOTP two-factor authentication, role-based access control, API key management, and comprehensive audit logging.

The system is architected as a **modular monolith** with vertical feature modules (`auth`, `users`, `roles`, `audit`) and horizontal cross-cutting concerns (`core`, `cache`, `providers`, `shared`). Every feature follows the pathway `Router → Service → Repository → DB/Redis`.


## Problem Statement

Modern applications require secure, production-ready authentication without the overhead of stitching together disparate libraries. AuthForge solves this by providing a complete, integrated authentication platform with:

- **Secure password handling** via bcrypt (passlib)
- **JWT-based session management** with token rotation and revocation
- **Progressive account lockout** against brute-force attacks
- **Two-factor authentication** (TOTP) with backup codes
- **Role-based access control** (RBAC) for endpoint protection
- **Audit logging** for security and compliance
- **Email verification** and **password reset** flows
- **Service account** authentication via API keys

AuthForge is intended for developers who need a battle-tested authentication foundation without the complexity of building one from scratch, and for teams looking to integrate a modular, extensible auth platform into existing FastAPI services.


## Key Features (Implemented)

- **User registration** with email verification token
- **Login** with email or username, progressive lockout after 5 failed attempts (15-min lock)
- **JWT access tokens** (15 min expiry) and **refresh tokens** (7 day expiry) with JTI per token
- **Token rotation** on refresh — old tokens are revoked, new family is established
- **Logout** revokes the entire refresh token family and blacklists the access token JTI in Redis
- **Password change** and **forgot/reset password** flows (all sessions revoked on password change)
- **Email verification** via time-limited tokens
- **TOTP 2FA** with secret key, QR code, and 8 single-use backup codes
- **Role-Based Access Control** (Admin, Manager, User roles)
- **API key management** for service accounts/machine-to-machine auth (hashed key value, scopes, expiration)
- **Audit logging** for: REGISTER, LOGIN, LOGOUT, PASSWORD_RESET, PASSWORD_CHANGE, TOTP events, API_KEY_CREATED/REVOKED
- **Redis-based rate limiting** (5 login attempts/60s atomic INCR+EXPIRE)
- **CORS** configuration via `CORS_ORIGINS` environment variable
- **Security headers** (X-Content-Type-Options, X-Frame-Options, CSP, HSTS)


## Technology Stack

| Layer | Technology |
|---|---|
| **Language** | Python 3.11 |
| **Framework** | FastAPI 0.139.0 |
| **ORM** | SQLAlchemy 2.0.51 (DeclarativeBase) |
| **Database** | PostgreSQL 17 |
| **Cache/Session** | Redis 7 |
| **Password Hashing** | bcrypt 4.0.1 via passlib 1.7.4 |
| **JWT** | python-jose 3.5.0 (HS256) |
| **2FA** | pyotp 2.9.0, QR code via qrcode[pil] |
| **Email** | console (dev), SMTP, or Resend API |
| **Validation** | Pydantic 2.13.4 (v2 models) |
| **Static/Lint** | ruff 0.15.20, black 23.11.0 |
| **Testing** | pytest 9.1.1, pytest-cov 7.1.0 |
| **Container** | Docker multi-stage build, docker-compose.yml |


## Architecture Overview

AuthForge is a **modular monolith** with vertical feature modules and horizontal cross-cutting concerns:

```
Client → FastAPI (app/main.py)
  → Middleware: CORS → RequestID → SecurityHeaders → LegacyPathRewrite
  → Router (app/modules/*/routes.py)
    → Service (business rules, hashing, token rotation)
      → Repository (SQLAlchemy queries + Redis ops)
        → PostgreSQL + Redis + EmailProvider
  → Middleware Response (X-Request-ID, security headers) → Client
```

**Key invariants:**
- JWT `access` token: 15 min, `refresh` token: 7 days, each has `jti` (UUID) + `type` + `sub` (user.id)
- Logout blacklists `jti` in Redis with `TTL = exp - now`
- Rate limit is atomic `INCR + EXPIRE` (5 login attempts / 60s)
- All list endpoints are paginated
- All models use `TimestampMixin` (created_at, updated_at)


## Project Folder Structure

```
AuthForge/
├── app/
│   ├── main.py                                          # FastAPI app factory, middleware, routers
│   ├── core/                                            # Cross-cutting: config, jwt, security, middleware, exceptions, rate_limit, dependencies
│   ├── cache/                                           # Redis wrapper + keys + circuit breaker
│   ├── db/                                              # SQLAlchemy base, session, model registry
│   ├── modules/                                         # Vertical feature modules
│   │   ├── auth/                                        # Registration, login, 2FA, tokens, API keys
│   │   ├── users/                                       # Admin user management
│   │   ├── roles/                                       # Role definitions + CRUD
│   │   └── audit/                                       # Audit logging
│   ├── providers/                                       # Email: console/SMTP/Resend
│   └── shared/                                          # Canonical dependencies, pagination, responses
├── alembic/                                             # Database migrations (alembic.ini + versions)
├── .github/workflows/                                    # CI/CD pipelines
├── docker-compose.yml                                   # PostgreSQL + Redis + API services
├── Dockerfile                                           # Multi-stage hardened container
├── pyproject.toml                                       # Project config, lint/test settings
├── requirements.txt                                     # Python dependencies
├── Makefile                                             # Convenience commands (lint, test, format, run, migrate, seed, docker-*)
├── .env.example                                         # Environment variable template
├── .env                                                 # Local overrides (gitignored)
└── tests/                                               # Integration tests (13 test files)
```


## Authentication Workflow

### Register → Verify → Login → Access → Refresh → Logout

1. **`POST /api/v1/auth/register`** — Client sends `{email, username, password}`. `AuthService.register_user` checks uniqueness, creates User with `role=User`, `is_verified=False`, generates `EmailVerificationToken(token_urlsafe(32), now+24h)`, sends verification email, returns `201`.

2. **`GET /api/v1/auth/verify-email?token=xxx`** — Marks `user.is_verified = True`. After verification, login is permitted if `require_email_verification` is enabled.

3. **`POST /api/v1/auth/login``** — Client sends `OAuth2PasswordRequestForm(username/email, password)`. Rate limit: 5 attempts/60s per identifier. `AuthService.login_user` looks up user, checks `is_active`, verifies bcrypt password, checks email verification if required. If 2FA is enabled and verified → stores `2fa_pending:{user_id}` in Redis (5 min TTL), returns `two_factor_required: true`. Otherwise `_issue_tokens(user)` creates access (15min) + refresh (7d) JWTs + persists `RefreshToken` row.

4. **`GET /api/v1/auth/me`** — Requires `Authorization: Bearer <access>`. `shared/dependencies:get_current_user` decodes JWT, checks `type=access`, verifies `jti` not blacklisted in Redis, loads user, checks `is_active`.

5. **`POST /api/v1/auth/refresh`** — Client sends `{refresh_token}`. `decode_token` verifies `type=refresh`, `RefreshTokenRepository.get_by_token` finds the row, checks not revoked, revokes the old token, `_issue_tokens(stored.user)` rotates the pair (new access + new refresh, old refresh revoked).

6. **`POST /api/v1/auth/logout`** — Client sends `Authorization: Bearer <access>` + `{refresh_token}`. `AuthService.logout` revokes the refresh token family, decodes the access token, extracts `jti`, blacklists it in Redis with TTL `exp - now`. Next access with old token → `401 Token revoked`.


## JWT and Refresh Token Workflow

- **`create_access_token(subject, expires_delta)`** — `exp = now(UTC) + 15 min`, payload: `{sub, exp, type:"access", jti:uuid4(), iss, aud}` → `jwt.encode(secret, algorithm)`.
- **`create_refresh_token(subject, expires_delta)`** — `exp = now + 7 days`, `type:"refresh"`.
- **`decode_token(token)`** — `jwt.decode(secret, [algorithm], audience, issuer)`. Returns `dict | None`. Caller must check `payload.get("type")`.
- **Token family** — All refresh tokens sharing the same `family_id` are revoked together on logout or reuse detection.
- **JTI blacklisting** — On logout, the access token's `jti` is stored in Redis with TTL `remaining_until_exp`. `get_current_user` rejects any blacklisted `jti`.
- **Reuse detection** — If a refresh token is used twice, the entire `family_id` is revoked and an audit event `TOKEN_REUSE_DETECTED` is logged.


## TOTP 2FA Workflow

- **`POST /api/v1/auth/2fa/enable`** — Creates an unverified `TotpDevice` (secret_key via `pyotp.random_base32()`, QR code data URI, 8 backup codes hashed with SHA-256). Returns `{secret, qr_code, backup_codes}`. Device `is_verified=False`.
- **`POST /api/v1/auth/2fa/verify-setup`** — Verifies a TOTP token during enrollment. Marks device `is_verified=True`.
- **`login`** — If user has 2FA enabled + verified → stores `2fa_pending:{user_id}` in Redis (TTL 300s), raises `ValueError("TWO_FACTOR_REQUIRED")`.
- **`POST /api/v1/auth/2fa/login-verify`** — Accepts `user_id` + `token`. Checks pending 2FA session exists → verifies TOTP token (or single-use backup code) → clears pending session → `_issue_tokens(user)` → returns `{access_token, refresh_token}`.
- **`POST /api/v1/auth/2fa/disable`** — Verifies current TOTP token → deletes the `TotpDevice` → returns `200`.
- **Backup codes** — SHA-256 hashed in `TotpDevice.backup_codes` JSONB. Each code can be used once.


## RBAC and API Key Management

### Role-Based Access Control

- **`require_role("Admin")`**, **`require_role("Manager")`**, **`require_role("User")`** — FastAPI dependencies that check `current_user.role.name` against allowed roles.
- Admin endpoints (`/api/v1/users/`, `/api/v1/audit/`) require `require_role("Admin")`.
- Self-modification protection: `/api/v1/users/{id}/role` and `/api/v1/users/{id}/status` block modification of your own account.

### API Key (Service Account) Management

- **`POST /api/v1/auth/api-keys`** — Create a new API key for the authenticated user. Returns `{id, name, key_prefix, scopes, expires_at, last_used_at, is_revoked, created_at, api_key}` — the plaintext key is shown **once only** at creation.
- **`GET /api/v1/auth/api-keys`** — List all API keys for a user (exposes metadata only, not key values).
- **`DELETE /api/v1/auth/api-keys/{id}`** — Revoke an API key.
- **`verify_api_key(api_key_value)`** — Verifies a key value (starts with `ak_`, hash matches, not revoked, not expired) and returns the associated `User` object. Updates `last_used_at`. Used via `X-API-Key` header.


## Audit Logging

- **`AuditLog`** model: `id`, `user_id` (FK → users, nullable), `action` (String, indexed), `success` (Boolean, default True), `ip_address` (String, nullable), `created_at`.
- Logged actions: REGISTER, LOGIN, LOGOUT, PASSWORD_RESET, PASSWORD_CHANGE, TOTP_ENROLLMENT_STARTED, TOTP_ENABLED, TOTP_DISABLED, TOTP_LOGIN_SUCCESS, TOTP_LOGIN_FAILED, TOTP_BACKUP_CODE_USED, API_KEY_CREATED, API_KEY_REVOKED, TOKEN_REFRESH, TOKEN_REUSE_DETECTED, EMAIL_VERIFY, EMAIL_RESEND, PASSWORD_RESET_REQUEST.
- **`GET /api/v1/audit/`** — Admin-only endpoint with pagination, search, and filtering by action, user_id, success, and sort order.


## Database Schema Overview

Core tables (all use `TimestampMixin`: `created_at`, `updated_at`):

| Table | Key Columns | Relationships |
|---|---|---|
| **users** | id(PK), email(unique), username(unique), hashed_password, is_active, is_verified, role_id(FK→roles) | ↔ roles (many-to-one) |
| **roles** | id(PK), name(unique), description | ↔ users (one-to-many) |
| **refresh_tokens** | id(PK), token(unique), user_id(FK→users CASCADE), family_id, expires_at, is_revoked | ↔ users |
| **password_reset_tokens** | id(PK), token(unique), user_id(FK→users), expires_at, is_used | ↔ users |
| **email_verification_tokens** | id(PK), token(unique), user_id(FK→users CASCADE), expires_at, is_used | ↔ users |
| **totp_devices** | id(PK), user_id(FK→users CASCADE), secret_key, is_verified, backup_codes(JSONB) | ↔ users |
| **api_keys** | id(PK), user_id(FK→users CASCADE), name, key_prefix, key_hash, scopes(JSONB), expires_at, last_used_at, is_revoked | ↔ users |
| **user_sessions** | id(PK), user_id(FK→users), jti, device_name, device_type, ip_address, user_agent, last_active_at, is_revoked | ↔ users |
| **audit_logs** | id(PK), user_id(FK→users nullable), action, success, ip_address | — |


## API Endpoint Documentation

### Authentication (`/api/v1/auth`)

| Endpoint | Method | Auth | Request | Response | Notes |
|---|---|---|---|---|---|
| `/register` | POST | public | `{email, username, password}` | `{message}` | 201; sends verification email |
| `/login` | POST | rate limit (5/60s) | `{username, password}` | `{access_token, refresh_token}` or `{two_factor_required: true}` | |
| `/me` | GET | Bearer | — | `{id, email, username, role, is_active, is_verified, created_at}` | |
| `/refresh` | POST | public | `{refresh_token}` | `{access_token, refresh_token}` | Rotation: old revoked |
| `/logout` | POST | Bearer + `{refresh_token}` | `{refresh_token}` | `{message}` | Revokes family + blacklists JTI |
| `/forgot-password` | POST | public | `{email}` | `{message}` | Generic reply (no enumeration) |
| `/reset-password` | POST | public | `{token, new_password}` | `{message}` | Revokes all user sessions |
| `/change-password` | POST | Bearer | `{current_password, new_password}` | `{message}` | Revokes all refresh tokens for user |
| `/verify-email` | GET | public | `{token}` | `{message}` | |
| `/resend-verification` | POST | public | `{email}` | `{message}` | |
| `/2fa/enable` | POST | Bearer | — | `{secret, qr_code, backup_codes}` | Creates unverified device |
| `/2fa/verify-setup` | POST | Bearer | `{token}` | `{message, verified}` | Marks device active |
| `/2fa/disable` | POST | Bearer | `{token}` | `{message}` | Verifies current token then disables |
| `/2fa/login-verify` | POST | public | `{user_id, token}` | `{access_token, refresh_token}` | Complete login after 2FA |
| `/api-keys` | POST | Bearer | `{name, scopes, expires_in_days}` | `{id, name, key_prefix, ... , api_key}` | Key shown once |
| `/api-keys` | GET | Bearer | — | `{keys: [...]}` | Metadata only |
| `/api-keys/{id}` | DELETE | Bearer | — | `{message}` | Revoke key |

### Users (`/api/v1/users`)

| Endpoint | Method | Auth | Notes |
|---|---|---|---|
| `/` | GET | `require_role("Admin")` | Paginated list with search/filter/sort |
| `/{id}` | GET | `require_role("Admin")` | Get user by ID |
| `/{id}/role` | PATCH | `require_role("Admin")` | Update user role (blocks own modification) |
| `/{id}/status` | PATCH | `require_role("Admin")` | Activate/deactivate user (blocks own deactivation) |

### Audit (`/api/v1/audit`)

| Endpoint | Method | Auth | Notes |
|---|---|---|---|
| `/` | GET | `require_role("Admin")` | Paginated logs with filters (action, user_id, success) |


## Prerequisites

- Python 3.11 or later
- PostgreSQL 17 (with `psql` access for migrations)
- Redis 7 (with `redis-cli` access)
- Docker and docker-compose (optional, for containerized setup)
- `uvicorn` for local development


## Local Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/aaryaa135/AuthForge.git
cd AuthForge
```

### 2. Create a virtual environment

```bash
python -m venv .venv
.\.venv\Scripts\activate  # Windows
source .venv/bin/activate   # macOS / Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
pip install -e ".[dev]"  # installs ruff, black, pytest, coverage
```

### 4. Environment configuration

```bash
cp .env.example .env
nano .env  # edit values as described below
```

### 5. Start dependencies (Docker recommended)

```bash
docker compose up -d  # starts db (postgres:17) and redis (redis:7-alpine)
```

### 6. Run database migrations

```bash
alembic upgrade head
```

### 7. Seed default roles

```bash
python scripts/seed_roles.py
```

### 8. Seed admin user (optional)

```bash
python scripts/seed_admin.py
```

### 9. Start the development server

```bash
make run  # uvicorn app.main:app --reload
# or manually:
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 10. Verify the service

```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"a@b.com","username":"ab","password":"Password@123"}'
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=a@b.com&password=Password@123"
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <access_token>"
```


## Environment Variable Setup

Copy `.env.example` to `.env` and configure the following variables:

| Variable | Required? | Description |
|---|---|---|
| `APP_NAME` | yes | Application name displayed in API metadata |
| `APP_VERSION` | yes | Semantic version |
| `ENVIRONMENT` | yes | `development` | `test` | `staging` | `production` |
| `DEBUG` | yes | `True` for dev, `False` for prod |
| `LOG_LEVEL` | yes | `INFO`, `DEBUG`, `WARNING`, `ERROR`, `CRITICAL` |
| `API_HOST` | yes | Bind host (e.g. `0.0.0.0`) |
| `API_PORT` | yes | Bind port (e.g. `8000`) |
| `FRONTEND_URL` | yes | Base URL for verification links (e.g. `http://localhost:8000`) |
| `DATABASE_URL` | yes | PostgreSQL connection string `postgresql://user:pw@host:port/db` |
| `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | alternate | Split DB vars (mutually exclusive with `DATABASE_URL`) |
| `JWT_SECRET_KEY` | yes | **Must be >= 32 random characters**. Generated via `openssl rand -hex 64`. |
| `JWT_ALGORITHM` | yes | `HS256` (default) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | no | Default `15` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | no | Default `7` |
| `REQUIRE_EMAIL_VERIFICATION` | no | `True` or `False` |
| `CORS_ORIGINS` | no | Comma-separated list (e.g. `https://app.com,https://admin.com`). Overrides `cors_origins`. In production, if unset, falls back to `[frontend_url]`. In dev, defaults to `["*"]`. |
| `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB` | yes | Redis connection parameters |
| `REDIS_PASSWORD` | no | If your Redis requires authentication |
| `EMAIL_PROVIDER` | yes | `console` | `smtp` | `resend` |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL` | if SMTP | SMTP connection settings |
| `RESEND_API_KEY`, `RESEND_FROM_EMAIL` | if Resend | Resend API key and from-email |
| `TEST_ADMIN_EMAIL`, `TEST_ADMIN_PASSWORD` | test only | Used by `scripts/seed_admin.py` |

The `.env` file is gitignored. Never commit real secrets. The `.env.example` file contains placeholder values for reference.


## Docker Setup

### Using docker-compose

```bash
docker compose up --build -d  # builds API container, starts db + redis
# View logs:
docker compose logs -f api
# Run migrations inside the running API container:
docker compose exec api alembic upgrade head
# Seed roles:
docker compose exec api python scripts/seed_roles.py
# Seed admin:
docker compose exec api python scripts/seed_admin.py
```

### Dockerfile

The project uses a multi-stage hardened Dockerfile:

- **builder stage**: `python:3.11-slim` with `build-essential` and `libpq-dev`, installs deps from `requirements.txt` to `/install`
- **runtime stage**: `python:3.11-slim` with `libpq5` and `curl`, creates `appuser` (UID 10001), copies installed deps and source code, runs as `appuser`
- **Exposes**: `8000`
- **Healthcheck**: `curl -f http://localhost:8000/health`
- **CMD**: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips '*'`


## Database Migration Instructions

Migrations are managed via **Alembic**. The `alembic.ini` configures the script location and default URL (set via `.env` `DATABASE_URL` or split `DB_*` vars).

### Creating a new migration

```bash
alembic revision --autogenerate -m "add description of change"
```

This auto-detects model changes and generates a new migration file under `alembic/versions/`.

### Running migrations

```bash
# Online (connected to DB)
alembic upgrade head

# Offline (no DB connection)
alembic upgrade head  # still works if URL is configured in .env

# Downgrade
alembic downgrade base
```

### Migration chain (current)

The existing chain creates tables in order:
1. `roles` + bulk insert Admin + User
2. `users`
3. `refresh_tokens`
4. `password_reset_tokens`
5. `email_verification_tokens`
6. `audit_logs`

New migrations are appended to the chain. Always test migrations on a copy of the production DB before applying.


## Running Tests and Linting

### Test suite

```bash
pytest -v --tb=short           # run all tests
pytest -v --tb=short -k "register"  # run only register-related tests
USE_FAKE_REDIS=1 pytest -q   # run with fake Redis (no Docker required)
pytest --cov=app               # with coverage report
```

### Coverage threshold

`pyproject.toml` enforces `coverage >= 70%`. If coverage falls below 70%, the coverage check fails.

### Linting

```bash
ruff check .           # lint errors
ruff --fix .           # auto-fix lint errors
black --check .        # format check
black .                # format files
```

### Makefile commands

```bash
make install        # pip install + pre-commit install
make lint           # ruff check
make format         # ruff --fix + black
make test           # pytest --cov
make test-quick     # USE_FAKE_REDIS=1 pytest -q
make run            # uvicorn --reload
make migrate        # alembic upgrade head
make seed           # python scripts/seed_roles.py
make seed-admin     # python scripts/seed_admin.py
make docker-up      # docker compose up --build -d
make docker-down    # docker compose down
make clean          # remove .venv, .pytest_cache, .coverage, htmlcov
```


## GitHub Actions CI/CD

The CI pipeline is defined in `.github/workflows/ci.yml` and runs on:

- **Push** to `main`, `develop`, or `feature/**` branches
- **Pull requests** targeting `main` or `develop`

### Workflow jobs

1. **`quality-checks`** (runs-on: `ubuntu-latest`)
   - Starts PostgreSQL 17 and Redis 7 service containers
   - Installs dependencies with pip cache (`~/.cache/pip`)
   - Runs `ruff check` (linting)
   - Runs `black --check` (format)
   - Runs `alembic upgrade head` (migrations — fails job on error with `|| exit 1`)
   - Seeds default roles via `scripts/seed_roles.py`
   - Runs `pytest -v --tb=short --cov=app --cov-report=term-missing` (tests with coverage)
   - Sets `USE_FAKE_REDIS=0` to prefer real Redis; conftest auto-falls back to FakeRedis on connection failure

### Secrets in CI

- `JWT_SECRET_KEY` is set as an env var in the CI job (not stored in YAML)
- Avoid committing real credentials — the `.env` and `.env.test` files are gitignored


## Example API Requests

### Register a new user

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","username":"user1","password":"Password@123"}'
```

### Login and receive tokens

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=user@example.com&password=Password@123"
```

### Login with 2FA (first step)

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=user@example.com&password=Password@123"
# Response: {"two_factor_required": true, "user_id": "uuid...", "message": "Two-factor verification required."}
```

### Complete 2FA login (second step)

```bash
totp_token=$(python -c "import pyotp; print(pyotp.TOTP('BASE32SECRET').now())")
curl -X POST http://localhost:8000/api/v1/auth/2fa/login-verify \
  -d "user_id=USER_UUID&token=$totp_token"
```

### Refresh token rotation

```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"old_refresh_token"}'
# Response: new {access_token, refresh_token} — old refresh is revoked
```

### Revoke all sessions on password change

After changing password, all existing refresh tokens are revoked. The next use of an old refresh token returns `401`.


## Future Improvements and Limitations

The following areas are identified for future work:

- **Algorithm rotation** — Currently HS256 only. Future: support RS256 / HS384 with key management.
- **CSRF protection** — API-only stateless design; SameSite cookie configuration recommended for browser-based flows.
- **Email provider configuration** — Default `console` provider prints links to stdout. Set `EMAIL_PROVIDER=smtp` or `EMAIL_PROVIDER=resend` with proper credentials for production.
- **Connection pooling tuning** — `pool_size`, `max_overflow`, `pool_recycle` in `db/session.py` may need adjustment for high-throughput deployments.
- **Additional 2FA methods** — TOTP is implemented; future: WebAuthn/FIDO2 support.
- **Rate limiting on password operations** — Currently only login is rate-limited; forgot/password-reset could benefit from similar limits.
- **Request body size limits** — FastAPI default; may need adjustment for large API key payloads.
- **OpenAPI extensions** — Additional description and example values can be added to schemas.

AuthForge is actively maintained. PRs welcome. See `CONTRIBUTING.md` for workflow, code style, and testing guidelines.