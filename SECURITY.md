# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.x     | ✅        |

## Reporting a Vulnerability

Do **not** open a public issue. Email `security@authforge.local` or DM `@aaryaa135` with:

- Description, impact, reproduce steps (`curl`), commit hash
- We respond within 72h, fix within 14 days, credit you in release notes if desired

## Hardening Checklist (already in repo)

- `JWT_SECRET_KEY >=32 chars` validator (`app/core/config.py:58`)
- `bcrypt` + `jti` blacklist (`app/core/jwt.py:28`, `app/cache/service.py:66`)
- Atomic rate limit (`app/core/rate_limit.py:14`)
- `is_active` gate + optional `REQUIRE_EMAIL_VERIFICATION`
- Security headers (`app/core/middleware.py:20`)
- No `.env` in git (`.gitignore:11`, `.dockerignore:9`)

Rotate secrets if leaked: `openssl rand -hex 32`
