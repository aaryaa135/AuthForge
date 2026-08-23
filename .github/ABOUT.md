# GitHub — About Section Setup

Copy-paste this into **GitHub → Settings → General → About** (top-right gear icon).

## Description (Website field: leave blank or https://github.com/aaryaa135/AuthForge)

```
Production-ready Auth Platform — FastAPI + PostgreSQL + Redis + Docker + JWT rotation + RBAC + audit logging
```

Short alt (if 350 char limit):
```
FastAPI auth service: JWT access/refresh rotation, RBAC, Redis blacklist, rate limiting, email verification, audit logs — Docker + CI
```

## Topics (Settings → Topics → Add topics)

```
fastapi
postgresql
redis
docker
jwt
authentication
authorization
rbac
sqlalchemy
alembic
pytest
python
backend
rest-api
```

## Website

- Local docs: `http://localhost:8000/docs` (or deploy URL after hosting)
- Or set to: `https://github.com/aaryaa135/AuthForge#readme`

## Social Preview

- Use `assets/swagger.png` (Swagger UI screenshot) as social preview: **Settings → General → Social preview → Upload**.
- Or generate: `npx og-image` with title "AuthForge — FastAPI Auth Platform".

## Badges (already in README.md:1)

```
![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.139-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-blue)
![Redis](https://img.shields.io/badge/Redis-7-red)
![Docker](https://img.shields.io/badge/Docker-Multi--Stage-blue)
![Pytest](https://img.shields.io/badge/Pytest-13%2B-success)
![CI](https://github.com/aaryaa135/AuthForge/actions/workflows/ci.yml/badge.svg)
```

## Verify

After saving: `gh repo view aaryaa135/AuthForge --json description,repositoryTopics,homepageUrl` or check repo header.
