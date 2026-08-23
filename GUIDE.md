# 📘 AuthForge — Complete Code Guide

> Every file, every module, every flow — explained line-by-line for SDE review, onboarding, and interviews.

**Read time:** 20 min · **Codebase:** `64 py files, ~3500 LOC` · **Stack:** FastAPI 0.139 · SQLAlchemy 2.0 · PostgreSQL 17 · Redis 7 · Docker

---

## Table of Contents

1. [Mental Model](#1-mental-model)
2. [Directory Tree](#2-directory-tree)
3. [Entry Point & Lifecycle](#3-entry-point--lifecycle)
4. [Core (`app/core/`)](#4-core-appcore)
5. [Cache (`app/cache/`)](#5-cache-appcache)
6. [Database (`app/db/`)](#6-database-appdb)
7. [Modules](#7-modules)
   - 7.1 Auth
   - 7.2 Users
   - 7.3 Roles
   - 7.4 Audit
8. [Providers (`app/providers/`)](#8-providers-appproviders)
9. [Shared (`app/shared/`)](#9-shared-appshared)
10. [Migrations (`alembic/`)](#10-migrations-alembic)
11. [Scripts (`scripts/`)](#11-scripts-scripts)
12. [Tests (`tests/`)](#12-tests-tests)
13. [Infra & Config](#13-infra--config)
14. [Request Lifecycle (End-to-End)](#14-request-lifecycle-end-to-end)
15. [Security Matrix](#15-security-matrix)
16. [How to Extend](#16-how-to-extend)
17. [Cheat Sheet](#17-cheat-sheet)

---

## 1. Mental Model

AuthForge is **modular monolith** with **vertical modules** (`auth`, `users`, `roles`, `audit`) + **horizontal cross-cutting** (`core`, `cache`, `providers`, `shared`). Every feature goes `Router → Service → Repository → DB/Redis`.

```
Client → FastAPI (app/main.py:24)
  → Middleware: CORS → RequestID → SecurityHeaders → LegacyRewrite
  → Router (app/modules/*/routes.py)
    → Service (business rules, hashing, token rotation)
      → Repository (SQLAlchemy queries)
        → PostgreSQL + Redis + EmailProvider
  → Middleware Response (X-Request-ID, security headers) → Client
```

**Key invariants:**
- JWT `access` 15 min, `refresh` 7 days, each has `jti` (UUID) + `type` + `sub` (user.id). See `app/core/jwt.py:9`.
- Logout blacklists `jti` in Redis with `TTL = exp - now` (`app/modules/auth/service.py:290`). `shared/dependencies.py:44` rejects blacklisted `jti`.
- Rate limit is atomic `INCR + EXPIRE` (`app/core/rate_limit.py:13`).
- All list endpoints are paginated (`app/shared/pagination.py:1`).

---

## 2. Directory Tree

```
AuthForge/
  app/
    main.py
    core/       config, jwt, security, dependencies, middleware, exceptions, logger, rate_limit
    cache/      client, keys, service
    db/         base, session, models
    modules/
      auth/     models, schemas, repository, service, routes, dependencies
      users/    models, schemas, repository, service, routes, dependencies (re-export)
      roles/    models, repository
      audit/    models, schemas, repository, service, routes, dependencies
    providers/  base, console, factory
    shared/     dependencies, pagination, responses
  alembic/      env.py, versions/*.py, alembic.ini
  scripts/      seed_roles.py, seed_admin.py
  tests/        conftest.py, utils.py, test_*.py
  docker-compose.yml  Dockerfile  .dockerignore
  pyproject.toml  requirements.txt  Makefile  .pre-commit-config.yaml
  GUIDE.md  README.md  CONTRIBUTING.md  LICENSE
```

---

## 3. Entry Point & Lifecycle

### `app/main.py:1` — FastAPI App Factory

| Line | What | Why |
|------|------|-----|
| `14: @asynccontextmanager lifespan` | Logs `Starting/Stopping` | Hook for warm-up/close (add Redis/DB ping here) |
| `24: FastAPI(... openapi_tags ...)` | Title `settings.app_name`, `version`, `debug`, `contact/license` | Swagger grouping |
| `31: add_middleware(SecurityHeaders) → RequestID → CORS` | Order outer→inner. `settings.cors_origins_list` (`app/core/config.py:66`) | `*` in dev, `frontend_url` in prod / `CORS_ORIGINS` csv |
| `41: @middleware legacy_path_rewrite` | Rewrites `/users/*`→`/api/v1/users/*`, `/audit/*`→`/api/v1/audit/*` | Backward compat after versioning fix |
| `49: register_exception_handlers(app)` | Global `AppException`, `HTTPException`, `ValidationError`, `500` | Unified JSON errors + `request_id` on 500 |
| `56: include_router` | `auth_router (/api/v1/auth)`, `users_router (/api/v1/users)`, `audit_router (/api/v1/audit)` | Versioned APIs |
| `42: GET /` , `48: GET /health` | Root + `{status, application, version, environment}` | Probes, `HEALTHCHECK curl /health` in Dockerfile |

**OpenAPI:** `/docs`, `/redoc`, `/openapi.json` auto-generated from routers.

---

## 4. Core (`app/core/`)

### `app/core/config.py:1` — 12-Factor Settings

`class Settings(BaseSettings)` loads from `.env` (UTF-8, case-insensitive, `extra="ignore"`).

- **App:** `app_name`, `app_version`, `environment` (validator `dev/test/staging/prod`), `debug`
- **API:** `api_host`, `api_port`
- **DB:** `database_url` **or** `db_host/port/name/user/password` → `sqlalchemy_database_url:82` (`postgresql+psycopg2://`)
- **JWT:** `jwt_secret_key` (validator `len>=32`, rejects placeholder), `jwt_algorithm` (HS256), `access_token_expire_minutes` (15), `refresh_token_expire_days` (7)
- **Redis:** `redis_host/port/db/password` → `redis_url:107` (`redis://:pwd@host:port/db`)
- **Frontend:** `frontend_url` (default `http://localhost:8000`), `require_email_verification` (bool), `cors_origins` csv → `cors_origins_list:66`
- **Logging:** `log_level`

`get_settings() @lru_cache` singleton `settings` imported everywhere. Used in `alembic/env.py:14` (`sqlalchemy_database_url`), `app/db/session.py:9`, `app/cache/client.py:6`, `app/core/jwt.py:21`.

### `app/core/jwt.py:1` — JWT

- `create_access_token(subject, expires_delta=None):9` — `exp = now(UTC)+15m`, payload `{sub, exp, type:"access", jti:uuid4()}` → `jwt.encode(secret, algorithm)`.
- `create_refresh_token(subject, ...):38` — `exp = now+7d`, `type:"refresh"`.
- `decode_token(token):67` — `jwt.decode(secret, [algorithm])` → `dict | None` (swallows `JWTError`). Caller must check `payload.get("type")`.

### `app/core/security.py:1` — Passwords

- `pwd_context = CryptContext(schemes=["bcrypt"])`
- `hash_password(pwd):10` → `pwd_context.hash`
- `verify_password(pwd, hashed):17` → `pwd_context.verify`

> Note: `bcrypt 4.0.1 + passlib` works but direct `bcrypt` library is more future-proof.

### `app/core/dependencies.py:1` — RBAC Helper

```py
def require_role(*roles):7
  def role_checker(current_user=Depends(get_current_user)):13  # from app/shared/dependencies.py:3
    if current_user.role is None → 403
    if role.name not in roles → 403
    return user
```

Used as `Depends(require_role("Admin"))` in `app/modules/users/routes.py:33`.

### `app/core/middleware.py:1` — Cross-Cutting

- `RequestIDMiddleware:7` — reads `X-Request-ID` or `uuid4()`, stores `request.state.request_id`, times `call_next`, adds `X-Request-ID` response, logs `METHOD path → status [ms] req_id=`.
- `SecurityHeadersMiddleware:20` — adds `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection:0`, `Referrer-Policy`, `Permissions-Policy`, `HSTS` if `https`.

### `app/core/exceptions.py:1` — Global Handlers

- `class AppException(detail, status_code=400):5`
- `register_exception_handlers:19` registers:
  - `AppException` → `{detail}` with `exc.status_code`
  - `StarletteHTTPException` → `{detail}`
  - `RequestValidationError` → `422 {detail: errors()}` (Pydantic)
  - `Exception` (catch-all) → `500 {detail:"Internal server error.", request_id}` + `logger.exception`

### `app/core/logger.py:1` — Logging

- `LOG_FORMAT = "%(asctime) | %(levelname)-8s | %(name)s | %(message)s"`
- If `environment=="production"` tries `pythonjsonlogger` JSON handler else human-readable, `stream=sys.stdout`, level `settings.log_level`. `logger = get_logger("authforge")` used in `auth/service.py`, `users/repository.py`.

### `app/core/rate_limit.py:1` — Atomic Rate Limiter

```py
class RateLimiter:
  def allow_request(key, limit, window):14
    pipe.incr(key); pipe.ttl(key) → count, ttl
    if count==1: expire(key, window)
    elif ttl==-1: expire(key, window)  # no TTL edge
    return count <= limit
```

Used in `app/modules/auth/dependencies.py:47` `login_rate_limit` with `key=f"login:{username}" limit=5 window=60`. Old bug was non-atomic `get→set` resetting TTL — fixed.

---

## 5. Cache (`app/cache/`)

### `app/cache/client.py:1`

```py
redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
```

Global singleton. `tests/conftest.py:1` swaps to `fakeredis.FakeRedis` if `ping` fails or `USE_FAKE_REDIS=1`.

### `app/cache/keys.py:1`

```py
class RedisKeys:
  user_email(email) → "user:email:{email}"
  user_username(username) → "user:username:{username}"
  blacklist(jti) → "blacklist:{jti}"
  session(user_id) → "session:{user_id}"  # reserved
```

### `app/cache/service.py:1`

Wrapper around `redis_client`:

- `set(key, value, ttl)`, `get(key) → Optional[str]`, `delete`, `exists → bool`
- `set_json(key, dict, ttl=300) → json.dumps`, `get_json → dict|None`
- `blacklist_token(jti, ttl)` → `set(RedisKeys.blacklist(jti), "1", ttl)`
- `is_blacklisted(jti) → exists(blacklist:{jti})`

Used in `shared/dependencies.py:44` (block blacklisted access) and `auth/service.py:290` (TTL = `exp - now`).

---

## 6. Database (`app/db/`)

### `app/db/base.py:1`

```py
class Base(DeclarativeBase):7
class TimestampMixin:15
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
  updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

### `app/db/session.py:1`

```py
engine = create_engine(settings.sqlalchemy_database_url,
  pool_pre_ping=True, pool_size=10, max_overflow=20, pool_timeout=30, pool_recycle=1800):9
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False):15
def get_db():22  # Generator[Session] — yields SessionLocal(), finally close()
```

Injected via `Depends(get_db)` in all routes/dependencies. `pool_recycle 1800` avoids stale Neon connections.

### `app/db/models.py:1` — Registry

Re-exports for `Base.metadata`:

```py
from app.modules.roles.models import Role
from app.modules.users.models import User
from app.modules.auth.models import RefreshToken, PasswordResetToken, EmailVerificationToken
from app.modules.audit.models import AuditLog
```

Needed by `alembic/env.py:9` `import app.db.models`.

---

## 7. Modules

### 7.1 Auth (`app/modules/auth/`)

#### `models.py:1`

- `RefreshToken:11` `__tablename__="refresh_tokens"` `__table_args__ Index(token), Index(user_id)` — `id UUID PK`, `token String unique index`, `user_id FK users.id CASCADE`, `expires_at DateTime(timezone=True)`, `is_revoked bool default False`, `user relationship`.
- `PasswordResetToken:44` `token unique index`, `user_id FK`, `expires_at DateTime(timezone=True)`, `is_used bool`, `Index(token)`.
- `EmailVerificationToken:81` same as above, `Index(token)`.

#### `schemas.py:1` — Pydantic v2

- `LoginRequest:4` `email:EmailStr`, `password:str`
- `TokenResponse:9` `access_token, refresh_token, token_type="bearer"  # noqa S105`
- `RefreshTokenRequest:15` `refresh_token:str`
- `LogoutRequest:19` `refresh_token, access_token` (legacy, not used — `routes.py` uses `RefreshTokenRequest` for logout body)
- `MessageResponse:24` `message:str`
- `ForgotPasswordRequest:28` `email:EmailStr`, `ForgotPasswordResponse:32` `message`
- `ResetPasswordRequest:36` `token, new_password`, `ChangePasswordRequest:41` `current_password, new_password`
- `VerifyEmailRequest:46` `token`, `ResendVerificationRequest:50` `email:EmailStr`

#### `repository.py:1`

- `RefreshTokenRepository(db):9` — `create(token)`, `get_by_token(token) → select where token==`, `revoke(token)` (`is_revoked=True + commit`), `delete`.
- `PasswordResetRepository:39` — `create`, `get_by_token`, `update`, `mark_used` (`is_used=True`).
- `EmailVerificationRepository:68` — same as above.

#### `service.py:1` — Business Logic (500 LOC)

`class AuthService(user_repo, role_repo, refresh_repo, reset_repo, verify_repo, email_provider, audit_service, cache=CacheService())`

- `register_user(user_data: UserCreate):65` — checks `email`/`username` uniqueness → `Role.get_by_name("User")` → `User(hashed_password=hash_password, role_id, is_active True, is_verified False)` → `audit.log REGISTER` → `EmailVerificationToken(token_urlsafe(32), now+24h)` → `logger.info` → `verification_link = f"{frontend_url}/api/v1/auth/verify-email?token={token}"` → `email_provider.send_verification_email` → return `User`.
- `_issue_tokens(user):134` — `create_access_token(str(user.id))`, `create_refresh_token(str(user.id))`, `RefreshToken(token=refresh, user_id, expires_at=now+7d)` → `create` → `TokenResponse`.
- `login_user(identifier, password):164` — `if "@" in identifier → get_by_email else get_by_username` → `if not user → ValueError Invalid credentials` → `if not is_active → Inactive` → `if not verify_password → Invalid` → `if require_email_verification and not is_verified → Email not verified` → `audit.log LOGIN` → `_issue_tokens`.
- `refresh_tokens(request):211` — `decode_token(refresh)` → `type=="refresh"` → `get_by_token` → `if not found/revoked → ValueError` → `revoke(old)` → `_issue_tokens(stored.user)` (rotation).
- `logout(current_user, request, access_token):244` — `decode refresh → get_by_token → revoke` → `decode access → jti/exp → remaining_ttl = max(0, int(exp - now.timestamp()))` → `cache.blacklist_token(jti, ttl)` → `audit.log LOGOUT` → `MessageResponse`.
- `forgot_password(request):303` — `get_by_email` → `if None → generic message` (no enumeration) → `token_urlsafe(32), PasswordResetToken(now+1h)` → `logger` → `reset_link = f"{frontend_url}/api/v1/auth/reset-password?token={token}"` → `send_password_reset_email` → generic `ForgotPasswordResponse`.
- `reset_password(request):346` — `get_by_token` → `if None → ValueError Invalid` → `if is_used → already used` → `if exp < now (tz-aware compare) → expired` → `user.hashed_password = hash_password(new)` → `user_repo.update` → `mark_used` → `audit.log PASSWORD_RESET` → `MessageResponse`.
- `change_password(current_user, request):389` — `verify_password(current)` → `hash new` → `update` → `audit.log PASSWORD_CHANGE`.
- `verify_email(token):421` — `get_by_token` → `if is_used/exp<now → ValueError` → `user.is_verified=True → update` → `verification.is_used=True → update` → `MessageResponse`.
- `resend_verification(request):457` — `get_by_email` → `if None → generic` → `if is_verified → already verified` → `new token_urlsafe now+24h` → `send_verification_email`.

> All `expires_at` now `datetime.now(timezone.utc)` + `timedelta`, TZ-aware compare `exp.replace(tzinfo=UTC) if naive`.

#### `routes.py:1` — HTTP

`router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])`

| Endpoint | Method | Auth | Handler | Error Mapping |
|----------|--------|------|---------|---------------|
| `/register` | POST | no | `register(user: UserCreate, service)` → `201 UserResponse` | `ValueError→400` (was `Exception + traceback`, fixed) |
| `/login` | POST | rate limit | `login(form_data: OAuth2PasswordRequestForm, _:login_rate_limit, service)` → `TokenResponse` | `ValueError→401` |
| `/me` | GET | Bearer | `me(current_user=Depends(get_current_user))` → `UserResponse` | |
| `/refresh` | POST | no | `refresh(RefreshTokenRequest)` → `TokenResponse` | `→401` |
| `/logout` | POST | Bearer | `logout(body:RefreshTokenRequest, request:Request, current_user, service)` — parses `Authorization: Bearer ` manually → `service.logout` | `ValueError→400` |
| `/forgot-password` | POST | no | `forgot_password(ForgotPasswordRequest)` | |
| `/reset-password` | POST | no | `reset_password(ResetPasswordRequest)` | `ValueError→400` |
| `/change-password` | POST | Bearer | `change_password(ChangePasswordRequest, current_user)` | `→400` |
| `/verify-email?token=` | GET | no | `verify_email(token)` | `→400` |
| `/resend-verification` | POST | no | `resend_verification(ResendVerificationRequest)` | |

#### `dependencies.py:1` — DI

- `get_auth_service(db=Depends(get_db)):25` → constructs `AuditService(AuditRepository(db))` + `AuthService(UserRepository, RoleRepository, RefreshTokenRepository, PasswordResetRepository, EmailVerificationRepository, get_email_provider(), audit_service)`.
- `login_rate_limit(form_data=Depends(OAuth2PasswordRequestForm)):47` → `RateLimiter().allow_request(key=f"login:{username}", limit=5, window=60)` → `429` if exceeded.

### 7.2 Users (`app/modules/users/`)

#### `models.py:1`

```py
class User(Base, TimestampMixin):
  __tablename__="users"
  __table_args__ = Index(ix_users_email), Index(ix_users_username), Index(ix_users_role_id)
  id: UUID PK, email String(255) unique index, username String(100) unique index,
  hashed_password String(255), is_active bool True, is_verified bool False,
  role_id FK roles.id, role relationship("Role")
```

#### `schemas.py:1`

- `UserCreate:7` `email:EmailStr, username:str (3-30), password:str (8-128)`
- `UserResponse:25` `id:UUID, email:EmailStr, username, role:str, is_active, is_verified, created_at`
- `UpdateUserRoleRequest:41` `role:str`
- `UpdateUserStatusRequest:45` `is_active:bool`

#### `repository.py:1`

- `get_by_email(email):20` — `RedisKeys.user_email(email)` → `cache.get_json` → if HIT `db.get(User, UUID(id))` else `select where email==` → `cache.set_json({"id": str(id)}, ttl=300)` → return.
- `get_by_username` same with `user:username`.
- `get_by_id(user_id):74` → `select where id==`.
- `create(user):78` → `add/commit/refresh`.
- `get_all():84` → `select order_by created_at desc` (legacy, no pagination).
- `get_paginated(offset, limit):87` → `scalar(count) total`, `select offset/limit` → `(items, total)`.
- `update(user):91` → `commit`, `cache.delete(email)`, `cache.delete(username)`, `refresh`.

#### `service.py:1`

`class UserService(repository: UserRepository)`

- `list_users():21` → `repo.get_all()` → `list[UserResponse]` (kept for compat, not used by new paginated route).
- `update_role(user_id, role_name, role_repo):37` → `get_by_id` → `get_by_name` → `user.role_id=role.id` → `update` → `logger` → `UserResponse`.
- `get_user(user_id):77` → `get_by_id` → `UserResponse` or `ValueError User not found`.
- `update_status(user_id, is_active):100` → `is_active=` → `update` → `UserResponse`.

#### `routes.py:1`

`router = APIRouter(prefix="/api/v1/users", tags=["Users"])`

| Endpoint | Method | Auth | Handler |
|----------|--------|------|---------|
| `/` | GET | `require_role("Admin")` | `list_users(page=Query(1,ge1), page_size=Query(20,1-100), db, _)` → `repo.get_paginated(offset,limit)` → `PaginatedResponse[UserResponse]` |
| `/{user_id}` | GET | Admin | `get_user(user_id)` → `404` on ValueError |
| `/{user_id}/role` | PATCH | Admin | `update_user_role(user_id, UpdateUserRoleRequest)` |
| `/{user_id}/status` | PATCH | Admin | `update_user_status(user_id, UpdateUserStatusRequest)` |

Legacy `/users` still works via `app/main.py:41` rewrite.

#### `dependencies.py:1` — Re-export

```py
from app.shared.dependencies import get_current_user, oauth2_scheme
__all__ = ["get_current_user", "oauth2_scheme"]
```

Canonical is `app/shared/dependencies.py`.

### 7.3 Roles (`app/modules/roles/`)

#### `models.py:1`

```py
class Role(Base, TimestampMixin):
  __tablename__="roles"
  id UUID PK, name String(50) unique, description String(255) nullable
```

#### `repository.py:1`

`RoleRepository(db).get_by_name(name):15` → `select where name==`.

Seeded via `scripts/seed_roles.py` and migration `49ca1ceb37f9`.

### 7.4 Audit (`app/modules/audit/`)

#### `models.py:1`

```py
class AuditLog(Base, TimestampMixin):
  __tablename__="audit_logs"
  __table_args__ = Index(user_id), Index(action), Index(created_at)
  id UUID PK, user_id FK users.id nullable index, action String(100) index, success bool, ip_address String(100) nullable
```

#### `schemas.py:1`

`AuditLogResponse:7` `id:UUID, user_id:UUID|None, action, success, ip_address|None, created_at`.

#### `repository.py:1`

- `create(audit_log)`, `get_all()`, `get_by_user(user_id)`, `get_paginated(offset, limit):28` → `(items, total)` with `func.count`.

#### `service.py:1`

`AuditService(repository).log(action, success=True, user_id=None, ip_address=None):16` → `AuditLog(...)` → `create`.

Called in `auth/service.py` for `REGISTER, LOGIN, LOGOUT, PASSWORD_RESET, PASSWORD_CHANGE`.

#### `routes.py:1`

`router = APIRouter(prefix="/api/v1/audit", tags=["Audit"])`

| Endpoint | Auth | Handler |
|----------|------|---------|
| `GET /` | `get_admin_user` | `get_audit_logs(page, page_size, current_user, repository)` → `repo.get_paginated` → `PaginatedResponse[AuditLogResponse]` |

Legacy `/audit` via rewrite.

#### `dependencies.py:1`

`get_audit_repository(db=Depends(get_db)) → AuditRepository(db)`

---

## 8. Providers (`app/providers/`)

### `base.py:1`

```py
class EmailProvider(ABC):
  send_verification_email(email, verification_link) -> None
  send_password_reset_email(email, reset_link) -> None
```

### `console.py:1`

`ConsoleEmailProvider(EmailProvider)` — prints `="*60`, `EMAIL VERIFICATION / PASSWORD RESET`, `To:`, `link` to stdout. For dev/test.

### `factory.py:1`

```py
def get_email_provider():4  # returns ConsoleEmailProvider()
# Future: Resend / SMTP / SendGrid switch via settings.email_provider
```

Injected in `auth/dependencies.py:get_auth_service`.

---

## 9. Shared (`app/shared/`)

### `dependencies.py:1` — Canonical Auth

```py
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login"):14
def get_current_user(token=Depends(oauth2_scheme), db=Depends(get_db)):19
  payload = decode_token(token)  # app/core/jwt.py:67
  if not payload → 401 Invalid token
  if payload.get("type") != "access" → 401 Invalid token type
  jti = payload.get("jti"); if None → 401
  if CacheService().is_blacklisted(jti):44 → 401 Token revoked
  try: user_id = UUID(payload["sub"]) → 401 on KeyError/ValueError/TypeError
  user = UserRepository(db).get_by_id(user_id); if None → 401 User not found
  if not user.is_active → 403 User inactive  # NEW
  return user
def get_admin_user(current_user=Depends(get_current_user)):78
  if current_user.role.name != "Admin" → 403 Admin required
```

Used by `app/modules/auth/routes.py:me`, `users/routes.py:require_role`, `audit/routes.py`. **Fix:** previously `core/dependencies` imported broken `users/dependencies`; now all via `shared`.

### `pagination.py:1`

```py
class PaginationParams:5  page:int=1, page_size:int=20, offset=(page-1)*page_size, limit=page_size
class PaginatedResponse(BaseModel, Generic[T]):13
  items:list[T], total:int, page, page_size, pages:int
  @classmethod create(items, total, params) → pages=(total+page_size-1)//page_size
```

Used by `users/routes.py:33` and `audit/routes.py:23`.

### `responses.py:1`

```py
class SuccessResponse(message, data|None)
class ErrorResponse(detail)
```

Generic wrappers (not yet used — ready for SDE).

---

## 10. Migrations (`alembic/`)

### `alembic.ini:1` — Config

`script_location = %(here)s/alembic`, `prepend_sys_path = .`, `sqlalchemy.url =` (empty, set in `env.py`), logging.

### `alembic/env.py:1`

```py
from app.core.config import settings
from app.db.base import Base
import app.db.models  # load metadata
config.set_main_option("sqlalchemy.url", settings.sqlalchemy_database_url):14  # FIXED: was settings.database_url
target_metadata = Base.metadata:19
def run_migrations_offline/online():22  # uses sqlalchemy_database_url
```

### `alembic/versions/`

Chain `49ca1ceb37f9 → 79c874dd1023 → 262b097f20f6 → 097bdb134512 → d3b9bb42aab1`

| Rev | File | Creates |
|-----|------|---------|
| `49ca1ceb37f9` | `create_users_and_roles_tables.py` | `roles` (id, name unique, description, timestamps) + `bulk_insert Admin/User` (Manager seeded via script), `users` (id, email unique, username unique, hashed_password, is_active, is_verified, role_id FK, timestamps) |
| `79c874dd1023` | `add_refresh_token_table.py` | `refresh_tokens` (id, token unique, user_id FK CASCADE, expires_at tz, is_revoked, timestamps) |
| `262b097f20f6` | `add_password_reset_tokens_table.py` | `password_reset_tokens` (id, token unique, user_id FK, expires_at, is_used, timestamps) |
| `097bdb134512` | `add_email_verification_tokens_table.py` | `email_verification_tokens` (id, token unique, user_id FK CASCADE, expires_at, is_used default false, timestamps) |
| `d3b9bb42aab1` | `add_audit_logs_table.py` | `audit_logs` (id, user_id FK nullable, action, success, ip_address, timestamps) |

> SDE improvement: added `Index` in models; new migrations would be needed to apply indexes if table exists — current indexes are in ORM only for new DBs.

---

## 11. Scripts (`scripts/`)

### `seed_roles.py:1`

```py
DEFAULT_ROLES = [Admin, Manager, User]:7
def seed_roles():23  # SessionLocal(), for each role_data if not exists( where name== ) → add(Role(**data)), commit
```

Run via `python scripts/seed_roles.py` or `make seed` or CI `Seed Roles`.

### `seed_admin.py:1`

```py
load_dotenv(".env"); load_dotenv(".env.test", override=False)
from app.core.security import hash_password  # FIXED: was get_password_hash
ADMIN_EMAIL = os.getenv("TEST_ADMIN_EMAIL") or os.getenv("ADMIN_EMAIL")
def seed_admin():17  # query Role Admin, query User by email, if exists → skip, if no email/pwd → warn, else User(email, username="admin", hash_password, is_active True, is_verified True, role_id) → commit
```

Needed for RBAC tests (`tests/utils.py:create_test_admin` also).

---

## 12. Tests (`tests/`)

### `conftest.py:1`

```py
# fakeredis fallback
try: import fakeredis; from app.cache import client
  if USE_FAKE_REDIS==1 → redis_client = FakeRedis
  else: try ping() except → FakeRedis
from app.main import app
client = TestClient(app)
```

Single `client` reused across tests (integration, hits real DB if available, fake Redis if not).

### `utils.py:1`

`create_test_admin():14` — `select User where email==TEST_ADMIN_EMAIL` → if exists return else `select Role Admin` → `User(admin hash, is_verified True)` → commit.

### `test_*.py` — 13 Integration Tests

| File | Test | Endpoint | Asserts |
|------|------|----------|---------|
| `test_register.py:6` | `test_register_user` | `POST /api/v1/auth/register` random `test_{uuid}@example.com` | `201`, `email endswith`, `id`, `is_active True` |
| `test_login.py:6` | `test_login_user` | register → `POST /api/v1/auth/login` `username=email` | `200`, `access_token`, `refresh_token` |
| `test_refresh.py:6` | `test_refresh_token` | register → login → `POST /api/v1/auth/refresh {refresh_token}` | `200`, rotation `new != old` |
| `test_logout.py:6` | `test_logout` | register → login → `POST /api/v1/auth/logout` `Bearer access + {refresh_token}` | `200` |
| `test_blacklist.py:6` | `test_blacklisted_token_cannot_access_me` | register → login → logout → `GET /api/v1/auth/me` with old access | `401` (blacklist) |
| `test_rbac.py:12,52` | `test_user_cannot_access_users_endpoint` / `test_admin_can_access_users` | register normal → `/api/v1/users/` → `403`; seed admin → login → `/api/v1/users/` → `200` | RBAC |
| `test_rate_limit.py:6` | `test_login_rate_limit` | register → 5× wrong pwd → 6th → `429` | `allow_request(limit=5, window=60)` |
| `test_cache.py:6` | `test_cache_service` | `CacheService().set_json("test:{uuid}", {"hello":"world"})` → `get_json` → `delete` | JSON round-trip |
| `test_redis.py:1` | `test_redis_connection` | `set("health","ok",ttl10)` → `get==ok`, `exists`, `delete` | Redis |
| `test_password_reset.py:6,36` | `test_forgot_password` / `unknown_email` | register → `POST /forgot-password {email}` → `200`; unknown `unknown@example.com` → `200` (no enumeration) | |
| `test_change_password.py:6` | `test_change_password` | register → login → `POST /change-password {current, new}` `Bearer` | `200` |

Run: `pytest -v`, `USE_FAKE_REDIS=1 pytest --cov=app`.

---

## 13. Infra & Config

### `docker-compose.yml:1`

```yaml
services:
  db: postgres:17, container authforge-db, POSTGRES_DB/USER/PASSWORD, 5433:5432, volume postgres_data, healthcheck pg_isready
  redis: redis:7-alpine, authforge-redis, 6379:6379, volume redis_data, healthcheck redis-cli ping
  api: build ., authforge-api, 8000:8000, depends_on db+redis condition: service_healthy, env_file .env
volumes: postgres_data, redis_data
```

Fix: added `redis` service, healthchecks, `depends_on` healthy.

### `Dockerfile:1` — Multi-stage Hardened

```dockerfile
FROM python:3.11-slim AS builder
  apt build-essential libpq-dev, COPY requirements.txt, pip install --prefix=/install -r requirements.txt
FROM python:3.11-slim AS runtime
  apt libpq5 curl, useradd appuser 10001, COPY --from=builder /install, COPY ., chown appuser, USER appuser, EXPOSE 8000, HEALTHCHECK curl /health, CMD uvicorn app.main:app --proxy-headers
```

### `.dockerignore:1` — Excludes `.venv, .git, __pycache__, .env, tests, htmlcov` etc.

### `requirements.txt:1` — `alembic, fastapi, sqlalchemy, psycopg2-binary, redis, pydantic, passlib, bcrypt, python-jose, fakeredis, pytest, ruff` (add `python-multipart`, `email-validator`, `httpx` etc).

### `pyproject.toml:1` — Single Source of Truth

- `project` `name:authforge, version 1.0.0, requires-python >=3.11`
- `tool.ruff` `line-length 100, target py311, select E/F/W/I/B/C4/UP/S, ignore S101/B008/B904, per-file-ignores tests/S105`
- `tool.black` `line 100`
- `tool.pytest.ini_options` `testpaths tests, addopts -v --tb=short`
- `tool.coverage` `source app, fail_under 70`

### `Makefile:1` — `install, lint (ruff), format (ruff --fix+black), test (--cov), test-quick, run (uvicorn --reload), migrate, migrate-new, seed, docker-up/down/logs, clean`

### `.pre-commit-config.yaml:1` — `ruff, ruff-format, black (line 100), trailing-whitespace, end-of-file, check-yaml, large-files`

### `.editorconfig:1` — `utf-8, lf, indent 4 (2 for yml), trim, tab for Makefile`

### `CONTRIBUTING.md:1` — Setup, workflow (branch, lint, pytest), code style, security (no .env), testing with fakeredis.

### `.env.example:1` — 16 vars: `APP_NAME/VERSION/ENVIRONMENT/DEBUG/LOG_LEVEL/API_HOST/PORT/FRONTEND_URL/REQUIRE_EMAIL_VERIFICATION, DATABASE_URL or DB_HOST/PORT/NAME/USER/PASSWORD, JWT_SECRET_KEY/ALGORITHM/ACCESS_TOKEN_EXPIRE_MINUTES/REFRESH_TOKEN_EXPIRE_DAYS, REDIS_HOST/PORT/DB/PASSWORD, CORS_ORIGINS, TEST_ADMIN_EMAIL/PASSWORD`.

### `.env:1` (gitignored, sanitized) — local dev `DATABASE_URL=postgresql://postgres:postgres@localhost:5433/authforge`, `JWT_SECRET_KEY=change-me... (>=32)`, `FRONTEND_URL`, etc. (was Neon leaked URL — rotated).

### `.github/workflows/ci.yml:1` — `on push/PR main/develop/feature/**` → `runs-on ubuntu-latest` with `services postgres:17, redis:7` healthchecks → `checkout, setup-python 3.11, pip install r.txt + black/ruff, ruff check, black --check, alembic upgrade head, seed_roles, pytest -v --tb=short` with env `DATABASE_URL postgres://.../authforge_test, JWT_SECRET_KEY test-secret..., REDIS_HOST localhost`.

---

## 14. Request Lifecycle (End-to-End)

**Register → Verify → Login → Access → Refresh → Logout:**

1. `POST /api/v1/auth/register {email, username, password}` `app/modules/auth/routes.py:34`
   - `UserCreate` validation `EmailStr, username 3-30, password 8-128`
   - `AuthService.register_user` checks `get_by_email/username` → `hash_password` → `User(role=User)` → `Refresh? No` → `EmailVerificationToken` → `email_provider.send_verification_email(frontend_url + ?token)` → `201 UserResponse`.

2. `GET /api/v1/auth/verify-email?token=xxx` → `verify_email` → marks `is_verified True`.

3. `POST /api/v1/auth/login` `OAuth2PasswordRequestForm(username=email|username, password)` + `login_rate_limit` (`login:{username}` 5/60s)
   - `AuthService.login_user` → `get_by_email/username` → `is_active` → `verify_password` → `require_email_verification?` → `_issue_tokens` → `{access_token, refresh_token}` + `audit.log LOGIN` + `RefreshToken` row.

4. `GET /api/v1/auth/me` `Authorization: Bearer <access>`
   - `shared/dependencies.py:get_current_user` → `decode_token` → `type access` → `jti not blacklisted` → `user_id` → `User` → return `UserResponse`.

5. `POST /api/v1/auth/refresh {refresh_token}`
   - `decode → type refresh` → `RefreshTokenRepository.get_by_token` → `not revoked` → `revoke(old)` → `_issue_tokens(user)` → new pair (old revoked).

6. `POST /api/v1/auth/logout {refresh_token}` `Authorization: Bearer <access>`
   - `revoke(refresh)` → `decode(access) → jti/exp → blacklist_token(jti, exp-now)` → `audit.log LOGOUT`. Next `GET /me` with old access → `401 Token revoked` (`is_blacklisted`).

7. `POST /api/v1/auth/forgot-password {email}` → generic `200` → `PasswordResetToken(now+1h)` → email.

8. `POST /api/v1/auth/reset-password {token, new_password}` → `mark_used`, `hash new`, `audit.log`.

9. `GET /api/v1/users/?page=1&page_size=20` `Bearer Admin` → `require_role("Admin")` → `UserRepository.get_paginated` → `PaginatedResponse[UserResponse]` with `items, total, page, pages`. Legacy `/users/` rewritten.

---

## 15. Security Matrix

| Threat | Mitigation | File:Line |
|--------|------------|-----------|
| Password leak | `bcrypt` + `passlib` | `core/security.py:4` |
| JWT reuse | `jti` per token + Redis blacklist `TTL=exp-now` | `core/jwt.py:28`, `auth/service.py:290`, `cache/service.py:66` |
| Token type confusion | `type` check `access` vs `refresh` | `shared/dependencies.py:31`, `auth/service.py:226` |
| Brute force | Atomic `INCR` rate limit 5/60s per `login:{id}` | `core/rate_limit.py:14`, `auth/dependencies.py:47` |
| Enumeration | Generic `If email exists...` | `auth/service.py:314` |
| RBAC bypass | `require_role` + `role.name` check + `get_current_user` blacklist | `core/dependencies.py:7`, `shared/dependencies.py:44` |
| Inactive user | `get_current_user` `if not is_active → 403` + login `is_active` check | `shared/dependencies.py:62`, `auth/service.py:185` |
| Secret weak | `field_validator len>=32` rejects placeholder | `core/config.py:58` |
| CORS abuse | `CORS_ORIGINS` csv / prod `frontend_url` | `core/config.py:66`, `main.py:31` |
| XSS/clickjack | `SecurityHeadersMiddleware` HSTS/nosniff/DENY | `core/middleware.py:20` |
| Leakage | No `.env` in git, `.dockerignore`, `CONTRIBUTING` | `.gitignore:11`, `.dockerignore:9` |
| IDOR | `user_id` from `sub` JWT, not client param for `me` | `shared/dependencies.py:54` |

---

## 16. How to Extend

**Add new module `posts`:**

```bash
mkdir -p app/modules/posts
touch app/modules/posts/{models.py,schemas.py,repository.py,service.py,routes.py,dependencies.py}
# app/modules/posts/models.py: class Post(Base, TimestampMixin): __tablename__="posts", user_id FK...
# app/modules/posts/schemas.py: class PostCreate(BaseModel): title, content
# app/modules/posts/repository.py: class PostRepository(db): create, get_paginated
# app/modules/posts/service.py: class PostService(repo): create_post, list_posts
# app/modules/posts/routes.py: router = APIRouter(prefix="/api/v1/posts", tags=["Posts"])
#   @router.post("/", response_model=PostResponse) def create(post: PostCreate, current_user=Depends(get_current_user), db=Depends(get_db)): ...
# app/db/models.py: from app.modules.posts.models import Post; add to __all__
# alembic revision --autogenerate -m "add posts table" && alembic upgrade head
# app/main.py: from app.modules.posts.routes import router as posts_router; app.include_router(posts_router)
# tests/test_posts.py: use client from tests/conftest.py
```

**Switch email provider:**

```py
# app/providers/factory.py:4
if settings.email_provider == "resend": return ResendEmailProvider()
# Implement class ResendEmailProvider(EmailProvider): send_verification_email -> resend.Emails.send(...)
```

**Add soft delete, search, sorting:** Add `deleted_at`, `where(func.lower(col).like(...))`, `order_by`.

---

## 17. Cheat Sheet

```bash
# Setup
cp .env.example .env && nano .env  # JWT_SECRET_KEY >=32
python -m venv .venv && .venv\Scripts\activate  # Windows
pip install -r requirements.txt && pip install -e ".[dev]"
pre-commit install

# DB
alembic upgrade head && python scripts/seed_roles.py && python scripts/seed_admin.py
# Docker
docker compose up --build -d && docker compose exec api alembic upgrade head

# Dev
make run          # uvicorn --reload
make lint         # ruff check .
make format       # ruff --fix + black
make test         # pytest --cov
USE_FAKE_REDIS=1 pytest -q

# API
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/v1/auth/register -H "Content-Type: application/json" -d '{"email":"a@b.com","username":"ab","password":"Password@123"}'
curl -X POST http://localhost:8000/api/v1/auth/login -d "username=a@b.com&password=Password@123"
curl http://localhost:8000/api/v1/auth/me -H "Authorization: Bearer <access>"
curl http://localhost:8000/api/v1/users/?page=1&page_size=5 -H "Authorization: Bearer <admin_access>"
```

---

**Maintained for SDE portfolio — PRs welcome. See `README.md` (overview), `CONTRIBUTING.md` (workflow), `pyproject.toml` (quality gates).**

