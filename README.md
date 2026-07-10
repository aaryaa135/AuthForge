# 🔐 AuthForge

> **Production-ready Authentication & Authorization Platform built with FastAPI, PostgreSQL, Redis & Docker.**

![Python](https://img.shields.io/badge/Python-3.13-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.116-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue)
![Redis](https://img.shields.io/badge/Redis-Cache-red)
![Docker](https://img.shields.io/badge/Docker-Containerized-blue)
![Pytest](https://img.shields.io/badge/Pytest-13%2B%20Tests-success)
![CI](https://github.com/YOUR_USERNAME/AuthForge/actions/workflows/quality-checks.yml/badge.svg)

---

## 📖 Overview

AuthForge is a modular authentication and authorization platform designed with production-ready architecture and security best practices.

It provides secure user authentication, role-based authorization, JWT access & refresh tokens, Redis-powered token blacklisting, rate limiting, email verification, password reset, audit logging, automated testing, and CI/CD integration.

The project follows a clean modular architecture making it reusable across multiple applications.

---

# ✨ Features

### Authentication

- User Registration
- Secure Login
- JWT Access Tokens
- Refresh Token Rotation
- Logout
- Session Management

### Authorization

- Role-Based Access Control (RBAC)
- Admin/User Roles
- Protected Routes

### Security

- Password Hashing (bcrypt)
- Email Verification
- Password Reset
- Redis Token Blacklisting
- Login Rate Limiting
- Secure JWT Validation

### Performance

- Redis User Caching
- Optimized Database Queries

### Monitoring

- Audit Logging
- Request Tracking
- Security Event Logging

### DevOps

- Docker Support
- GitHub Actions CI
- Automated Testing
- Ruff
- Black

---

# 🏗 Architecture

```
                Client
                   │
                   ▼
             FastAPI Server
                   │
        ┌──────────┴──────────┐
        │                     │
 Authentication           Authorization
        │                     │
        └──────────┬──────────┘
                   │
              Auth Service
                   │
      ┌────────────┼─────────────┐
      │            │             │
 PostgreSQL      Redis      Email Provider
      │            │
      ▼            ▼
 Persistent     Cache &
 Storage      Blacklisting
```

---

# 🛠 Tech Stack

## Backend

- FastAPI
- SQLAlchemy
- PostgreSQL
- Redis
- Pydantic v2

## Authentication

- JWT
- OAuth2 Password Flow
- RBAC
- Refresh Token Rotation

## Security

- bcrypt
- Email Verification
- Password Reset
- Rate Limiting

## DevOps

- Docker
- GitHub Actions
- Pytest
- Ruff
- Black

---

# 📂 Project Structure

```
app/
│
├── cache/
├── core/
├── db/
├── modules/
│   ├── auth/
│   ├── users/
│   ├── roles/
│   ├── audit/
│   └── ...
│
├── providers/
├── shared/
│
tests/
alembic/
```

---

# 🔑 Authentication Flow

```
Register
    │
    ▼
Email Verification
    │
    ▼
Login
    │
    ▼
Access Token
Refresh Token
    │
    ▼
Protected APIs
    │
    ▼
Refresh Token Rotation
    │
    ▼
Logout
    │
    ▼
JWT Blacklisted
```

---

# 🚀 Getting Started

## Clone

```bash
git clone https://github.com/YOUR_USERNAME/AuthForge.git

cd AuthForge
```

---

## Virtual Environment

```bash
python -m venv .venv
```

Windows

```bash
.venv\Scripts\activate
```

Linux

```bash
source .venv/bin/activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Configure Environment

Create

```
.env
```

```
DATABASE_URL=
JWT_SECRET_KEY=
JWT_ALGORITHM=
REDIS_URL=
SMTP_USERNAME=
SMTP_PASSWORD=
```

---

## Run Migrations

```bash
alembic upgrade head
```

---

## Run Server

```bash
uvicorn app.main:app --reload
```

Swagger

```
http://localhost:8000/docs
```

---

# 🐳 Docker

Start Redis

```bash
docker run -d \
-p 6379:6379 \
--name authforge-redis \
redis:7
```

Verify

```bash
docker exec -it authforge-redis redis-cli
```

```
PING

PONG
```

---

# 🧪 Running Tests

```bash
pytest
```

Current Status

```
13+ Tests Passing
```

---

# 📬 API Endpoints

## Authentication

| Method | Endpoint |
|----------|----------------------------|
| POST | /api/v1/auth/register |
| POST | /api/v1/auth/login |
| POST | /api/v1/auth/logout |
| POST | /api/v1/auth/refresh |
| GET | /api/v1/auth/me |
| POST | /api/v1/auth/change-password |
| POST | /api/v1/auth/forgot-password |
| POST | /api/v1/auth/reset-password |
| GET | /api/v1/auth/verify-email |

---

# 🔒 Security Features

✅ Password Hashing

✅ JWT Authentication

✅ Refresh Token Rotation

✅ Redis Token Blacklisting

✅ Login Rate Limiting

✅ RBAC

✅ Email Verification

✅ Password Reset

✅ Audit Logging

---

# 📈 CI/CD

Every push automatically runs:

- Ruff
- Black
- Pytest

via GitHub Actions.

---

# 🗺 Roadmap

- [x] Authentication
- [x] RBAC
- [x] Email Verification
- [x] Password Reset
- [x] Refresh Tokens
- [x] JWT Blacklisting
- [x] Redis Cache
- [x] Rate Limiting
- [x] Audit Logging
- [ ] Session Management
- [ ] Admin Dashboard APIs
- [ ] Frontend Dashboard
- [ ] Deployment

---

# 🤝 Contributing

Contributions are welcome.

Please open an issue before submitting large changes.

---

# 📄 License

MIT License
