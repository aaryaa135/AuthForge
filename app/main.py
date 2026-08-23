from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logger import logger
from app.core.middleware import RequestIDMiddleware, SecurityHeadersMiddleware
from app.modules.audit.routes import router as audit_router
from app.modules.auth.routes import router as auth_router
from app.modules.users.routes import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.app_name}...")

    yield

    logger.info(f"Stopping {settings.app_name}...")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
    contact={"name": "AuthForge", "url": "https://github.com/YOUR_USERNAME/AuthForge"},
    license_info={"name": "MIT"},
    openapi_tags=[
        {"name": "Root", "description": "Service metadata"},
        {"name": "Health", "description": "Health checks"},
        {"name": "Authentication", "description": "Register, login, tokens, password flows"},
        {"name": "Users", "description": "Admin user management"},
        {"name": "Audit", "description": "Security audit logs"},
    ],
)

# Order matters: outer -> inner (CORS outermost)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def legacy_path_rewrite(request: Request, call_next):
    # Backward compat: rewrite /users/* and /audit/* to versioned prefix
    path = request.scope.get("path", "")
    if path == "/users" or path.startswith("/users/"):
        request.scope["path"] = "/api/v1" + path
    elif path == "/audit" or path.startswith("/audit/"):
        request.scope["path"] = "/api/v1" + path
    return await call_next(request)


register_exception_handlers(app)


@app.get("/", tags=["Root"])
async def root():
    return {"message": f"Welcome to {settings.app_name}"}


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "application": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }


app.include_router(auth_router)
app.include_router(users_router)
app.include_router(audit_router)
