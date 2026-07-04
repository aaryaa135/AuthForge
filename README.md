# 🔐 AuthForge

A production-grade Authentication and Authorization microservice built with FastAPI, following Clean Architecture and modern backend engineering practices.

> This project is being built feature-by-feature with a focus on scalability, security, maintainability, and production readiness.

---

## 🚀 Tech Stack

- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- JWT Authentication
- bcrypt
- Docker & Docker Compose
- Pytest

---

## 🏗 Architecture

This project follows **Clean Architecture** with clear separation of responsibilities.

```
Presentation Layer
        │
Service Layer
        │
Repository Layer
        │
Database Layer
```

Core design principles:

- Repository Pattern
- Service Layer
- Dependency Injection
- Environment-based Configuration
- Structured Logging
- Centralized Exception Handling
- Unit Testing

---

## ✨ Planned Features

### Authentication

- User Registration
- Login
- Logout
- Refresh Tokens
- JWT Authentication

### User Management

- Search Users
- Pagination
- Profile Management

### Security

- Email Verification
- Forgot Password
- Password Reset
- Role-Based Access Control (RBAC)
- Password Hashing (bcrypt)

### Infrastructure

- Docker Support
- Alembic Migrations
- Swagger Documentation
- Environment Variables
- Production Logging

---

## 📂 Project Structure

```
app/
├── api/
├── core/
├── db/
├── repositories/
├── services/
├── schemas/
├── middleware/
└── utils/

tests/
alembic/
docker/
```

---

## 📌 Project Status

🚧 Currently under active development.

The project is being built incrementally with production-grade engineering practices, meaningful commit history, and comprehensive documentation.

---

## 📜 License

This project is intended for learning, portfolio, and demonstration purposes.